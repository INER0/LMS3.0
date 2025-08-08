"""
Management command to update membership fees to match specification
"""

from django.core.management.base import BaseCommand
from authentication.models import MembershipFee


class Command(BaseCommand):
    help = 'Update membership fees to match the correct specification'
    
    def handle(self, *args, **options):
        # Correct membership fee structure from specification
        correct_fees = {
            'basic': {
                'monthly_fee': 50.00,
                'annual_fee': 500.00,
                'max_books': 3,
                'loan_period': 14,
                'extension_days': 0
            },
            'premium': {
                'monthly_fee': 75.00,
                'annual_fee': 750.00,
                'max_books': 5,
                'loan_period': 14,
                'extension_days': 7
            },
            'student': {
                'monthly_fee': 30.00,
                'annual_fee': 300.00,
                'max_books': 4,
                'loan_period': 21,
                'extension_days': 0
            }
        }
        
        updated_count = 0
        created_count = 0
        
        for membership_type, data in correct_fees.items():
            try:
                fee = MembershipFee.objects.get(membership_type=membership_type)
                # Update existing
                fee.monthly_fee = data['monthly_fee']
                fee.annual_fee = data['annual_fee']
                fee.max_books = data['max_books']
                fee.loan_period = data['loan_period']
                fee.extension_days = data['extension_days']
                fee.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated {membership_type} membership fee'
                    )
                )
                updated_count += 1
                
            except MembershipFee.DoesNotExist:
                # Create new
                fee = MembershipFee.objects.create(
                    membership_type=membership_type,
                    **data
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created {membership_type} membership fee'
                    )
                )
                created_count += 1
        
        # Remove old membership types not in specification
        unwanted_types = ['regular']  # Remove the 'regular' type that's not in spec
        for membership_type in unwanted_types:
            deleted_count = MembershipFee.objects.filter(
                membership_type=membership_type
            ).delete()[0]
            if deleted_count > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'Removed {deleted_count} {membership_type} membership(s)'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Membership fees updated: {updated_count} updated, '
                f'{created_count} created'
            )
        )
        
        # Display final structure
        self.stdout.write('\nFinal membership structure:')
        for fee in MembershipFee.objects.all():
            self.stdout.write(
                f'  {fee.membership_type.title()}: {fee.loan_period} days, '
                f'{fee.max_books} books max, MVR {fee.monthly_fee}/month'
            )
