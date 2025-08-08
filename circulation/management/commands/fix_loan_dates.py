"""
Management command to fix existing loan due dates based on membership fees
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from circulation.models import BookLoan
from authentication.models import MembershipFee


class Command(BaseCommand):
    help = 'Fix existing loan due dates based on proper membership fees'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all active loans
        active_loans = BookLoan.objects.filter(status='borrowed')
        
        self.stdout.write(f'Found {active_loans.count()} active loans')
        
        fixed_count = 0
        for loan in active_loans:
            user = loan.user
            
            # Get correct loan period based on user's membership
            if user.membership_fee:
                loan_period = user.membership_fee.loan_period
                membership_type = user.membership_fee.membership_type
            else:
                # Default to basic membership
                loan_period = 14
                membership_type = 'basic (default)'
            
            # Calculate correct due date
            correct_due_date = loan.borrow_date + timedelta(days=loan_period)
            
            if loan.due_date != correct_due_date:
                self.stdout.write(
                    f'User: {user.username} ({membership_type})\n'
                    f'  Book: {loan.book_copy.book.title}\n'
                    f'  Borrow Date: {loan.borrow_date}\n'
                    f'  Current Due Date: {loan.due_date}\n'
                    f'  Correct Due Date: {correct_due_date}\n'
                    f'  Loan Period: {loan_period} days\n'
                )
                
                if not dry_run:
                    loan.due_date = correct_due_date
                    loan.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Updated due date')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  → Would update due date (dry run)')
                    )
                
                fixed_count += 1
                self.stdout.write('---')
        
        if fixed_count == 0:
            self.stdout.write(
                self.style.SUCCESS('All loan due dates are already correct!')
            )
        else:
            action = 'Would fix' if dry_run else 'Fixed'
            self.stdout.write(
                self.style.SUCCESS(
                    f'{action} {fixed_count} loan due dates'
                )
            )
