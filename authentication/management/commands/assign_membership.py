"""
Management command to assign default membership fees to users without them
"""

from django.core.management.base import BaseCommand
from authentication.models import User, MembershipFee


class Command(BaseCommand):
    help = 'Assign default membership fees to users without them'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--membership-type',
            type=str,
            default='basic',
            help='Default membership type to assign (basic, premium, student)'
        )
    
    def handle(self, *args, **options):
        membership_type = options['membership_type']
        
        try:
            default_membership = MembershipFee.objects.get(
                membership_type=membership_type
            )
        except MembershipFee.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'Membership type "{membership_type}" does not exist'
                )
            )
            return
        
        # Find users without membership fees
        users_without_membership = User.objects.filter(membership_fee__isnull=True)
        
        count = 0
        for user in users_without_membership:
            user.membership_fee = default_membership
            user.save()
            count += 1
            self.stdout.write(
                f'Assigned {membership_type} membership to {user.username}'
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully assigned {membership_type} membership to '
                f'{count} users'
            )
        )
