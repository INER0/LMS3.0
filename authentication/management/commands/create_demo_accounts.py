"""
Management command to create comprehensive demo accounts for all roles
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authentication.models import Role, UserRole, MembershipFee
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Create comprehensive demo accounts for all user roles'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating demo accounts for all roles...\n'))
        
        # Get or create roles
        member_role, _ = Role.objects.get_or_create(
            name='Member', 
            defaults={'description': 'Regular library member'}
        )
        librarian_role, _ = Role.objects.get_or_create(
            name='Librarian', 
            defaults={'description': 'Library staff member'}
        )
        manager_role, _ = Role.objects.get_or_create(
            name='Manager', 
            defaults={'description': 'Library manager'}
        )
        admin_role, _ = Role.objects.get_or_create(
            name='Admin', 
            defaults={'description': 'System administrator with Django admin access'}
        )
        
        # Get membership types
        basic_membership = MembershipFee.objects.filter(membership_type='basic').first()
        premium_membership = MembershipFee.objects.filter(membership_type='premium').first()
        student_membership = MembershipFee.objects.filter(membership_type='student').first()
        
        # Demo accounts data
        demo_accounts = [
            {
                'username': 'demo_member',
                'email': 'member@demo.com',
                'password': 'demo123',
                'first_name': 'Demo',
                'last_name': 'Member',
                'role': member_role,
                'membership': basic_membership,
                'is_staff': False,
                'is_superuser': False
            },
            {
                'username': 'demo_librarian',
                'email': 'librarian@demo.com',
                'password': 'demo123',
                'first_name': 'Demo',
                'last_name': 'Librarian',
                'role': librarian_role,
                'membership': premium_membership,
                'is_staff': True,
                'is_superuser': False
            },
            {
                'username': 'demo_manager',
                'email': 'manager@demo.com',
                'password': 'demo123',
                'first_name': 'Demo',
                'last_name': 'Manager',
                'role': manager_role,
                'membership': premium_membership,
                'is_staff': True,
                'is_superuser': False
            },
            {
                'username': 'demo_admin',
                'email': 'admin@demo.com',
                'password': 'demo123',
                'first_name': 'Demo',
                'last_name': 'Admin',
                'role': admin_role,
                'membership': None,
                'is_staff': True,
                'is_superuser': True
            }
        ]
        
        # Create or update demo accounts
        for account_data in demo_accounts:
            username = account_data['username']
            role = account_data.pop('role')
            membership = account_data.pop('membership')
            
            try:
                # Get or create user
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults=account_data
                )
                
                if not created:
                    # Update existing user
                    for key, value in account_data.items():
                        if key != 'password':
                            setattr(user, key, value)
                    user.set_password(account_data['password'])
                    
                    # Clear existing roles
                    UserRole.objects.filter(user=user).delete()
                    action = 'Updated'
                else:
                    user.set_password(account_data['password'])
                    action = 'Created'
                
                # Set membership if specified
                if membership:
                    user.membership_fee = membership
                    user.membership_status = 'active'
                    user.membership_expiry = timezone.now().date() + timedelta(days=365)
                
                user.save()
                
                # Assign role
                UserRole.objects.get_or_create(
                    user=user,
                    role=role,
                    defaults={'assigned_by': user}
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'{action} {role.name}: {username} (password: {account_data["password"]})'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating {username}: {str(e)}')
                )
        
        self.stdout.write(self.style.SUCCESS('\n=== Demo Accounts Summary ==='))
        self.stdout.write(self.style.SUCCESS('Member Account:'))
        self.stdout.write('  Username: demo_member')
        self.stdout.write('  Password: demo123')
        self.stdout.write('  Access: Library dashboard, book browsing, borrowing')
        
        self.stdout.write(self.style.SUCCESS('\nLibrarian Account:'))
        self.stdout.write('  Username: demo_librarian') 
        self.stdout.write('  Password: demo123')
        self.stdout.write('  Access: Library management, circulation, member management')
        
        self.stdout.write(self.style.SUCCESS('\nManager Account:'))
        self.stdout.write('  Username: demo_manager')
        self.stdout.write('  Password: demo123')  
        self.stdout.write('  Access: Full library management, staff management, reports')
        
        self.stdout.write(self.style.SUCCESS('\nAdmin Account:'))
        self.stdout.write('  Username: demo_admin')
        self.stdout.write('  Password: demo123')
        self.stdout.write('  Access: Django admin backend, full system control')
        
        self.stdout.write(self.style.SUCCESS('\nSuper Admin Account (existing):'))
        self.stdout.write('  Username: admin')
        self.stdout.write('  Password: admin123')
        self.stdout.write('  Access: Django admin backend, full system control')
        
        self.stdout.write(self.style.SUCCESS('\nAll demo accounts ready for testing! 🚀'))
