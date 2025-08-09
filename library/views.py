"""
Library views for Library Management System
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from django.urls import reverse_lazy
from django.http import JsonResponse
from datetime import timedelta

from .models import Book, Author, Publisher, Branch, Section, BookCopy
from circulation.models import BookLoan, Reservation, Fine
from authentication.models import User


class DashboardView(TemplateView):
    """Main dashboard view"""
    template_name = 'library/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get active branch from session
        active_branch_id = self.request.session.get('active_branch_id')
        branches = Branch.objects.all()
        active_branch = None
        
        if active_branch_id:
            try:
                active_branch = Branch.objects.get(id=active_branch_id)
            except Branch.DoesNotExist:
                pass
        
        if not active_branch and branches.exists():
            active_branch = branches.first()
            self.request.session['active_branch_id'] = active_branch.id
            self.request.session['active_branch_name'] = active_branch.name
        
        # Statistics for the active branch or all if no branch selected
        if active_branch:
            total_books = BookCopy.objects.filter(branch=active_branch).count()
            borrowed_books = BookLoan.objects.filter(
                book_copy__branch=active_branch,
                status='borrowed'
            ).count()
        else:
            total_books = Book.objects.count()
            borrowed_books = BookLoan.objects.filter(status='borrowed').count()
        
        # Statistics for all users
        context['stats'] = {
            'total_books': total_books,
            'borrowed_books': borrowed_books,
            'reservations': Reservation.objects.filter(
                status='active'
            ).count(),
            'pending_fines': Fine.objects.filter(paid=False).count(),
        }
        
        # Branch context
        context['branches'] = branches
        context['active_branch'] = active_branch
        
        # User-specific data if logged in
        if self.request.user.is_authenticated:
            user = self.request.user
            
            # Recent loans
            context['recent_loans'] = BookLoan.objects.filter(
                user=user
            ).order_by('-borrow_date')[:5]
            
            # Active reservations
            context['reservations'] = Reservation.objects.filter(
                user=user,
                status='active'
            ).order_by('-reservation_date')[:5]
            
            # Overdue books
            overdue_loans = BookLoan.objects.filter(
                user=user,
                status='borrowed',
                due_date__lt=timezone.now().date()
            )
            context['overdue_books'] = overdue_loans
            
            # Update pending fines for user
            context['stats']['pending_fines'] = Fine.objects.filter(
                user=user,
                paid=False
            ).aggregate(total=Count('amount'))['total'] or 0
        
        # Popular books (branch-specific if active branch selected)
        popular_books = Book.objects.annotate(
            loan_count=Count('bookcopy__bookloan')
        )
        if active_branch:
            popular_books = popular_books.filter(
                bookcopy__branch=active_branch
            )
        context['popular_books'] = popular_books.order_by('-loan_count')[:8]
        
        context['today'] = timezone.now()
        
        return context


class BookSearchView(TemplateView):
    """Book search and listing"""
    template_name = 'library/book_search.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get search parameters
        query = self.request.GET.get('q', '')
        category = self.request.GET.get('category', '')
        language = self.request.GET.get('language', '')
        branch_id = self.request.GET.get('branch', '')
        availability = self.request.GET.get('availability', '')
        sort_by = self.request.GET.get('sort_by', 'title')
        per_page = int(self.request.GET.get('per_page', 12))
        
        # Build queryset
        books = Book.objects.all()
        
        # Apply filters
        if query:
            books = books.filter(
                Q(title__icontains=query) |
                Q(authors__name__icontains=query) |
                Q(isbn__icontains=query) |
                Q(publisher__name__icontains=query)
            ).distinct()
        
        if category:
            books = books.filter(category=category)
            
        if language:
            books = books.filter(language=language)
            
        if branch_id:
            books = books.filter(section__branch_id=branch_id)
            
        if availability == 'available':
            books = books.filter(bookcopy__condition='good').exclude(
                bookcopy__bookloan__status='borrowed'
            ).distinct()
        elif availability == 'borrowed':
            books = books.filter(
                bookcopy__bookloan__status='borrowed'
            ).distinct()
        
        # Apply sorting
        if sort_by:
            books = books.order_by(sort_by)
        
        # Pagination
        paginator = Paginator(books, per_page)
        page = self.request.GET.get('page')
        books = paginator.get_page(page)
        
        # Context data
        context['books'] = books
        context['query'] = query
        context['total_books'] = Book.objects.count()
        context['categories'] = Book.CATEGORY_CHOICES
        context['languages'] = Book.LANGUAGE_CHOICES
        context['branches'] = Branch.objects.all()
        
        return context


class BookDetailView(DetailView):
    """Book detail page"""
    model = Book
    template_name = 'library/book_detail.html'
    context_object_name = 'book'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.object
        
        # Get all copies for this book
        all_copies = BookCopy.objects.filter(book=book).select_related(
            'branch', 'section'
        )
        context['copies'] = all_copies
        
        # Group copies by branch with detailed information
        copies_by_branch = {}
        for copy in all_copies:
            branch = copy.branch
            if branch not in copies_by_branch:
                copies_by_branch[branch] = {
                    'branch': branch,
                    'copies': [],
                    'available_count': 0,
                    'total_count': 0
                }
            
            # Get current loan information
            current_loan = None
            borrowed_by = None
            if not copy.is_available():
                current_loan = BookLoan.objects.filter(
                    book_copy=copy,
                    status='borrowed'
                ).select_related('user').first()
                if current_loan:
                    borrowed_by = current_loan.user
            
            copy_info = {
                'copy': copy,
                'current_loan': current_loan,
                'borrowed_by': borrowed_by,
                'is_available': copy.is_available()
            }
            
            copies_by_branch[branch]['copies'].append(copy_info)
            copies_by_branch[branch]['total_count'] += 1
            if copy.is_available() and copy.condition == 'good':
                copies_by_branch[branch]['available_count'] += 1
        
        context['copies_by_branch'] = copies_by_branch
        
        # Similar books
        context['similar_books'] = Book.objects.filter(
            category=book.category
        ).exclude(id=book.id)[:4]
        
        # Borrowing statistics
        context['borrowed_count'] = BookLoan.objects.filter(
            book_copy__book=book,
            status='borrowed'
        ).count()
        
        return context


@method_decorator(login_required, name='dispatch')
class ManageBooksView(ListView):
    """Book management for staff"""
    model = Book
    template_name = 'library/manage_books.html'
    context_object_name = 'books'
    paginate_by = 20
    
    def get_queryset(self):
        if not self.request.user.is_staff:
            messages.error(self.request, 'Access denied.')
            return Book.objects.none()
        
        queryset = Book.objects.all().order_by('title')
        
        # Search functionality for staff
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(isbn__icontains=search) |
                Q(authors__name__icontains=search)
            ).distinct()
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistics for management
        context['stats'] = {
            'total_books': Book.objects.count(),
            'total_copies': BookCopy.objects.count(),
            'available_copies': BookCopy.objects.filter(condition='good').count(),
            'damaged_copies': BookCopy.objects.filter(condition='damaged').count(),
            'lost_copies': BookCopy.objects.filter(condition='lost').count(),
        }
        
        return context


class BorrowingRulesView(TemplateView):
    """Display borrowing rules and policies"""
    template_name = 'library/borrowing_rules.html'


@method_decorator(login_required, name='dispatch')
class AddBookView(CreateView):
    """Add a new book"""
    model = Book
    template_name = 'library/add_book.html'
    fields = [
        'isbn', 'title', 'category', 'edition', 'publication_year',
        'language', 'publisher', 'section', 'authors'
    ]
    success_url = reverse_lazy('library:manage_books')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Access denied.')
            return redirect('library:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, 'Book added successfully!')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class EditBookView(UpdateView):
    """Edit an existing book"""
    model = Book
    template_name = 'library/edit_book.html'
    fields = [
        'isbn', 'title', 'category', 'edition', 'publication_year',
        'language', 'publisher', 'section', 'authors'
    ]
    success_url = reverse_lazy('library:manage_books')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Access denied.')
            return redirect('library:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, 'Book updated successfully!')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class DeleteBookView(DeleteView):
    """Delete a book"""
    model = Book
    template_name = 'library/delete_book.html'
    success_url = reverse_lazy('library:manage_books')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Access denied.')
            return redirect('library:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Book deleted successfully!')
        return super().delete(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class AddBookCopyView(CreateView):
    """Add a copy of an existing book"""
    model = BookCopy
    template_name = 'library/add_book_copy.html'
    fields = ['branch', 'section', 'barcode', 'purchase_price', 'condition']
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Access denied.')
            return redirect('library:dashboard')
        self.book = get_object_or_404(Book, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['book'] = self.book
        # Get available and borrowed copy counts
        all_copies = BookCopy.objects.filter(book=self.book)
        context['total_copies'] = all_copies.count()
        available_count = sum(1 for copy in all_copies if copy.is_available())
        context['available_copies'] = available_count
        return context
    
    def form_valid(self, form):
        form.instance.book = self.book
        messages.success(self.request, 'Book copy added successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('library:manage_book_copies',
                            kwargs={'pk': self.book.pk})


@method_decorator(login_required, name='dispatch')
class ManageBookCopiesView(ListView):
    """Manage copies of a specific book"""
    model = BookCopy
    template_name = 'library/manage_book_copies.html'
    context_object_name = 'book_copies'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Access denied.')
            return redirect('library:dashboard')
        self.book = get_object_or_404(Book, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return BookCopy.objects.filter(book=self.book).select_related(
            'branch', 'section'
        ).order_by('-last_seen')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['book'] = self.book
        
        # Get all copies for statistics
        all_copies = self.get_queryset()
        context['total_copies'] = all_copies.count()
        context['available_copies'] = sum(
            1 for copy in all_copies if copy.is_available()
        )
        context['borrowed_copies'] = sum(
            1 for copy in all_copies if not copy.is_available()
            and copy.condition == 'good'
        )
        context['other_copies'] = sum(
            1 for copy in all_copies if copy.condition != 'good'
        )
        
        # Get all branches for filtering
        context['branches'] = Branch.objects.all()
        
        return context


@method_decorator(login_required, name='dispatch')
class EditBookCopyView(UpdateView):
    """Edit an existing book copy"""
    model = BookCopy
    template_name = 'library/edit_book_copy.html'
    fields = ['branch', 'section', 'barcode', 'purchase_price', 'condition']
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Access denied.')
            return redirect('library:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['book'] = self.object.book
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Book copy updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('library:manage_book_copies',
                            kwargs={'pk': self.object.book.pk})


@method_decorator(login_required, name='dispatch')
class DeleteBookCopyView(DeleteView):
    """Delete a book copy"""
    model = BookCopy
    template_name = 'library/delete_book_copy.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Access denied.')
            return redirect('library:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['book'] = self.object.book
        return context
    
    def delete(self, request, *args, **kwargs):
        book = self.get_object().book
        messages.success(request, 'Book copy deleted successfully!')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('library:manage_book_copies',
                            kwargs={'pk': self.object.book.pk})


@method_decorator(login_required, name='dispatch')
class BranchManagementView(ListView):
    """Branch and section management"""
    model = Branch
    template_name = 'library/branch_management.html'
    context_object_name = 'branches'
    
    def dispatch(self, request, *args, **kwargs):
        user_roles = ['manager', 'admin']
        if not request.user.is_staff and request.user.role not in user_roles:
            messages.error(request, 'Access denied.')
            return redirect('library:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Branch.objects.prefetch_related('section_set').annotate(
            total_books=Count('bookcopy'),
            total_sections=Count('section_set')
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Branch statistics
        context['stats'] = {
            'total_branches': Branch.objects.count(),
            'total_sections': Section.objects.count(),
            'total_books': BookCopy.objects.count(),
            'branches_with_books': Branch.objects.annotate(
                book_count=Count('bookcopy')
            ).filter(book_count__gt=0).count()
        }
        
        return context


def set_active_branch(request, branch_id):
    """Set the active branch for the session"""
    if not request.user.is_authenticated:
        return redirect('authentication:login')
    
    try:
        branch = Branch.objects.get(id=branch_id)
        request.session['active_branch_id'] = branch_id
        request.session['active_branch_name'] = branch.name
        messages.success(request, f'Switched to {branch.name}')
    except Branch.DoesNotExist:
        messages.error(request, 'Branch not found')
    
    return redirect(request.META.get('HTTP_REFERER', 'library:dashboard'))


def get_sections_for_branch(request):
    """AJAX endpoint to get sections for a branch"""
    branch_id = request.GET.get('branch_id')
    if branch_id:
        sections = Section.objects.filter(branch_id=branch_id).values(
            'id', 'name'
        )
        return JsonResponse({'sections': list(sections)})
    return JsonResponse({'sections': []})


@method_decorator(login_required, name='dispatch')
class BranchDetailView(DetailView):
    """Branch detail view with statistics"""
    model = Branch
    template_name = 'library/branch_detail.html'
    context_object_name = 'branch'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        branch = self.object
        
        # Branch statistics
        context['stats'] = {
            'total_books': BookCopy.objects.filter(branch=branch).count(),
            'available_books': BookCopy.objects.filter(
                branch=branch,
                condition='good'
            ).count(),
            'borrowed_books': BookLoan.objects.filter(
                book_copy__branch=branch,
                status='borrowed'
            ).count(),
            'total_sections': Section.objects.filter(branch=branch).count()
        }
        
        # Sections with book counts
        context['sections'] = Section.objects.filter(branch=branch).annotate(
            book_count=Count('bookcopy')
        )
        
        # Recent activity
        context['recent_loans'] = BookLoan.objects.filter(
            book_copy__branch=branch
        ).order_by('-borrow_date')[:5]
        
        return context
