"""
Management command to create test users for the LMS
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from authentication.models import MembershipFee, Role, Permission

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test users for the Library Management System'

    def handle(self, *args, **options):
        # Create membership fee if it doesn't exist
        basic_membership, created = MembershipFee.objects.get_or_create(
            membership_type='basic',
            defaults={
                'monthly_fee': 50.00,
                'annual_fee': 500.00,
                'max_books': 3,
                'loan_period': 14,
                'extension_days': 7
            }
        )
        
        premium_membership, created = MembershipFee.objects.get_or_create(
            membership_type='premium',
            defaults={
                'monthly_fee': 100.00,
                'annual_fee': 1000.00,
                'max_books': 10,
                'loan_period': 21,
                'extension_days': 14
            }
        )

        # Test users to create
        test_users = [
            {
                'username': 'john_member',
                'email': 'john@example.com',
                'password': 'test123',
                'first_name': 'John',
                'last_name': 'Doe',
                'national_id': 'A123456789',
                'membership_fee': basic_membership,
                'is_staff': False,
                'description': 'Basic Member - Regular library user'
            },
            {
                'username': 'sara_premium',
                'email': 'sara@example.com',
                'password': 'test123',
                'first_name': 'Sara',
                'last_name': 'Smith',
                'national_id': 'A987654321',
                'membership_fee': premium_membership,
                'is_staff': False,
                'description': 'Premium Member - Extended privileges'
            },
            {
                'username': 'mike_librarian',
                'email': 'mike@example.com',
                'password': 'test123',
                'first_name': 'Mike',
                'last_name': 'Wilson',
                'national_id': 'A555666777',
                'membership_fee': basic_membership,
                'is_staff': True,
                'description': 'Librarian - Can manage books and loans'
            },
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'password': 'admin123',
                'first_name': 'System',
                'last_name': 'Administrator',
                'national_id': 'A000000001',
                'membership_fee': premium_membership,
                'is_staff': True,
                'is_superuser': True,
                'description': 'System Admin - Full access to all features'
            }
        ]

        for user_data in test_users:
            username = user_data['username']
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'User {username} already exists')
                )
                continue

            description = user_data.pop('description')
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                national_id=user_data['national_id'],
                membership_fee=user_data['membership_fee'],
                membership_expiry=date.today() + timedelta(days=365),
                is_staff=user_data.get('is_staff', False),
                is_superuser=user_data.get('is_superuser', False)
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Created user: {username} - {description}'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                '\nTest users created successfully!\n'
                'You can now use these credentials to test the system:'
            )
        )
