"""
Management command to create sample data for the LMS
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
import random

from authentication.models import Role, MembershipFee
from library.models import Author, Publisher, Book, BookCopy, Branch, Section
from circulation.models import BookLoan, Reservation, Fine

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for testing the LMS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of users to create'
        )
        parser.add_argument(
            '--books',
            type=int,
            default=50,
            help='Number of books to create'
        )

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create roles
        self.create_roles()
        
        # Create membership fees
        self.create_membership_fees()
        
        # Create library data
        self.create_library_data()
        
        # Create users
        self.create_users(options['users'])
        
        # Create books
        self.create_books(options['books'])
        
        # Create some loans and reservations
        self.create_circulation_data()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )

    def create_roles(self):
        """Create user roles"""
        roles = [
            ('member', 'Library Member'),
            ('librarian', 'Librarian'),
            ('manager', 'Library Manager'),
            ('admin', 'System Administrator'),
        ]
        
        for role_name, description in roles:
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={'description': description}
            )
            if created:
                self.stdout.write(f'Created role: {role_name}')

    def create_membership_fees(self):
        """Create membership fee structures"""
        fees = [
            {
                'membership_type': 'student',
                'monthly_fee': 5.00,
                'annual_fee': 50.00,
                'max_books': 5,
                'loan_period': 14,
                'extension_days': 7,
            },
            {
                'membership_type': 'regular',
                'monthly_fee': 10.00,
                'annual_fee': 100.00,
                'max_books': 10,
                'loan_period': 21,
                'extension_days': 14,
            },
            {
                'membership_type': 'premium',
                'monthly_fee': 20.00,
                'annual_fee': 200.00,
                'max_books': 20,
                'loan_period': 30,
                'extension_days': 21,
            },
        ]
        
        for fee_data in fees:
            fee, created = MembershipFee.objects.get_or_create(
                membership_type=fee_data['membership_type'],
                defaults=fee_data
            )
            if created:
                self.stdout.write(f'Created membership fee: {fee_data["membership_type"]}')

    def create_library_data(self):
        """Create authors, publishers, subjects, branches"""
        
        # Authors
        authors_data = [
            'J.K. Rowling', 'Stephen King', 'Agatha Christie', 
            'Isaac Asimov', 'Jane Austen', 'Mark Twain',
            'Charles Dickens', 'William Shakespeare', 'George Orwell',
            'Harper Lee', 'F. Scott Fitzgerald', 'Ernest Hemingway'
        ]
        
        for name in authors_data:
            author, created = Author.objects.get_or_create(name=name)
            if created:
                self.stdout.write(f'Created author: {name}')

        # Publishers
        publishers_data = [
            'Penguin Books', 'HarperCollins', 'Simon & Schuster',
            'Macmillan', 'Oxford University Press', 'Cambridge University Press',
            'Pearson Education', 'McGraw-Hill', 'Wiley', 'Elsevier'
        ]
        
        for name in publishers_data:
            publisher, created = Publisher.objects.get_or_create(
                name=name,
                defaults={'address': f'{name} Address'}
            )
            if created:
                self.stdout.write(f'Created publisher: {name}')

        # Branch
        branch, created = Branch.objects.get_or_create(
            name='Main Library',
            defaults={'location': 'Main Street, Male 20026'}
        )
        if created:
            self.stdout.write('Created main branch')

        # Sections (instead of subjects)
        sections_data = [
            'Fiction', 'Science Fiction', 'Mystery', 'Romance', 'Biography',
            'History', 'Science', 'Technology', 'Mathematics', 'Literature',
            'Philosophy', 'Psychology', 'Education', 'Business', 'Health'
        ]
        
        for name in sections_data:
            section, created = Section.objects.get_or_create(
                name=name,
                branch=branch
            )
            if created:
                self.stdout.write(f'Created section: {name}')

    def create_users(self, count):
        """Create sample users"""
        member_role = Role.objects.get(name='member')
        librarian_role = Role.objects.get(name='librarian')
        
                # Create admin user if not exists
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@library.mv',
                password='admin123',
                first_name='System',
                last_name='Administrator',
                national_id='A001'
            )
            self.stdout.write('Created admin user (admin/admin123)')

        # Create librarian
        if not User.objects.filter(username='librarian').exists():
            librarian = User.objects.create_user(
                username='librarian',
                email='librarian@library.mv',
                password='librarian123',
                first_name='Library',
                last_name='Staff',
                is_staff=True,
                national_id='L001'
            )
            librarian.role = librarian_role
            librarian.save()
            self.stdout.write(
                'Created librarian user (librarian/librarian123)'
            )

        # Create regular users
        membership_fees = list(MembershipFee.objects.all())
        
        for i in range(count):
            username = f'user{i+1}'
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f'{username}@example.com',
                    password='password123',
                    first_name=f'User{i+1}',
                    last_name='Test',
                    national_id=f'U{i+1:03d}'
                )
                user.role = member_role
                user.membership_fee = random.choice(membership_fees)
                user.save()
                
        self.stdout.write(f'Created {count} sample users')

    def create_books(self, count):
        """Create sample books"""
        authors = list(Author.objects.all())
        publishers = list(Publisher.objects.all())
        sections = list(Section.objects.all())
        
        book_titles = [
            'The Art of Programming', 'Database Design Fundamentals',
            'Web Development Guide', 'Mobile App Development',
            'Artificial Intelligence Basics', 'Data Science Handbook',
            'Cloud Computing Essentials', 'Cybersecurity Principles',
            'Software Engineering Best Practices', 'Computer Networks',
            'Operating Systems Concepts', 'Algorithm Design Manual',
            'Python Programming', 'JavaScript Complete Guide',
            'Machine Learning Introduction', 'Digital Marketing Strategies',
            'Project Management', 'Business Analysis', 'Leadership Skills',
            'Communication Excellence', 'Creative Writing',
            'Photography Basics',
            'Graphic Design Principles', 'Music Theory', 'Art History',
            'World History', 'Science Discoveries', 'Mathematics',
            'Physics Made Simple', 'Chemistry Fundamentals', 'Biology'
        ]
        
        for i in range(min(count, len(book_titles))):
            title = book_titles[i]
            if not Book.objects.filter(title=title).exists():
                # Generate a random but valid ISBN
                isbn = f'978{random.randint(1000000000, 9999999999)}'
                
                book = Book.objects.create(
                    title=title,
                    isbn=isbn,
                    category=random.choice(['fiction', 'non-fiction', 'academic']),
                    edition='1st Edition',
                    publication_year=random.randint(2000, 2024),
                    language='english',
                    publisher=random.choice(publishers),
                    section=random.choice(sections)
                )
                
                # Add author through BookAuthor relationship
                from library.models import BookAuthor
                BookAuthor.objects.create(
                    book=book,
                    author=random.choice(authors)
                )
                
                # Create book copies
                num_copies = random.randint(2, 5)
                for j in range(num_copies):
                    barcode = f"{book.isbn}-{j+1:03d}"  # Generate unique barcode
                    purchase_price = random.uniform(15.0, 150.0)  # Random price
                    BookCopy.objects.create(
                        book=book,
                        barcode=barcode,
                        purchase_price=purchase_price,
                        condition='good'
                    )
                
        self.stdout.write(f'Created {count} books with copies')

    def create_circulation_data(self):
        """Create some loans, reservations, and fines for testing"""
        # Get regular users (not superusers/staff)
        users = list(User.objects.filter(is_staff=False, is_superuser=False))
        book_copies = list(BookCopy.objects.all())
        
        if not users or not book_copies:
            self.stdout.write('No users or books available for circulation data')
            return
        
        # Create some current loans
        for i in range(min(10, len(users), len(book_copies))):
            user = users[i]
            book_copy = book_copies[i]
            
            # Check if this book copy is already loaned
            if not BookLoan.objects.filter(
                book_copy=book_copy,
                status='borrowed'
            ).exists():
                borrowed_date = timezone.now().date() - timedelta(days=random.randint(1, 20))
                due_date = borrowed_date + timedelta(days=14)
                
                loan = BookLoan.objects.create(
                    user=user,
                    book_copy=book_copy,
                    borrowed_date=borrowed_date,
                    due_date=due_date,
                    status='borrowed'
                )
                
                # Create some overdue loans with fines
                if random.random() < 0.3 and due_date < timezone.now().date():
                    days_overdue = (timezone.now().date() - due_date).days
                    fine_amount = days_overdue * 2  # 2 MVR per day
                    
                    Fine.objects.create(
                        user=user,
                        book_loan=loan,
                        amount=fine_amount,
                        fine_date=timezone.now().date(),
                        description=f'Late return fee for {days_overdue} days',
                        status='pending'
                    )
        
        # Create some reservations
        available_books = Book.objects.exclude(
            bookcopy__bookloan__status='borrowed'
        )[:5]
        
        for i, book in enumerate(available_books):
            if i < len(users):
                Reservation.objects.create(
                    user=users[i],
                    book=book,
                    reserved_date=timezone.now().date(),
                    queue_position=1,
                    status='active'
                )
        
        self.stdout.write('Created circulation data (loans, reservations, fines)')
