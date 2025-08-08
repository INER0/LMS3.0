from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authentication.models import MembershipFee
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Assign student membership to Alex Johnson'

    def handle(self, *args, **options):
        try:
            # Get the student user
            student_user = User.objects.get(username='alex_student')
            
            # Get the student membership fee
            student_membership = MembershipFee.objects.get(
                membership_type='student'
            )
            
            # Assign membership to student
            student_user.membership_fee = student_membership
            student_user.membership_status = 'active'
            student_user.membership_expiry = (
                timezone.now().date() + timedelta(days=365)
            )
            student_user.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully assigned student membership to '
                    f'{student_user.first_name} {student_user.last_name}'
                )
            )
            self.stdout.write(f'Membership Type: {student_membership.membership_type}')
            self.stdout.write(f'Loan Period: {student_membership.loan_period} days')
            self.stdout.write(f'Max Books: {student_membership.max_books}')
            self.stdout.write(f'Monthly Fee: MVR {student_membership.monthly_fee}')
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Student user "alex_student" not found')
            )
        except MembershipFee.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Student membership fee structure not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error assigning membership: {str(e)}')
            )
