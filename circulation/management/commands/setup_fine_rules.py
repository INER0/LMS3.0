from django.core.management.base import BaseCommand
from circulation.models import FineRule


class Command(BaseCommand):
    help = 'Setup fine rules for overdue books according to library policy'

    def handle(self, *args, **options):
        # Clear existing fine rules
        FineRule.objects.all().delete()
        
        # Create overdue fine rules according to specification
        fine_rules = [
            {
                'fine_type': 'overdue',
                'delay_from': 1,
                'delay_to': 3,
                'rate_per_day': 2.00,
                'processing_fee': 0.00,
                'description': '1-3 Days Late: 2 MVR per day'
            },
            {
                'fine_type': 'overdue',
                'delay_from': 4,
                'delay_to': 7,
                'rate_per_day': 5.00,
                'processing_fee': 0.00,
                'description': '4-7 Days Late: 5 MVR per day'
            },
            {
                'fine_type': 'overdue',
                'delay_from': 8,
                'delay_to': 999,  # More than 7 days
                'rate_per_day': 10.00,
                'processing_fee': 0.00,
                'description': 'More than 7 Days: 10 MVR per day'
            },
            {
                'fine_type': 'lost',
                'delay_from': 1,
                'delay_to': 999,
                'rate_per_day': 0.00,  # Not per day, but full book price
                'processing_fee': 50.00,
                'description': ('Lost Book: Full Book Price + '
                                '50 MVR Processing Fee')
            },
            {
                'fine_type': 'damaged',
                'delay_from': 1,
                'delay_to': 999,
                'rate_per_day': 0.00,  # Not per day, but full book price
                'processing_fee': 50.00,
                'description': ('Damaged Book: Full Book Price + '
                                '50 MVR Processing Fee')
            }
        ]
        
        created_rules = 0
        
        for rule_data in fine_rules:
            FineRule.objects.create(
                fine_type=rule_data['fine_type'],
                delay_from=rule_data['delay_from'],
                delay_to=rule_data['delay_to'],
                rate_per_day=rule_data['rate_per_day'],
                processing_fee=rule_data['processing_fee']
            )
            created_rules += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Created: {rule_data["description"]}'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully created {created_rules} fine rules'
            )
        )
        
        # Test the calculation
        self.stdout.write('\nTesting fine calculations:')
        test_cases = [1, 2, 3, 4, 5, 6, 7, 8, 10, 15, 30]
        
        for days in test_cases:
            fine = FineRule.calculate_overdue_fine(days)
            self.stdout.write(f'  {days} days overdue: MVR {fine}')
