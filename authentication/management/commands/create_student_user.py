from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authentication.models import MembershipFee
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a student demo user account'

    def handle(self, *args, **options):
        try:
            # Create student user
            student_username = 'alex_student'
            if not User.objects.filter(username=student_username).exists():
                student_user = User.objects.create_user(
                    username=student_username,
                    email='alex.student@university.edu',
                    password='test123',
                    first_name='Alex',
                    last_name='Johnson',
                    date_of_birth='2001-05-15',
                    phone_number='+960-7123456',
                    address='Student Dormitory, Block A, Room 203',
                    national_id='A123456789'
                )
                
                # Get or create student membership fee
                student_membership, created = MembershipFee.objects.get_or_create(
                    membership_type='student',
                    defaults={
                        'monthly_fee': 30.00,
                        'annual_fee': 300.00,
                        'max_books': 4,
                        'loan_period': 21,
                        'extension_days': 0
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS('Created student membership fee')
                    )
                
                # Assign membership to student
                student_user.membership = student_membership
                student_user.membership_start_date = timezone.now().date()
                end_date = timezone.now().date() + timedelta(days=365)
                student_user.membership_end_date = end_date
                student_user.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created student user: {student_username}'
                    )
                )
                self.stdout.write('Email: alex.student@university.edu')
                self.stdout.write('Password: test123')
                self.stdout.write('Membership: Student (21-day loan period)')
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Student user {student_username} already exists'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating student user: {str(e)}')
            )
