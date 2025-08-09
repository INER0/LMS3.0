from django.core.management.base import BaseCommand
from library.models import Branch, Section


class Command(BaseCommand):
    help = 'Create initial library branches and sections'

    def handle(self, *args, **options):
        # Create branches for Maldives locations
        branches_data = [
            {
                'name': 'Male\' Central Library',
                'location': 'Male\', Maldives',
                'sections': [
                    'Fiction',
                    'Non-Fiction',
                    'Research',
                    'Children\'s Books',
                    'Academic',
                    'Reference',
                    'Local History',
                    'Digital Media'
                ]
            },
            {
                'name': 'Kulhudhufushi Public Library',
                'location': 'Kulhudhufushi, Haa Dhaalu Atoll',
                'sections': [
                    'Fiction',
                    'Non-Fiction',
                    'Children\'s Books',
                    'Educational',
                    'Islamic Studies',
                    'Reference'
                ]
            },
            {
                'name': 'Addu City Library',
                'location': 'Hithadhoo, Addu City',
                'sections': [
                    'Fiction',
                    'Non-Fiction',
                    'Research',
                    'Children\'s Books',
                    'Academic',
                    'Tourism & Culture',
                    'Reference'
                ]
            }
        ]
        
        created_branches = 0
        created_sections = 0
        
        for branch_data in branches_data:
            # Create or get branch
            branch, created = Branch.objects.get_or_create(
                name=branch_data['name'],
                defaults={'location': branch_data['location']}
            )
            
            if created:
                created_branches += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created branch: {branch.name}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Branch already exists: {branch.name}'
                    )
                )
            
            # Create sections for this branch
            for section_name in branch_data['sections']:
                section, created = Section.objects.get_or_create(
                    name=section_name,
                    branch=branch
                )
                
                if created:
                    created_sections += 1
                    self.stdout.write(
                        f'  + Created section: {section_name}'
                    )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                '\nSummary:'
            )
        )
        self.stdout.write(f'Branches created: {created_branches}')
        self.stdout.write(f'Sections created: {created_sections}')
        
        # Show current structure
        self.stdout.write('\nCurrent Library Structure:')
        for branch in Branch.objects.all():
            self.stdout.write(f'\n📍 {branch.name} ({branch.location})')
            sections = Section.objects.filter(branch=branch)
            for section in sections:
                self.stdout.write(f'   📚 {section.name}')
                
        self.stdout.write(
            self.style.SUCCESS(
                '\n✅ Library structure setup complete!'
            )
        )
