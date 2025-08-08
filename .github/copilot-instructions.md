# Copilot Instructions for Library Management System

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

## Project Overview
This is a Django-based Library Management System (LMS) for academic coursework. The project implements:

- **Multi-branch library operations** with comprehensive book management
- **Role-based access control** (Members, Librarians, Managers, Admin)
- **Secure authentication** with MFA support and audit logging
- **Circulation system** with borrowing, reservations, and fine management
- **Payment processing** for memberships, fines, and digital services
- **Advanced security features** including session management and password policies

## Code Style Guidelines
- Follow Django best practices and PEP 8 style guidelines
- Use descriptive variable and function names
- Implement comprehensive error handling and validation
- Add docstrings to all classes and methods
- Use Django's built-in security features
- Implement proper database relationships and constraints
- Write comprehensive unit tests for all functionality

## Security Requirements
- Implement role-based access control (RBAC)
- Use secure password hashing and validation
- Implement session management with timeout
- Add audit logging for critical operations
- Validate all user inputs
- Use Django's CSRF protection
- Implement proper authentication and authorization

## Database Design
- Follow the provided database schema exactly
- Use Django ORM for all database operations
- Implement proper foreign key relationships
- Add database constraints and validations
- Use migrations for schema changes
