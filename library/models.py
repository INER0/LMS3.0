"""
Library models for Library Management System
Implements book catalog, inventory, and branch management
"""

from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class Branch(models.Model):
    """Library branches/locations"""
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'branches'
        verbose_name_plural = 'Branches'
    
    def __str__(self):
        return f"{self.name} - {self.location}"


class BranchManager(models.Model):
    """One manager per branch"""
    branch = models.OneToOneField(Branch, on_delete=models.CASCADE, primary_key=True)
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'branch_managers'
    
    def __str__(self):
        return f"Manager: {self.user.username} at {self.branch.name}"


class Section(models.Model):
    """Sections within library branches"""
    name = models.CharField(max_length=255)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'sections'
    
    def __str__(self):
        return f"{self.name} ({self.branch.name})"


class Publisher(models.Model):
    """Book publishers"""
    name = models.CharField(max_length=255, unique=True)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'publishers'
    
    def __str__(self):
        return self.name


class Author(models.Model):
    """Book authors"""
    name = models.CharField(max_length=255)
    
    class Meta:
        db_table = 'authors'
    
    def __str__(self):
        return self.name


class Book(models.Model):
    """Book catalog entries"""
    isbn_validator = RegexValidator(
        regex=r'^\d{10}$|^\d{13}$',
        message='ISBN must be 10 or 13 digits'
    )
    
    LANGUAGE_CHOICES = [
        ('dhivehi', 'Dhivehi'),
        ('english', 'English'),
        ('arabic', 'Arabic'),
        ('other', 'Other'),
    ]
    
    CATEGORY_CHOICES = [
        ('fiction', 'Fiction'),
        ('non-fiction', 'Non-Fiction'),
        ('research', 'Research'),
        ('children', 'Children\'s Books'),
        ('academic', 'Academic'),
        ('reference', 'Reference'),
    ]
    
    isbn = models.CharField(max_length=13, validators=[isbn_validator], unique=True)
    title = models.CharField(max_length=500)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    edition = models.CharField(max_length=100)
    publication_year = models.IntegerField()
    language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES)
    publisher = models.ForeignKey(Publisher, on_delete=models.PROTECT)
    section = models.ForeignKey(Section, on_delete=models.PROTECT)
    authors = models.ManyToManyField(Author, through='BookAuthor')
    
    class Meta:
        db_table = 'books'
    
    def __str__(self):
        return f"{self.title} ({self.isbn})"
    
    def get_available_copies_count(self):
        """Count available copies for borrowing"""
        return self.bookcopy_set.filter(
            condition='good'
        ).exclude(
            bookloan__status='borrowed'
        ).count()
    
    def get_total_copies_count(self):
        """Count total copies"""
        return self.bookcopy_set.count()


class BookAuthor(models.Model):
    """Many-to-many relationship between books and authors"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'book_authors'
        unique_together = ['book', 'author']
    
    def __str__(self):
        return f"{self.book.title} by {self.author.name}"


class BookCopy(models.Model):
    """Physical copies of books"""
    CONDITION_CHOICES = [
        ('good', 'Good'),
        ('damaged', 'Damaged'),
        ('lost', 'Lost'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    barcode = models.CharField(max_length=255, unique=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    last_seen = models.DateField(default=timezone.now)
    
    class Meta:
        db_table = 'book_copies'
        verbose_name_plural = 'Book Copies'
    
    def __str__(self):
        return f"{self.book.title} - {self.barcode}"
    
    def is_available(self):
        """Check if copy is available for borrowing"""
        if self.condition != 'good':
            return False
        current_loan = self.bookloan_set.filter(status='borrowed').first()
        return current_loan is None


class BookCondition(models.Model):
    """Track condition history of book copies"""
    CONDITION_CHOICES = [
        ('good', 'Good'),
        ('damaged', 'Damaged'),
        ('lost', 'Lost'),
    ]
    
    book_copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    notes = models.TextField()
    updated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'book_conditions'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.book_copy} - {self.condition} at {self.updated_at}"


class BookBorrowHistory(models.Model):
    """Historical record of book borrowing"""
    book_copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE)
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE)
    borrow_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'book_borrow_history'
        verbose_name_plural = 'Book Borrow History'
        ordering = ['-borrow_date']
    
    def __str__(self):
        return f"{self.book_copy.book.title} borrowed by {self.user.username}"


class SystemSetting(models.Model):
    """System configuration settings"""
    key = models.CharField(max_length=255, primary_key=True)
    value = models.TextField()
    
    class Meta:
        db_table = 'system_settings'
    
    def __str__(self):
        return f"{self.key}: {self.value}"


# Notification system
class UserNotification(models.Model):
    """User notifications"""
    NOTIFICATION_TYPES = [
        ('due_soon', 'Due Soon'),
        ('overdue', 'Overdue'),
        ('reservation_ready', 'Reservation Ready'),
        ('fine_notice', 'Fine Notice'),
        ('membership_expiry', 'Membership Expiry'),
        ('system_notice', 'System Notice'),
    ]
    
    user = models.ForeignKey('authentication.User', on_delete=models.CASCADE)
    type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'user_notifications'
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.get_type_display()} for {self.user.username}"
