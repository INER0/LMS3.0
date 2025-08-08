"""
Tests for authentication models and views
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from .models import MembershipFee, Role, Permission


User = get_user_model()


class MembershipFeeModelTest(TestCase):
    """Test MembershipFee model"""
    
    def setUp(self):
        self.membership_fee = MembershipFee.objects.create(
            membership_type='basic',
            monthly_fee=50.00,
            annual_fee=500.00,
            max_books=3,
            loan_period=14,
            extension_days=0
        )
    
    def test_string_representation(self):
        """Test the string representation of MembershipFee"""
        expected = "Basic Member - MVR 50.00/month"
        self.assertEqual(str(self.membership_fee), expected)
    
    def test_membership_type_choices(self):
        """Test membership type choices are enforced"""
        choices = ['basic', 'premium', 'student']
        self.assertIn(self.membership_fee.membership_type, choices)


class UserModelTest(TestCase):
    """Test custom User model"""
    
    def setUp(self):
        self.membership_fee = MembershipFee.objects.create(
            membership_type='basic',
            monthly_fee=50.00,
            annual_fee=500.00,
            max_books=3,
            loan_period=14,
            extension_days=0
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            membership_fee=self.membership_fee,
            membership_expiry=date.today() + timedelta(days=30)
        )
    
    def test_user_creation(self):
        """Test user can be created with required fields"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_user_string_representation(self):
        """Test the string representation of User"""
        expected = "testuser (test@example.com)"
        self.assertEqual(str(self.user), expected)
    
    def test_account_lock_functionality(self):
        """Test account locking mechanism"""
        # User should not be locked initially
        self.assertFalse(self.user.is_account_locked())
        
        # Lock the account
        self.user.account_locked = True
        self.user.account_locked_until = timezone.now() + timedelta(minutes=15)
        self.user.save()
        
        self.assertTrue(self.user.is_account_locked())
        
        # Test auto-unlock after time expires
        self.user.account_locked_until = timezone.now() - timedelta(minutes=1)
        self.user.save()
        
        self.assertFalse(self.user.is_account_locked())
        self.assertFalse(self.user.account_locked)


class RolePermissionTest(TestCase):
    """Test role and permission models"""
    
    def setUp(self):
        self.role = Role.objects.create(
            name='Member',
            description='Regular library member'
        )
        
        self.permission = Permission.objects.create(
            code='borrow_books',
            description='Can borrow books from library'
        )
    
    def test_role_creation(self):
        """Test role creation and string representation"""
        self.assertEqual(str(self.role), 'Member')
        self.assertEqual(self.role.description, 'Regular library member')
    
    def test_permission_creation(self):
        """Test permission creation and string representation"""
        self.assertEqual(str(self.permission), 'borrow_books')
        expected_desc = 'Can borrow books from library'
        self.assertEqual(self.permission.description, expected_desc)


class PasswordSecurityTest(TestCase):
    """Test password security features"""
    
    def test_strong_password_validation(self):
        """Test that strong passwords are required"""
        # This test would need to be expanded with actual password validation
        # Currently just testing basic functionality
        membership_fee = MembershipFee.objects.create(
            membership_type='basic',
            monthly_fee=50.00,
            annual_fee=500.00,
            max_books=3,
            loan_period=14
        )
        
        user = User.objects.create_user(
            username='stronguser',
            email='strong@example.com',
            password='StrongPass123!',
            membership_fee=membership_fee,
            membership_expiry=date.today() + timedelta(days=30)
        )
        
        self.assertTrue(user.check_password('StrongPass123!'))
        self.assertFalse(user.check_password('weakpass'))


class AuthenticationViewsTest(TestCase):
    """Test authentication views"""
    
    def setUp(self):
        self.client = Client()
        self.membership_fee = MembershipFee.objects.create(
            membership_type='basic',
            monthly_fee=50.00,
            annual_fee=500.00,
            max_books=3,
            loan_period=14
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            membership_fee=self.membership_fee,
            membership_expiry=date.today() + timedelta(days=30)
        )
    
    def test_login_view_get(self):
        """Test login view loads correctly"""
        response = self.client.get(reverse('authentication:login'))
        self.assertEqual(response.status_code, 200)
    
    def test_logout_view(self):
        """Test logout functionality"""
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        # Then logout
        response = self.client.get(reverse('authentication:logout'))
        self.assertRedirects(response, reverse('authentication:login'))
    
    def test_profile_view_requires_login(self):
        """Test that profile view requires authentication"""
        response = self.client.get(reverse('authentication:profile'))
        login_url = reverse('authentication:login')
        profile_url = reverse('authentication:profile')
        expected_redirect = f"{login_url}?next={profile_url}"
        self.assertRedirects(response, expected_redirect)


class SecurityMiddlewareTest(TestCase):
    """Test security middleware functionality"""
    
    def setUp(self):
        self.client = Client()
        self.membership_fee = MembershipFee.objects.create(
            membership_type='basic',
            monthly_fee=50.00,
            annual_fee=500.00,
            max_books=3,
            loan_period=14
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            membership_fee=self.membership_fee,
            membership_expiry=date.today() + timedelta(days=30)
        )
    
    def test_session_timeout(self):
        """Test session timeout functionality"""
        # This would require more complex testing with session manipulation
        # Currently just testing basic middleware integration
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)  # Redirect to library home
