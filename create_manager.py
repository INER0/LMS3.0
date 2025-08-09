#!/usr/bin/env python
"""
Script to create a manager user for the Library Management System
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_management.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from authentication.models import User, Role, UserRole

def create_manager_user():
    """Create a manager user with proper role assignment"""
    try:
        # Get or create the Manager role
        manager_role, created = Role.objects.get_or_create(
            name='Manager',
            defaults={
                'description': 'Library manager with full access to staff functions'
            }
        )
        
        # Create the manager user
        manager_user, user_created = User.objects.get_or_create(
            username='manager',
            defaults={
                'email': 'manager@lms.com',
                'first_name': 'Library',
                'last_name': 'Manager',
                'is_staff': True,
                'is_active': True,
                'password': make_password('manager123'),
                'national_id': 'MGR001'  # Add unique national_id
            }
        )
        
        if user_created:
            print("✓ Manager user created successfully!")
        else:
            print("! Manager user already exists - updating password...")
            manager_user.set_password('manager123')
            manager_user.save()
        
        # Assign Manager role to user
        user_role, role_created = UserRole.objects.get_or_create(
            user=manager_user,
            role=manager_role
        )
        
        if role_created:
            print("✓ Manager role assigned successfully!")
        else:
            print("! Manager already has the Manager role")
        
        print("\n" + "="*50)
        print("MANAGER LOGIN CREDENTIALS")
        print("="*50)
        print(f"Username: {manager_user.username}")
        print(f"Password: manager123")
        print(f"Email: {manager_user.email}")
        print(f"Role: {manager_role.name}")
        print(f"Full Name: {manager_user.get_full_name()}")
        print("="*50)
        print("\nYou can now log in to the system using these credentials.")
        print("The manager has access to:")
        print("- Staff Dashboard")
        print("- Book Management (Add/Edit/Delete)")
        print("- Loan Management (View/Return/Renew)")
        print("- Fine Management (View/Process Payments)")
        print("- Reports and Analytics")
        print("- Member Management")
        
    except Exception as e:
        print(f"Error creating manager user: {e}")
        return False
        
    return True

if __name__ == "__main__":
    print("Creating Library Manager Account...")
    print("-" * 40)
    
    success = create_manager_user()
    
    if success:
        print("\n✓ Manager account setup complete!")
    else:
        print("\n✗ Failed to create manager account!")
        sys.exit(1)
