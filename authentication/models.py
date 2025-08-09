"""
Authentication models for Library Management System
Implements user management, roles, and security features
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from decimal import Decimal
from datetime import date


class MembershipFee(models.Model):
    """Membership fee structure"""
    MEMBERSHIP_TYPES = [
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('student', 'Student'),
    ]
    
    membership_type = models.CharField(
        max_length=20, 
        choices=MEMBERSHIP_TYPES, 
        unique=True
    )
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2)
    annual_fee = models.DecimalField(max_digits=10, decimal_places=2)
    max_books = models.IntegerField(
        help_text="Maximum books that can be borrowed"
    )
    loan_period = models.IntegerField(help_text="Loan period in days")
    extension_days = models.IntegerField(
        help_text="Extension period in days", 
        default=0
    )
    
    class Meta:
        db_table = 'membership_fees'
    
    def __str__(self):
        type_display = self.get_membership_type_display()
        amount = f"{self.monthly_fee:.2f}"
        return f"{type_display} Member - MVR {amount}/month"


class User(AbstractUser):
    """Custom user model extending Django's AbstractUser"""
    MEMBERSHIP_STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]
    
    membership_fee = models.ForeignKey(
        MembershipFee, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True
    )
    membership_status = models.CharField(
        max_length=20,
        choices=MEMBERSHIP_STATUS_CHOICES,
        default='active'
    )
    membership_expiry = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    national_id = models.CharField(max_length=20, null=True, blank=True, unique=True)
    
    # Security fields
    failed_login_attempts = models.IntegerField(default=0)
    account_locked = models.BooleanField(default=False)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    force_password_change = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    def is_super_admin(self):
        """Check if user has Admin role (super admin)"""
        try:
            admin_role = Role.objects.get(name='Admin')
            return UserRole.objects.filter(user=self, role=admin_role).exists()
        except Role.DoesNotExist:
            return False

    def save(self, *args, **kwargs):
        """Override save to handle empty national_id as NULL"""
        if self.national_id == '':
            self.national_id = None
        super().save(*args, **kwargs)
    
    def is_account_locked(self):
        """Check if account is currently locked"""
        if self.account_locked_until and timezone.now() > \
                self.account_locked_until:
            # Auto-unlock expired locks
            self.account_locked = False
            self.account_locked_until = None
            self.save()
        return self.account_locked
    
    def get_full_name(self):
        """Return the full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username


class Role(models.Model):
    """User roles for permission management"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'roles'
    
    def __str__(self):
        return self.name


class Permission(models.Model):
    """System permissions"""
    code = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    
    class Meta:
        db_table = 'permissions'
    
    def __str__(self):
        return self.code


class UserRole(models.Model):
    """User-Role relationship"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='assigned_roles'
    )
    
    class Meta:
        db_table = 'user_roles'
        unique_together = ['user', 'role']


class RolePermission(models.Model):
    """Role-Permission relationship"""
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'role_permissions'
        unique_together = ['role', 'permission']


class PasswordHistory(models.Model):
    """Track password history for security"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    password_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'password_history'
        ordering = ['-created_at']


class LoginAttempt(models.Model):
    """Track login attempts for security monitoring"""
    ATTEMPT_TYPES = [
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('blocked', 'Blocked'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    attempt_type = models.CharField(max_length=10, choices=ATTEMPT_TYPES)
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'login_attempts'
        ordering = ['-attempted_at']


class AuditLog(models.Model):
    """System audit logging"""
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('view', 'View'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    action_type = models.CharField(max_length=10, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        user_display = self.user.username if self.user else 'Anonymous'
        return f"{user_display} - {self.action_type} - {self.timestamp}"
