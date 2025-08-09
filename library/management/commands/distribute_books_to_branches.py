from django.core.management.base import BaseCommand
from django.db import transaction
from library.models import Branch, Section, BookCopy, Book
import random


class Command(BaseCommand):
    help = ('Distribute existing book copies across branches and '
            'create additional copies')

    def handle(self, *args, **options):
        with transaction.atomic():
            # Get all branches
            branches = list(Branch.objects.all())
            if not branches:
                self.stdout.write(
                    self.style.ERROR(
                        'No branches found. Run setup_library_structure first.'
                    )
                )
                return

            self.stdout.write(f'Found {len(branches)} branches')
            
            # Get all existing book copies
            book_copies = BookCopy.objects.filter(
                branch__isnull=True,
                section__isnull=True
            )
            
            if not book_copies.exists():
                self.stdout.write(
                    self.style.WARNING(
                        'No unassigned book copies found. Creating new ones...'
                    )
                )
                # Create some book copies if none exist
                self._create_sample_book_copies()
                book_copies = BookCopy.objects.filter(
                    branch__isnull=True,
                    section__isnull=True
                )
            
            self.stdout.write(
                f'Distributing {book_copies.count()} book copies'
            )
            
            copies_assigned = 0
            for book_copy in book_copies:
                # Randomly assign to a branch
                branch = random.choice(branches)
                
                # Get sections for this branch, prefer matching book category
                sections = Section.objects.filter(branch=branch)
                if sections.exists():
                    # Try to match book category to section
                    book_category = getattr(book_copy.book, 'category', None)
                    if book_category:
                        matching_sections = sections.filter(
                            name__icontains=book_category.replace(
                                '_', ' '
                            ).title()
                        )
                        if matching_sections.exists():
                            section = matching_sections.first()
                        else:
                            # Try some common mappings
                            if 'fiction' in book_category.lower():
                                fiction_sections = sections.filter(
                                    name__icontains='Fiction'
                                )
                                section = (
                                    fiction_sections.first()
                                    if fiction_sections.exists()
                                    else sections.first()
                                )
                            elif 'children' in book_category.lower():
                                children_sections = sections.filter(
                                    name__icontains='Children'
                                )
                                section = (
                                    children_sections.first()
                                    if children_sections.exists()
                                    else sections.first()
                                )
                            elif 'research' in book_category.lower():
                                research_sections = sections.filter(
                                    name__icontains='Research'
                                )
                                section = (
                                    research_sections.first()
                                    if research_sections.exists()
                                    else sections.first()
                                )
                            else:
                                section = sections.first()
                    else:
                        section = sections.first()
                else:
                    section = None
                
                # Update the book copy
                book_copy.branch = branch
                book_copy.section = section
                book_copy.save()
                
                copies_assigned += 1
                
                if copies_assigned % 10 == 0:
                    self.stdout.write(f'Assigned {copies_assigned} copies...')
            
            # Create additional copies for popular books across branches
            self._create_additional_copies()
            
            # Summary
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Successfully assigned {copies_assigned} book copies'
                )
            )
            
            # Show distribution by branch
            self.stdout.write('\nDistribution by Branch:')
            for branch in branches:
                count = BookCopy.objects.filter(branch=branch).count()
                sections_count = Section.objects.filter(branch=branch).count()
                self.stdout.write(
                    f'  📍 {branch.name}: {count} books, '
                    f'{sections_count} sections'
                )

    def _create_sample_book_copies(self):
        """Create sample book copies if none exist"""
        books = Book.objects.all()[:20]  # Get first 20 books
        
        if not books:
            self.stdout.write(
                self.style.ERROR('No books found in the system.')
            )
            return
        
        for i, book in enumerate(books):
            # Create 1-3 copies per book
            num_copies = random.randint(1, 3)
            for j in range(num_copies):
                BookCopy.objects.create(
                    book=book,
                    barcode=f'BC{book.id:04d}{j+1:02d}',
                    purchase_price=random.uniform(100, 500),
                    condition='good'
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Created sample book copies for {len(books)} books'
            )
        )

    def _create_additional_copies(self):
        """Create additional copies for each branch"""
        branches = Branch.objects.all()
        books = Book.objects.all()[:15]  # Top 15 books
        
        copies_created = 0
        
        for branch in branches:
            sections = Section.objects.filter(branch=branch)
            
            # Create 2-3 additional copies per branch for popular books
            for book in books[:8]:  # Top 8 books get copies in each branch
                # Skip if this book already has copies in this branch
                existing_copies = BookCopy.objects.filter(
                    book=book,
                    branch=branch
                ).count()
                
                if existing_copies == 0:
                    # Choose appropriate section
                    section = self._get_appropriate_section(book, sections)
                    
                    # Create 1-2 copies
                    num_copies = random.randint(1, 2)
                    for i in range(num_copies):
                        barcode = f'BC{book.id:04d}{branch.id:02d}{i+1:02d}'
                        BookCopy.objects.create(
                            book=book,
                            branch=branch,
                            section=section,
                            barcode=barcode,
                            purchase_price=random.uniform(150, 600),
                            condition='good'
                        )
                        copies_created += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Created {copies_created} additional copies across branches'
            )
        )

    def _get_appropriate_section(self, book, sections):
        """Get the most appropriate section for a book"""
        if not sections.exists():
            return None
            
        book_category = getattr(book, 'category', '').lower()
        
        # Try to match category to section name
        if 'fiction' in book_category:
            fiction_sections = sections.filter(name__icontains='Fiction')
            if fiction_sections.exists():
                return fiction_sections.first()
        elif 'children' in book_category:
            children_sections = sections.filter(name__icontains='Children')
            if children_sections.exists():
                return children_sections.first()
        elif 'research' in book_category or 'academic' in book_category:
            research_sections = sections.filter(
                name__icontains='Research'
            ) or sections.filter(name__icontains='Academic')
            if research_sections.exists():
                return research_sections.first()
        elif 'reference' in book_category:
            ref_sections = sections.filter(name__icontains='Reference')
            if ref_sections.exists():
                return ref_sections.first()
        
        # Default to first available section
        return sections.first()
