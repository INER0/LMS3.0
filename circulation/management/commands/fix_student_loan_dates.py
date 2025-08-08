from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from circulation.models import BookLoan
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Fix loan due dates for student users to be 21 days'

    def handle(self, *args, **options):
        try:
            # Get the student user
            student_user = User.objects.get(username='alex_student')
            
            if not student_user.membership_fee:
                self.stdout.write(
                    self.style.ERROR('Student user has no membership assigned')
                )
                return
                
            # Get all active loans for the student
            active_loans = BookLoan.objects.filter(
                user=student_user,
                status='borrowed'
            )
            
            updated_count = 0
            for loan in active_loans:
                # Calculate correct due date (21 days from borrow date)
                correct_due_date = loan.borrow_date + timedelta(
                    days=student_user.membership_fee.loan_period
                )
                
                if loan.due_date != correct_due_date:
                    old_due_date = loan.due_date
                    loan.due_date = correct_due_date
                    loan.save()
                    
                    self.stdout.write(
                        f'Updated loan for "{loan.book_copy.book.title}": '
                        f'{old_due_date} → {correct_due_date}'
                    )
                    updated_count += 1
                else:
                    self.stdout.write(
                        f'Loan for "{loan.book_copy.book.title}" '
                        f'already has correct due date: {loan.due_date}'
                    )
            
            if updated_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully updated {updated_count} loan(s) '
                        f'for student user'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING('No loans needed updating')
                )
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Student user "alex_student" not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error fixing loan dates: {str(e)}')
            )
