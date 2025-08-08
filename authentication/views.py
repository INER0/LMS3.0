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
        # If user is already authenticated, redirect to dashboard
        if request.user.is_authenticated:
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
            
            # Redirect to next page or dashboard
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
        return render(request, self.template_name)
    
    def post(self, request):
        # TODO: Implement registration logic
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
