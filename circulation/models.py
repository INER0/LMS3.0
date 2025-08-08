"""
Circulation models for Library Management System
Implements borrowing, reservations, and loan management
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError


class BookLoan(models.Model):
    """Book borrowing transactions"""
    STATUS_CHOICES = [
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
        ('overdue', 'Overdue'),
    ]
    
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE)
    book_copy = models.ForeignKey('library.BookCopy', on_delete=models.CASCADE)
    borrow_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='borrowed')
    
    class Meta:
        db_table = 'book_loans'
        ordering = ['-borrow_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.book_copy.book.title}"
    
    def save(self, *args, **kwargs):
        if not self.due_date and self.user.membership_fee:
            # Calculate due date based on membership
            loan_days = self.user.membership_fee.loan_period
            self.due_date = self.borrow_date + timedelta(days=loan_days)
        super().save(*args, **kwargs)
    
    def is_overdue(self):
        """Check if loan is overdue"""
        if self.status == 'returned':
            return False
        return timezone.now().date() > self.due_date
    
    def days_overdue(self):
        """Calculate days overdue"""
        if not self.is_overdue():
            return 0
        return (timezone.now().date() - self.due_date).days
    
    def can_extend(self):
        """Check if loan can be extended"""
        if self.status != 'borrowed':
            return False
        # Check if already extended
        if self.loanextension_set.exists():
            return False
        # Check if book is reserved by others
        pending_reservations = self.book_copy.book.reservation_set.filter(
            status='active'
        ).exclude(user=self.user)
        return not pending_reservations.exists()


class LoanExtension(models.Model):
    """Loan extensions"""
    book_loan = models.ForeignKey(BookLoan, on_delete=models.CASCADE)
    extended_by_days = models.IntegerField()
    extension_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'loan_extensions'
    
    def __str__(self):
        return f"Extension: {self.book_loan} by {self.extended_by_days} days"


class Reservation(models.Model):
    """Book reservations"""
    RESERVATION_TYPES = [
        ('regular', 'Regular'),
        ('priority', 'Priority'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('fulfilled', 'Fulfilled'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE)
    book = models.ForeignKey('library.Book', on_delete=models.CASCADE)
    reservation_type = models.CharField(max_length=20, choices=RESERVATION_TYPES, default='regular')
    reservation_date = models.DateField(default=timezone.now)
    queue_position = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    expires_at = models.DateTimeField(null=True, blank=True)
    notified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'reservations'
        ordering = ['queue_position', 'reservation_date']
        unique_together = ['user', 'book', 'status']  # Prevent duplicate active reservations
    
    def __str__(self):
        return f"{self.user.username} - {self.book.title} (Position: {self.queue_position})"
    
    def save(self, *args, **kwargs):
        if not self.pk:  # New reservation
            # Set queue position
            last_position = Reservation.objects.filter(
                book=self.book, status='active'
            ).aggregate(models.Max('queue_position'))['queue_position__max'] or 0
            self.queue_position = last_position + 1
            
            # Priority reservations go to the front
            if self.reservation_type == 'priority':
                self.queue_position = 1
                # Update other reservations
                Reservation.objects.filter(
                    book=self.book, status='active'
                ).update(queue_position=models.F('queue_position') + 1)
        
        super().save(*args, **kwargs)
    
    def is_ready(self):
        """Check if reservation is ready for pickup"""
        return (self.queue_position == 1 and 
                self.book.get_available_copies_count() > 0)
    
    def notify_ready(self):
        """Mark reservation as ready and notify user"""
        if self.is_ready() and not self.notified_at:
            from library.models import UserNotification
            UserNotification.objects.create(
                user=self.user,
                type='reservation_ready',
                message=f'Your reserved book "{self.book.title}" is ready for pickup.'
            )
            self.notified_at = timezone.now()
            # Set expiration (3 days to pick up)
            self.expires_at = timezone.now() + timedelta(days=3)
            self.save()


class FineRule(models.Model):
    """Rules for calculating fines"""
    FINE_TYPES = [
        ('overdue', 'Overdue'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    ]
    
    fine_type = models.CharField(max_length=20, choices=FINE_TYPES)
    delay_from = models.IntegerField(help_text="Days from (inclusive)")
    delay_to = models.IntegerField(help_text="Days to (inclusive)")
    rate_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'fine_rules'
        ordering = ['fine_type', 'delay_from']
    
    def __str__(self):
        return f"{self.get_fine_type_display()}: {self.delay_from}-{self.delay_to} days @ {self.rate_per_day}/day"
    
    @classmethod
    def calculate_overdue_fine(cls, days_overdue):
        """Calculate fine for overdue books"""
        if days_overdue <= 0:
            return 0
        
        # Get applicable fine rule
        rule = cls.objects.filter(
            fine_type='overdue',
            delay_from__lte=days_overdue,
            delay_to__gte=days_overdue
        ).first()
        
        if not rule:
            # Default to highest tier if no specific rule found
            rule = cls.objects.filter(fine_type='overdue').order_by('-delay_from').first()
        
        if rule:
            return days_overdue * rule.rate_per_day + rule.processing_fee
        
        # Fallback default rates
        if days_overdue <= 3:
            return days_overdue * 2  # 2 MVR per day
        elif days_overdue <= 7:
            return days_overdue * 5  # 5 MVR per day
        else:
            return days_overdue * 10  # 10 MVR per day


class Fine(models.Model):
    """User fines"""
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE)
    book_loan = models.ForeignKey(BookLoan, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    fine_date = models.DateTimeField(auto_now_add=True)
    paid_date = models.DateTimeField(null=True, blank=True)
    fine_type = models.CharField(max_length=50, default='overdue')
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'fines'
        ordering = ['-fine_date']
    
    def __str__(self):
        status = "Paid" if self.paid else "Unpaid"
        return f"{status} fine: {self.user.username} - MVR {self.amount}"
    
    def mark_paid(self):
        """Mark fine as paid"""
        self.paid = True
        self.paid_date = timezone.now()
        self.save()


class LateRenewal(models.Model):
    """Late membership renewals"""
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE)
    days_late = models.IntegerField()
    late_fee = models.DecimalField(max_digits=10, decimal_places=2)
    processed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'late_renewals'
        ordering = ['-processed_at']
    
    def __str__(self):
        return f"Late renewal: {self.user.username} - {self.days_late} days - MVR {self.late_fee}"
    
    @classmethod
    def calculate_late_fee(cls, days_late):
        """Calculate late renewal fee"""
        if days_late <= 0:
            return 0
        elif days_late <= 7:
            return 10  # MVR 10 for 1-7 days late
        elif days_late <= 30:
            return 50  # MVR 50 for 8-30 days late
        else:
            # More than 30 days requires full re-registration
            return None


class DigitalService(models.Model):
    """Digital services usage"""
    SERVICE_TYPES = [
        ('ebook', 'E-Book Access'),
        ('research_access', 'Research Access'),
        ('printing', 'Printing/Photocopy'),
    ]
    
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE)
    service_type = models.CharField(max_length=30, choices=SERVICE_TYPES)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_fee = models.DecimalField(max_digits=10, decimal_places=2)
    access_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'digital_services'
        ordering = ['-access_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_service_type_display()}"
    
    def save(self, *args, **kwargs):
        if not self.total_fee:
            self.total_fee = self.quantity * self.unit_price
        super().save(*args, **kwargs)
