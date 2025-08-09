from django.core.management.base import BaseCommand
from django.db import transaction
from library.models import Book, Author, Publisher, Section, Branch, BookCopy
import random


class Command(BaseCommand):
    help = 'Create sample books across different categories for all branches'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Sample books data
            sample_books = [
                {
                    'title': 'Dhivehi Raajjeuge Thaareekh',
                    'category': 'non-fiction',
                    'language': 'dhivehi',
                    'edition': '3rd Edition',
                    'publication_year': 2020,
                    'authors': ['Hassan Ahmed Maniku'],
                    'publisher': 'National Centre for Linguistic Studies'
                },
                {
                    'title': 'The Maldive Islands: A Physical Geography',
                    'category': 'research',
                    'language': 'english',
                    'edition': '1st Edition',
                    'publication_year': 2019,
                    'authors': ['Dr. Ibrahim Waheed'],
                    'publisher': 'Maldivian Heritage Foundation'
                },
                {
                    'title': 'Laal Gandu - Children Stories',
                    'category': 'children',
                    'language': 'dhivehi',
                    'edition': '2nd Edition',
                    'publication_year': 2021,
                    'authors': ['Aminath Shathira'],
                    'publisher': 'Novelty Printers & Publishers'
                },
                {
                    'title': 'Islamic Banking in the Maldives',
                    'category': 'academic',
                    'language': 'english',
                    'edition': '1st Edition',
                    'publication_year': 2022,
                    'authors': ['Dr. Mohamed Waheed'],
                    'publisher': 'Maldives Islamic University Press'
                },
                {
                    'title': 'Coral Reef Conservation Manual',
                    'category': 'reference',
                    'language': 'english',
                    'edition': '4th Edition',
                    'publication_year': 2023,
                    'authors': ['Marine Research Centre'],
                    'publisher': 'Ministry of Environment Publications'
                },
                {
                    'title': 'Dhivehi Bahuge Qawaaaidhu',
                    'category': 'academic',
                    'language': 'dhivehi',
                    'edition': '5th Edition',
                    'publication_year': 2020,
                    'authors': ['Mohamed Waheed Deen'],
                    'publisher': 'Dhivehi Language Academy'
                },
                {
                    'title': 'Tourism Development in Small Island States',
                    'category': 'research',
                    'language': 'english',
                    'edition': '1st Edition',
                    'publication_year': 2021,
                    'authors': ['Dr. Aishath Ali', 'Prof. Ahmed Hassan'],
                    'publisher': 'Maldivian University Press'
                },
                {
                    'title': 'Maldivian Folk Tales for Children',
                    'category': 'children',
                    'language': 'english',
                    'edition': '3rd Edition',
                    'publication_year': 2022,
                    'authors': ['Mariyam Shakeela'],
                    'publisher': 'Cultural Heritage Publications'
                },
                {
                    'title': 'Sustainable Fisheries Management',
                    'category': 'academic',
                    'language': 'english',
                    'edition': '2nd Edition',
                    'publication_year': 2023,
                    'authors': ['Ministry of Fisheries'],
                    'publisher': 'Government Publications'
                },
                {
                    'title': 'Dhivehi Literature Through the Ages',
                    'category': 'non-fiction',
                    'language': 'dhivehi',
                    'edition': '1st Edition',
                    'publication_year': 2021,
                    'authors': ['Ibrahim Shihab', 'Hassan Saeed'],
                    'publisher': 'National Library of Maldives'
                }
            ]

            created_books = 0
            created_copies = 0

            for book_data in sample_books:
                # Check if book already exists
                if Book.objects.filter(title=book_data['title']).exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f'Book "{book_data["title"]}" already exists'
                        )
                    )
                    continue

                # Create or get publisher
                publisher, created = Publisher.objects.get_or_create(
                    name=book_data['publisher'],
                    defaults={'address': 'Maldives'}
                )

                # Generate ISBN
                isbn_part1 = random.randint(1000, 9999)
                isbn_part2 = random.randint(10, 99)
                isbn = f'978999{isbn_part1}{isbn_part2}'

                # Get appropriate section (we'll use the first available one)
                section = Section.objects.first()

                # Create book
                book = Book.objects.create(
                    title=book_data['title'],
                    isbn=isbn,
                    category=book_data['category'],
                    language=book_data['language'],
                    edition=book_data['edition'],
                    publication_year=book_data['publication_year'],
                    publisher=publisher,
                    section=section
                )

                # Create authors and link them
                for author_name in book_data['authors']:
                    author, created = Author.objects.get_or_create(
                        name=author_name
                    )
                    book.authors.add(author)

                created_books += 1
                
                # Create copies in each branch
                branches = Branch.objects.all()
                for branch in branches:
                    # Get appropriate section for this branch
                    branch_sections = Section.objects.filter(branch=branch)
                    
                    # Try to find appropriate section based on category
                    appropriate_section = self._get_section_for_category(
                        book_data['category'],
                        branch_sections
                    )
                    
                    if not appropriate_section:
                        appropriate_section = branch_sections.first()

                    # Create 1-2 copies per branch
                    num_copies = random.randint(1, 2)
                    for i in range(num_copies):
                        barcode = f'BC{book.id:04d}{branch.id:02d}{i+1:02d}'
                        
                        BookCopy.objects.create(
                            book=book,
                            branch=branch,
                            section=appropriate_section,
                            barcode=barcode,
                            purchase_price=random.uniform(200, 800),
                            condition='good'
                        )
                        created_copies += 1

                self.stdout.write(
                    f'Created: "{book.title}" with {num_copies} copies '
                    f'per branch'
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Created {created_books} new books with '
                    f'{created_copies} total copies'
                )
            )

    def _get_section_for_category(self, category, sections):
        """Get the most appropriate section for a book category"""
        category_mapping = {
            'fiction': ['Fiction'],
            'non-fiction': ['Non-Fiction'],
            'children': ['Children', 'Children\'s Books'],
            'research': ['Research', 'Academic'],
            'academic': ['Academic', 'Research'],
            'reference': ['Reference'],
        }
        
        if category in category_mapping:
            for section_name in category_mapping[category]:
                matching_section = sections.filter(
                    name__icontains=section_name
                ).first()
                if matching_section:
                    return matching_section
        
        return sections.first()
