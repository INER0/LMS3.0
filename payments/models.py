"""
Payment models for Library Management System
Implements payment processing for memberships, fines, and services
"""

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
import uuid


class Payment(models.Model):
    """Payment transactions"""
    PURPOSE_CHOICES = [
        ('membership', 'Membership'),
        ('fine', 'Fine'),
        ('reservation', 'Reservation'),
        ('digital', 'Digital Service'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('online', 'Online Banking'),
        ('mobile', 'Mobile Payment'),
    ]
    
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    related_id = models.IntegerField(null=True, blank=True, 
                                   help_text="ID of related record (polymorphic)")
    amount = models.DecimalField(max_digits=10, decimal_places=2, 
                               validators=[MinValueValidator(0.01)])
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, 
                            default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, 
                                    default='cash')
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True)
    payment_date = models.DateTimeField(default=timezone.now)
    processed_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name='processed_payments')
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_purpose_display()} - MVR {self.amount}"
    
    def mark_completed(self, processed_by_user=None):
        """Mark payment as completed"""
        self.status = 'completed'
        self.processed_by = processed_by_user
        self.payment_date = timezone.now()
        self.save()
        
        # Update related records
        if self.purpose == 'fine' and self.related_id:
            try:
                from circulation.models import Fine
                fine = Fine.objects.get(id=self.related_id)
                fine.mark_paid()
            except Fine.DoesNotExist:
                pass
        elif self.purpose == 'reservation' and self.related_id:
            try:
                from circulation.models import Reservation
                # Create reservation payment record if needed
                pass
            except:
                pass
    
    def mark_failed(self, reason=""):
        """Mark payment as failed"""
        self.status = 'failed'
        if reason:
            self.notes = reason
        self.save()


class PaymentHistory(models.Model):
    """Historical record of all payments"""
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    status_change = models.CharField(max_length=50)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, 
                                 null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'payment_history'
        ordering = ['-changed_at']
        verbose_name_plural = 'Payment History'
    
    def __str__(self):
        return f"Payment {self.payment.transaction_id} - {self.status_change}"


class MembershipPayment(models.Model):
    """Specific payment records for memberships"""
    MEMBERSHIP_PERIOD_CHOICES = [
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
    ]
    
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)
    membership_type = models.CharField(max_length=20)
    period = models.CharField(max_length=20, choices=MEMBERSHIP_PERIOD_CHOICES)
    valid_from = models.DateField()
    valid_until = models.DateField()
    auto_renew = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'membership_payments'
        ordering = ['-valid_from']
    
    def __str__(self):
        return f"{self.user.username} - {self.membership_type} ({self.period})"


class FinePayment(models.Model):
    """Specific payment records for fines"""
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)
    fine = models.ForeignKey('circulation.Fine', on_delete=models.CASCADE)
    partial_payment = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'fine_payments'
        ordering = ['-payment__payment_date']
    
    def __str__(self):
        return f"Fine payment: {self.user.username} - MVR {self.payment.amount}"


class DigitalServicePayment(models.Model):
    """Specific payment records for digital services"""
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)
    service = models.ForeignKey('circulation.DigitalService', on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'digital_service_payments'
        ordering = ['-payment__payment_date']
    
    def __str__(self):
        return f"Service payment: {self.user.username} - {self.service.get_service_type_display()}"


class PaymentReport(models.Model):
    """Payment reports and analytics"""
    REPORT_TYPES = [
        ('daily', 'Daily Revenue'),
        ('monthly', 'Monthly Revenue'),
        ('yearly', 'Yearly Revenue'),
        ('fines_collected', 'Fines Collected'),
        ('membership_revenue', 'Membership Revenue'),
        ('service_revenue', 'Digital Services Revenue'),
    ]
    
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    report_date = models.DateField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_count = models.IntegerField()
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, 
                                   null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'payment_reports'
        ordering = ['-report_date']
        unique_together = ['report_type', 'report_date']
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.report_date}"


# Revenue tracking views (implemented as models for Django ORM)
class MonthlyRevenue(models.Model):
    """Monthly revenue summary"""
    month = models.DateField()
    membership_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fine_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    service_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reservation_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'monthly_revenue'
        ordering = ['-month']
        managed = False  # This will be implemented as a database view
    
    def __str__(self):
        return f"Revenue for {self.month.strftime('%B %Y')}: MVR {self.total_revenue}"


class DailyRevenue(models.Model):
    """Daily revenue summary"""
    date = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_count = models.IntegerField()
    
    class Meta:
        db_table = 'daily_revenue'
        ordering = ['-date']
        managed = False  # This will be implemented as a database view
    
    def __str__(self):
        return f"Revenue for {self.date}: MVR {self.total_amount}"


class PaymentAnalytics(models.Model):
    """Payment analytics and insights"""
    metric_name = models.CharField(max_length=100)
    metric_value = models.DecimalField(max_digits=12, decimal_places=2)
    calculation_date = models.DateField(auto_now_add=True)
    period = models.CharField(max_length=50)  # e.g., "2025-01", "Q1-2025"
    
    class Meta:
        db_table = 'payment_analytics'
        ordering = ['-calculation_date']
    
    def __str__(self):
        return f"{self.metric_name} ({self.period}): {self.metric_value}"
