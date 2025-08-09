"""
Management command to assign roles to users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authentication.models import Role, UserRole

User = get_user_model()


class Command(BaseCommand):
    help = 'Assign roles to users'

    def add_arguments(self, parser):
        parser.add_argument(
            'username', type=str, help='Username to assign role'
        )
        parser.add_argument(
            'role', type=str, help='Role name (librarian/manager)'
        )

    def handle(self, *args, **options):
        username = options['username']
        role_name = options['role']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User "{username}" not found')
            )
            return

        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Role "{role_name}" not found')
            )
            return

        user_role, created = UserRole.objects.get_or_create(
            user=user,
            role=role
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully assigned "{role_name}" role to "{username}"'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'User "{username}" already has "{role_name}" role'
                )
            )
