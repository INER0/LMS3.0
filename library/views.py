"""
Library views for Library Management System
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, UpdateView
)
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta

from .models import Book, Author, Publisher, Branch, Section, BookCopy
from circulation.models import BookLoan, Reservation, Fine
from authentication.models import User


class DashboardView(TemplateView):
    """Main dashboard view"""
    template_name = 'library/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistics for all users
        context['stats'] = {
            'total_books': Book.objects.count(),
            'borrowed_books': BookLoan.objects.filter(status='borrowed').count(),
            'reservations': Reservation.objects.filter(status='active').count(),
            'pending_fines': Fine.objects.filter(paid=False).count(),
        }
        
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
        
        # Popular books
        context['popular_books'] = Book.objects.annotate(
            loan_count=Count('bookcopy__bookloan')
        ).order_by('-loan_count')[:8]
        
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
        
        # Available copies
        context['copies'] = BookCopy.objects.filter(book=book)
        
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
