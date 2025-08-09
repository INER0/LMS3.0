"""
Management command to setup staff roles and permissions
"""

from django.core.management.base import BaseCommand
from authentication.models import Role, Permission, RolePermission


class Command(BaseCommand):
    help = 'Setup librarian and manager roles with permissions'

    def handle(self, *args, **options):
        # Create roles
        librarian_role, created = Role.objects.get_or_create(
            name='librarian',
            defaults={
                'description': 'Librarian - Manages book inventory, '
                               'approves reservations, tracks loans and fines'
            }
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created Librarian role')
            )

        manager_role, created = Role.objects.get_or_create(
            name='manager',
            defaults={
                'description': 'Library Manager - Generates reports, '
                               'manages branches and librarian accounts'
            }
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created Manager role')
            )

        # Create permissions
        permissions_data = [
            # Librarian permissions
            ('manage_books', 'Add, update, and remove books from inventory'),
            ('approve_reservations', 'Approve and manage book reservations'),
            ('track_loans', 'View and manage book loans'),
            ('manage_fines', 'View and manage user fines'),
            ('view_reports_basic', 'View basic reports'),
            
            # Manager permissions
            ('generate_reports', 'Generate comprehensive library reports'),
            ('manage_branches', 'Add and manage library branches'),
            ('manage_librarians', 'Manage librarian accounts'),
            ('view_all_data', 'Access to all library data'),
            ('manage_staff', 'Manage all staff accounts'),
        ]

        created_permissions = []
        for code, description in permissions_data:
            permission, created = Permission.objects.get_or_create(
                code=code,
                defaults={'description': description}
            )
            if created:
                created_permissions.append(permission)

        if created_permissions:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created {len(created_permissions)} permissions'
                )
            )

        # Assign permissions to roles
        librarian_permissions = [
            'manage_books', 'approve_reservations', 'track_loans',
            'manage_fines', 'view_reports_basic'
        ]
        
        manager_permissions = [
            'generate_reports', 'manage_branches', 'manage_librarians',
            'view_all_data', 'manage_staff'
        ] + librarian_permissions  # Managers have all librarian permissions

        # Assign librarian permissions
        for perm_code in librarian_permissions:
            permission = Permission.objects.get(code=perm_code)
            RolePermission.objects.get_or_create(
                role=librarian_role,
                permission=permission
            )

        # Assign manager permissions
        for perm_code in manager_permissions:
            permission = Permission.objects.get(code=perm_code)
            RolePermission.objects.get_or_create(
                role=manager_role,
                permission=permission
            )

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully setup staff roles and permissions!'
            )
        )
