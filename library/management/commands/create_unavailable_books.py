"""
Management command to create unavailable books for testing reservations.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from datetime import timedelta
from circulation.models import BookLoan
from library.models import Book

User = get_user_model()


class Command(BaseCommand):
    help = ('Create unavailable books (all copies borrowed) '
            'for testing reservations')

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help='Number of books to make unavailable (default: 3)'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        try:
            # Get some users to borrow books
            users = User.objects.filter(is_active=True)[:5]
            if len(users) < 2:
                self.stdout.write(
                    self.style.ERROR(
                        'Need at least 2 active users in the system'
                    )
                )
                return

            # Find books with multiple copies that we can make unavailable
            books_with_multiple_copies = Book.objects.annotate(
                copy_count=models.Count('bookcopy')
            ).filter(copy_count__gte=2)[:count]

            if len(books_with_multiple_copies) < count:
                self.stdout.write(
                    self.style.WARNING(
                        f'Only found {len(books_with_multiple_copies)} books '
                        f'with multiple copies, need {count}'
                    )
                )

            created_loans = 0
            unavailable_books = []

            for book in books_with_multiple_copies:
                copies = book.bookcopy_set.all()
                user_idx = 0
                
                # Borrow all copies of this book to different users
                for copy in copies:
                    # Check if already borrowed
                    if not copy.is_available:
                        continue
                        
                    user = users[user_idx % len(users)]
                    
                    # Create loan with due date in the future
                    loan_date = timezone.now().date() - timedelta(days=3)
                    due_date = loan_date + timedelta(days=14)
                    
                    BookLoan.objects.create(
                        user=user,
                        book_copy=copy,
                        borrow_date=loan_date,
                        due_date=due_date,
                        status='borrowed'
                    )
                    
                    created_loans += 1
                    user_idx += 1
                    
                    self.stdout.write(
                        f'  - Borrowed {copy.barcode} to {user.username}'
                    )
                
                # Check if all copies are now borrowed
                available_count = sum(1 for c in copies if c.is_available)
                if available_count == 0:
                    unavailable_books.append(book)
                    self.stdout.write(
                        f'✓ {book.title} is now fully unavailable '
                        f'({copies.count()} copies all borrowed)'
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {created_loans} loans making '
                    f'{len(unavailable_books)} books unavailable '
                    'for reservation'
                )
            )
            
            self.stdout.write(
                '\n📚 Books now available for reservation testing:'
            )
            for book in unavailable_books:
                author_name = (
                    book.authors.first().name if book.authors.first()
                    else 'Unknown Author'
                )
                self.stdout.write(f'  - {book.title} by {author_name}')
                copy_count = book.bookcopy_set.count()
                self.stdout.write(f'    All {copy_count} copies borrowed')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating unavailable books: {str(e)}')
            )
