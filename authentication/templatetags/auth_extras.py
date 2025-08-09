from django import template
from authentication.utils import has_role, has_permission

register = template.Library()


@register.filter
def user_has_role(user, role_name):
    """Check if user has a specific role"""
    return has_role(user, role_name)


@register.filter
def user_has_permission(user, permission_name):
    """Check if user has a specific permission"""
    return has_permission(user, permission_name)


@register.simple_tag
def is_librarian(user):
    """Check if user is a librarian"""
    return has_role(user, 'librarian')


@register.simple_tag
def is_manager(user):
    """Check if user is a manager"""
    return has_role(user, 'manager')


@register.simple_tag
def can_manage_books(user):
    """Check if user can manage books"""
    return has_permission(user, 'manage_books')


@register.simple_tag
def can_approve_reservations(user):
    """Check if user can approve reservations"""
    return has_permission(user, 'approve_reservations')


@register.simple_tag
def can_manage_staff(user):
    """Check if user can manage staff"""
    return has_permission(user, 'manage_staff')


@register.simple_tag
def can_generate_reports(user):
    """Check if user can generate reports"""
    return has_permission(user, 'generate_reports')
