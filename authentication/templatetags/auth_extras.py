from django import template
from authentication.utils import (
    has_role as utils_has_role, 
    has_permission as utils_has_permission
)

register = template.Library()


@register.filter
def user_has_role(user, role_name):
    """Check if user has a specific role"""
    return utils_has_role(user, role_name)


@register.filter
def has_role(user, role_name):
    """Check if user has a specific role - alias for user_has_role"""
    return utils_has_role(user, role_name)


@register.filter
def user_has_permission(user, permission_name):
    """Check if user has a specific permission"""
    return utils_has_permission(user, permission_name)


@register.simple_tag
def is_librarian(user):
    """Check if user is a librarian"""
    return utils_has_role(user, 'librarian')


@register.simple_tag
def is_manager(user):
    """Check if user is a manager"""
    return utils_has_role(user, 'manager')


@register.simple_tag
def can_manage_books(user):
    """Check if user can manage books"""
    return utils_has_permission(user, 'manage_books')


@register.simple_tag
def can_approve_reservations(user):
    """Check if user can approve reservations"""
    return utils_has_permission(user, 'approve_reservations')


@register.simple_tag
def can_manage_staff(user):
    """Check if user can manage staff"""
    return utils_has_permission(user, 'manage_staff')


@register.simple_tag
def can_generate_reports(user):
    """Check if user can generate reports"""
    return utils_has_permission(user, 'generate_reports')
