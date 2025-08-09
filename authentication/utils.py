"""
Utility functions for role-based access control
"""

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from authentication.models import UserRole, RolePermission


def has_permission(user, permission_code):
    """Check if user has specific permission"""
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    # Get user roles
    user_roles = UserRole.objects.filter(user=user).values_list(
        'role', flat=True
    )
    
    # Check if any role has the permission
    return RolePermission.objects.filter(
        role__in=user_roles,
        permission__code=permission_code
    ).exists()


def has_role(user, role_name):
    """Check if user has specific role"""
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    return UserRole.objects.filter(
        user=user,
        role__name=role_name
    ).exists()


def get_user_roles(user):
    """Get list of user's role names"""
    if not user.is_authenticated:
        return []
    
    return list(UserRole.objects.filter(user=user).values_list(
        'role__name', flat=True
    ))


def get_user_permissions(user):
    """Get list of user's permission codes"""
    if not user.is_authenticated:
        return []
    
    if user.is_superuser:
        # Superuser has all permissions
        from authentication.models import Permission
        return list(Permission.objects.values_list('code', flat=True))
    
    user_roles = UserRole.objects.filter(user=user).values_list(
        'role', flat=True
    )
    
    return list(RolePermission.objects.filter(
        role__in=user_roles
    ).values_list('permission__code', flat=True))


def require_permission(permission_code, redirect_url=None):
    """Decorator to require specific permission"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not has_permission(request.user, permission_code):
                if redirect_url:
                    messages.error(
                        request,
                        f'You do not have permission to access this page. '
                        f'Required permission: {permission_code}'
                    )
                    return redirect(redirect_url)
                else:
                    raise PermissionDenied(
                        f'Permission denied. Required: {permission_code}'
                    )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_role(role_name, redirect_url=None):
    """Decorator to require specific role"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not has_role(request.user, role_name):
                if redirect_url:
                    messages.error(
                        request,
                        f'You do not have access to this page. '
                        f'Required role: {role_name.title()}'
                    )
                    return redirect(redirect_url)
                else:
                    raise PermissionDenied(
                        f'Permission denied. Required role: {role_name}'
                    )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def staff_required(view_func):
    """Decorator to require librarian or manager role"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (has_role(request.user, 'librarian') or
                has_role(request.user, 'manager') or
                request.user.is_superuser):
            messages.error(
                request,
                'You must be a librarian or manager to access this page.'
            )
            return redirect('library:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_required(view_func):
    """Decorator to require manager role"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (has_role(request.user, 'manager') or
                request.user.is_superuser):
            messages.error(
                request,
                'You must be a manager to access this page.'
            )
            return redirect('library:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
