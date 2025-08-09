"""
Management command to create or update a super admin user
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authentication.models import Role, UserRole

User = get_user_model()


class Command(BaseCommand):
    help = 'Create or update a super admin user with Django admin access'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Username for the super admin (default: admin)',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@library.com',
            help='Email for the super admin (default: admin@library.com)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123',
            help='Password for the super admin (default: admin123)',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        # Get or create the Admin role
        admin_role, created = Role.objects.get_or_create(
            name='Admin',
            defaults={'description': 'System administrator with Django admin access'}
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created Admin role')
            )

        # Check if user already exists
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'User {username} already exists. Updating...')
            
            # Update user properties
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)
            user.save()
            
        except User.DoesNotExist:
            # Create new super admin user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name='Super',
                last_name='Admin',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(f'Created new user {username}')

        # Assign Admin role to user
        user_role, created = UserRole.objects.get_or_create(
            user=user,
            role=admin_role,
            defaults={'assigned_by': user}
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Assigned Admin role to {username}')
            )
        else:
            self.stdout.write(f'User {username} already has Admin role')

        self.stdout.write(
            self.style.SUCCESS(
                f'Super admin setup complete!\n'
                f'Username: {username}\n'
                f'Password: {password}\n'
                f'This user will be redirected to Django admin (/admin/) upon login.'
            )
        )
