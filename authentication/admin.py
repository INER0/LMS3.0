from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, UserRole, Permission, RolePermission, MembershipFee


@admin.register(MembershipFee)
class MembershipFeeAdmin(admin.ModelAdmin):
    list_display = ['membership_type', 'monthly_fee', 'annual_fee', 'max_books', 'loan_period']
    list_filter = ['membership_type']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['code', 'description']
    search_fields = ['code', 'description']


class UserRoleInline(admin.TabularInline):
    model = UserRole
    fk_name = 'user'  # Specify which foreign key to use
    extra = 1
    readonly_fields = ['assigned_at']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'membership_status', 'get_roles', 'is_super_admin']
    list_filter = ['membership_status', 'is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Membership Info', {
            'fields': ('membership_fee', 'membership_status', 'membership_expiry')
        }),
        ('Personal Info Extended', {
            'fields': ('phone_number', 'address', 'date_of_birth', 'national_id')
        }),
        ('Security', {
            'fields': ('failed_login_attempts', 'account_locked', 'account_locked_until', 
                      'password_changed_at', 'force_password_change')
        }),
    )
    
    inlines = [UserRoleInline]
    
    def get_roles(self, obj):
        """Display user roles"""
        roles = UserRole.objects.filter(user=obj).select_related('role')
        return ', '.join([ur.role.name for ur in roles])
    get_roles.short_description = 'Roles'
    
    def is_super_admin(self, obj):
        """Display if user is super admin"""
        return obj.is_super_admin()
    is_super_admin.boolean = True
    is_super_admin.short_description = 'Super Admin'


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'assigned_at', 'assigned_by']
    list_filter = ['role', 'assigned_at']
    search_fields = ['user__username', 'user__email', 'role__name']


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'permission']
    list_filter = ['role']
    search_fields = ['role__name', 'permission__code']