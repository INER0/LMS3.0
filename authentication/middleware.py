"""
Custom middleware for Library Management System
Implements session timeout and audit logging
"""

from django.utils import timezone
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.conf import settings
from .models import LoginAttempt, AuditLog
import logging

logger = logging.getLogger(__name__)


class SessionTimeoutMiddleware:
    """
    Middleware to handle session timeout
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Check session timeout
            last_activity = request.session.get('last_activity')
            if last_activity:
                time_since_activity = (timezone.now().timestamp() - last_activity)
                if time_since_activity > settings.SESSION_COOKIE_AGE:
                    # Session expired
                    logout(request)
                    return redirect('authentication:login')
            
            # Update last activity
            request.session['last_activity'] = timezone.now().timestamp()
            
            # Log activity if needed
            try:
                skip_paths = ['/admin/jsi18n/', '/static/', '/media/']
                if request.path not in skip_paths:
                    AuditLog.objects.create(
                        user=request.user,
                        action_type='view',
                        description=f"Accessed {request.path}",
                        ip_address=self._get_client_ip(request)
                    )
            except Exception as e:
                logger.error(f"Error logging activity: {e}")

        response = self.get_response(request)
        return response
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AuditLogMiddleware:
    """
    Middleware to log user activities for audit trail
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Log significant activities
        if request.user.is_authenticated and request.method in ['POST', 'PUT', 'DELETE']:
            self._log_activity(request, response)
        
        return response
    
    def _log_activity(self, request, response):
        """Log user activity"""
        try:
            # Skip logging for certain paths
            skip_paths = ['/admin/jsi18n/', '/static/', '/media/']
            if any(request.path.startswith(path) for path in skip_paths):
                return
            
            # Determine action
            action = f"{request.method} {request.path}"
            
            # Get additional details
            details = {
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
            
            # Add POST data (excluding sensitive fields)
            if request.method == 'POST':
                post_data = request.POST.copy()
                # Remove sensitive fields
                sensitive_fields = ['password', 'password1', 'password2', 'old_password']
                for field in sensitive_fields:
                    if field in post_data:
                        post_data[field] = '[REDACTED]'
                details['post_data'] = dict(post_data)
            
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action_type='update',
                description=action,
                ip_address=self._get_client_ip(request)
            )
            
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add CSP header for enhanced security
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self';"
        )
        response['Content-Security-Policy'] = csp_policy
        
        return response
