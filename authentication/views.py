"""
Authentication views for Library Management System
"""

from django.shortcuts import render, redirect
from django.views.generic import View, TemplateView
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta


class LoginView(View):
    """User login view"""
    template_name = 'authentication/login.html'
    
    def get(self, request):
        # If user is already authenticated, redirect based on role
        if request.user.is_authenticated:
            if request.user.is_super_admin():
                return redirect('/admin/')
            return redirect('library:dashboard')
        return render(request, self.template_name)
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, self.template_name)
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if account is locked
            if hasattr(user, 'is_account_locked') and user.is_account_locked():
                messages.error(request, 'Account is temporarily locked due to multiple failed login attempts.')
                return render(request, self.template_name)
            
            # Login successful
            login(request, user)
            
            # Reset failed login attempts
            user.failed_login_attempts = 0
            user.save()
            
            # Set session expiry based on remember me
            if not remember_me:
                request.session.set_expiry(0)  # Session expires when browser closes
            
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            
            # Check if user is super admin and redirect to Django admin
            if user.is_super_admin():
                return redirect('/admin/')
            
            # Redirect to next page or dashboard for regular users
            next_url = request.GET.get('next', 'library:dashboard')
            return redirect(next_url)
        else:
            # Login failed - increment failed attempts if user exists
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(username=username)
                user.failed_login_attempts += 1
                
                # Lock account after 5 failed attempts
                if user.failed_login_attempts >= 5:
                    user.account_locked = True
                    user.account_locked_until = timezone.now() + timezone.timedelta(minutes=15)
                    messages.error(request, 'Account locked due to too many failed login attempts. Try again in 15 minutes.')
                else:
                    remaining_attempts = 5 - user.failed_login_attempts
                    messages.error(request, f'Invalid credentials. {remaining_attempts} attempts remaining.')
                
                user.save()
            except User.DoesNotExist:
                messages.error(request, 'Invalid username or password.')
            
            return render(request, self.template_name)


class LogoutView(View):
    """User logout view"""
    
    def get(self, request):
        logout(request)
        return redirect('authentication:login')


class RegisterView(View):
    """User registration view"""
    template_name = 'authentication/register.html'
    
    def get(self, request):
        # If user is already authenticated, redirect to dashboard
        if request.user.is_authenticated:
            return redirect('library:dashboard')
        return render(request, self.template_name)
    
    def post(self, request):
        # If user is already authenticated, redirect to dashboard
        if request.user.is_authenticated:
            return redirect('library:dashboard')
            
        # Extract form data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        date_of_birth = request.POST.get('date_of_birth')
        phone_number = request.POST.get('phone_number', '').strip()
        address = request.POST.get('address', '').strip()
        membership_type = request.POST.get('membership_type', 'basic')
        terms = request.POST.get('terms')
        
        # Validation
        errors = []
        
        if not all([first_name, last_name, email, username, password1, password2]):
            errors.append('All required fields must be filled.')
        
        if password1 != password2:
            errors.append('Passwords do not match.')
        
        if len(password1) < 8:
            errors.append('Password must be at least 8 characters long.')
        
        if not terms:
            errors.append('You must agree to the Terms of Service.')
        
        # Check if username already exists
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists. Please choose a different one.')
        
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered. Please use a different email.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, self.template_name)
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            
            # Add optional fields
            if date_of_birth:
                user.date_of_birth = date_of_birth
            if phone_number:
                user.phone_number = phone_number
            if address:
                user.address = address
            
            # Assign membership
            from .models import MembershipFee
            try:
                membership = MembershipFee.objects.get(membership_type=membership_type)
                user.membership_fee = membership
                user.membership_status = 'active'
                user.membership_expiry = timezone.now().date() + timedelta(days=365)
            except MembershipFee.DoesNotExist:
                # Fallback to basic membership
                try:
                    basic_membership = MembershipFee.objects.get(membership_type='basic')
                    user.membership_fee = basic_membership
                    user.membership_status = 'active'
                    user.membership_expiry = timezone.now().date() + timedelta(days=365)
                except MembershipFee.DoesNotExist:
                    pass  # No membership assigned
            
            user.save()
            
            # Auto-login the user
            login(request, user)
            
            messages.success(
                request,
                f'Welcome to the Library Management System, {first_name}! '
                f'Your account has been created successfully.'
            )
            
            return redirect('library:dashboard')
            
        except Exception as e:
            messages.error(request, f'An error occurred during registration: {str(e)}')
            return render(request, self.template_name)


@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
    """User profile view"""
    template_name = 'authentication/profile.html'


@method_decorator(login_required, name='dispatch')
class ChangePasswordView(View):
    """Change password view"""
    template_name = 'authentication/change_password.html'
    
    def get(self, request):
        return render(request, self.template_name)
    
    def post(self, request):
        # TODO: Implement password change logic
        return render(request, self.template_name)


class PasswordResetView(View):
    """Password reset request view"""
    template_name = 'authentication/password_reset.html'
    
    def get(self, request):
        return render(request, self.template_name)
    
    def post(self, request):
        # TODO: Implement password reset logic
        return render(request, self.template_name)


class PasswordResetConfirmView(View):
    """Password reset confirmation view"""
    template_name = 'authentication/password_reset_confirm.html'
    
    def get(self, request, token):
        return render(request, self.template_name, {'token': token})
    
    def post(self, request, token):
        # TODO: Implement password reset confirmation logic
        return render(request, self.template_name, {'token': token})


@method_decorator(login_required, name='dispatch')
class MFASetupView(TemplateView):
    """MFA setup view"""
    template_name = 'authentication/mfa_setup.html'


@method_decorator(login_required, name='dispatch')
class MFAVerifyView(View):
    """MFA verification view"""
    template_name = 'authentication/mfa_verify.html'
    
    def get(self, request):
        return render(request, self.template_name)
    
    def post(self, request):
        # TODO: Implement MFA verification logic
        return render(request, self.template_name)
