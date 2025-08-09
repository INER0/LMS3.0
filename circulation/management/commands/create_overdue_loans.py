"""
Management command to create overdue loans for testing fine calculations.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from circulation.models import BookLoan, FineRule, Fine
from library.models import BookCopy

User = get_user_model()


class Command(BaseCommand):
    help = 'Create overdue loans for testing fine calculations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='johndoe',
            help='Username to create overdue loans for (default: johndoe)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing loans and fines for this user first'
        )

    def handle(self, *args, **options):
        username = options['username']
        clear_existing = options['clear']
        
        try:
            # Get or create the user
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'email': f'{username}@example.com'
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created user: {user.username}')
                )
            else:
                self.stdout.write(f'Using existing user: {user.username}')

            # Clear existing data if requested
            if clear_existing:
                existing_loans = BookLoan.objects.filter(user=user)
                existing_fines = Fine.objects.filter(user=user)
                loans_count = existing_loans.count()
                fines_count = existing_fines.count()
                existing_loans.delete()
                existing_fines.delete()
                self.stdout.write(
                    f'Cleared {loans_count} existing loans and '
                    f'{fines_count} existing fines'
                )

            # Get available book copies (not currently borrowed)
            all_copies = BookCopy.objects.filter(condition='good')
            available_copies = []
            
            for copy in all_copies:
                if copy.is_available:
                    available_copies.append(copy)
                if len(available_copies) >= 3:
                    break

            if len(available_copies) < 3:
                self.stdout.write(
                    self.style.ERROR(
                        f'Not enough available copies. Found '
                        f'{len(available_copies)}, need 3.'
                    )
                )
                return

            # Create loans with different overdue periods
            today = timezone.now().date()
            overdue_scenarios = [
                {
                    'days_overdue': 2,  # 2 days overdue (1-3 days: 2 MVR/day)
                    'description': '2 days overdue - should be 4 MVR total'
                },
                {
                    'days_overdue': 5,  # 5 days overdue (4-7 days: 5 MVR/day)
                    'description': '5 days overdue - should be 25 MVR total'
                },
                {
                    'days_overdue': 10,  # 10 days overdue (>7 days: 10 MVR)
                    'description': '10 days overdue - should be 100 MVR total'
                }
            ]

            created_loans = []
            
            for i, scenario in enumerate(overdue_scenarios):
                copy = available_copies[i]
                
                # Calculate loan and due dates
                days_overdue = scenario['days_overdue']
                borrow_date = today - timedelta(days=14 + days_overdue)
                due_date = borrow_date + timedelta(days=14)
                
                # Create the loan
                loan = BookLoan.objects.create(
                    user=user,
                    book_copy=copy,
                    borrow_date=borrow_date,
                    due_date=due_date,
                    status='borrowed'
                )
                
                # Calculate fine
                fine_amount = FineRule.calculate_overdue_fine(
                    scenario['days_overdue']
                )
                
                # Create Fine record
                Fine.objects.create(
                    user=user,
                    book_loan=loan,
                    amount=fine_amount,
                    fine_type='overdue',
                    description=(
                        f'Overdue fine for {copy.book.title} - '
                        f'{scenario["days_overdue"]} days overdue'
                    )
                )
                
                created_loans.append({
                    'loan': loan,
                    'scenario': scenario,
                    'fine': fine_amount
                })
                
                self.stdout.write(
                    f'Created loan for {copy.book.title} ({copy.barcode})'
                )
                self.stdout.write(
                    f'  - Loan Date: {borrow_date}'
                )
                self.stdout.write(
                    f'  - Due Date: {due_date}'
                )
                self.stdout.write(
                    f'  - Days Overdue: {scenario["days_overdue"]}'
                )
                self.stdout.write(
                    f'  - Fine Amount: MVR {fine_amount}'
                )
                self.stdout.write(
                    f'  - Description: {scenario["description"]}'
                )
                self.stdout.write('---')

            # Summary
            total_fine = sum(loan_data['fine'] for loan_data in created_loans)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {len(created_loans)} overdue '
                    f'loans for {user.username}'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(f'Total expected fines: MVR {total_fine}')
            )
            
            self.stdout.write('\nFine Calculation Breakdown:')
            self.stdout.write('- 1-3 days overdue: MVR 2 per day')
            self.stdout.write('- 4-7 days overdue: MVR 5 per day')
            self.stdout.write('- 8+ days overdue: MVR 10 per day')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating overdue loans: {str(e)}')
            )
