"""
Circulation views for Library Management System
Handles book borrowing, returns, reservations, and fines
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.db import models
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta

from .models import BookLoan, Reservation, Fine
from library.models import Book, BookCopy


@method_decorator(login_required, name='dispatch')
class MyLoansView(TemplateView):
    """User's loan management view"""
    template_name = 'circulation/my_loans.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Current loans
        current_loans = BookLoan.objects.filter(
            user=user,
            status='borrowed'
        ).select_related('book_copy__book').order_by('-borrow_date')
        
        # Add helper methods for template
        today = timezone.now().date()
        for loan in current_loans:
            loan.is_overdue = loan.due_date < today
            loan.due_soon = (loan.due_date - today).days <= 3
            loan.days_overdue = (
                (today - loan.due_date).days if loan.is_overdue else 0
            )
            loan.days_until_due = (loan.due_date - today).days
            loan.can_extend = not loan.is_overdue  # Simplified logic
        
        context['current_loans'] = current_loans
        context['current_loans_count'] = current_loans.count()
        
        # Overdue loans
        overdue_loans = current_loans.filter(due_date__lt=today)
        context['overdue_loans'] = overdue_loans
        
        # Loan history (paginated)
        loan_history = BookLoan.objects.filter(
            user=user,
            status='returned'
        ).select_related('book_copy__book').order_by('-return_date')
        
        paginator = Paginator(loan_history, 12)
        page_number = self.request.GET.get('page')
        context['loan_history'] = paginator.get_page(page_number)
        
        # Statistics
        context['stats'] = {
            'current_loans': current_loans.count(),
            'overdue_loans': overdue_loans.count(),
            'total_loans': BookLoan.objects.filter(user=user).count(),
            'pending_fines': Fine.objects.filter(
                user=user, paid=False
            ).aggregate(total=models.Sum('amount'))['total'] or 0
        }
        
        return context


@method_decorator(login_required, name='dispatch')
class MyReservationsView(TemplateView):
    """User's reservation management view"""
    template_name = 'circulation/my_reservations.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Active reservations
        context['active_reservations'] = Reservation.objects.filter(
            user=user,
            status='active'
        ).select_related('book').order_by('queue_position')
        
        # Ready reservations (position 1 or ready status)
        context['ready_reservations'] = Reservation.objects.filter(
            user=user,
            status='ready'
        ).select_related('book')
        
        # Past reservations
        context['past_reservations'] = Reservation.objects.filter(
            user=user,
            status__in=['cancelled', 'fulfilled', 'expired']
        ).select_related('book').order_by('-reservation_date')
        
        return context


@method_decorator(login_required, name='dispatch')
class MyFinesView(TemplateView):
    """User's fine management view"""
    template_name = 'circulation/my_fines.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Unpaid fines
        unpaid_fines = Fine.objects.filter(
            user=user,
            paid=False
        ).select_related('book_loan__book_copy__book')
        context['unpaid_fines'] = unpaid_fines
        
        # Paid fines (paginated)
        paid_fines = Fine.objects.filter(
            user=user,
            paid=True
        ).select_related('book_loan__book_copy__book').order_by('-paid_date')
        
        paginator = Paginator(paid_fines, 12)
        page_number = self.request.GET.get('page')
        context['paid_fines'] = paginator.get_page(page_number)
        
        # Calculate totals
        unpaid_total = unpaid_fines.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        context['unpaid_total'] = unpaid_total
        
        paid_total = Fine.objects.filter(
            user=user,
            paid=True
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        context['paid_total'] = paid_total
        
        context['total_fines'] = unpaid_total + paid_total
        
        return context


@method_decorator(login_required, name='dispatch')
class BorrowBookView(View):
    """Borrow book view"""
    template_name = 'circulation/borrow.html'
    
    def get(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        
        # Check if user can borrow more books
        current_loans = BookLoan.objects.filter(
            user=request.user, status='borrowed'
        ).count()
        
        # Get max books from user's membership
        if request.user.membership_fee:
            max_books = request.user.membership_fee.max_books
        else:
            # Default to basic membership max books if no membership assigned
            max_books = 3
        
        if current_loans >= max_books:
            messages.error(
                request,
                f'You have reached your borrowing limit of {max_books} books.'
            )
            return redirect('library:book_detail', pk=book_id)
        
        # Check for available copies
        available_copy = BookCopy.objects.filter(
            book=book,
            condition='good'
        ).exclude(
            bookloan__status='borrowed'
        ).first()
        
        if not available_copy:
            messages.error(request, 'No copies available for borrowing.')
            return redirect('library:book_detail', pk=book_id)
        
        return render(request, self.template_name, {
            'book': book,
            'available_copy': available_copy
        })
    
    def post(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        
        # Get available copy
        available_copy = BookCopy.objects.filter(
            book=book,
            condition='good'
        ).exclude(
            bookloan__status='borrowed'
        ).first()
        
        if available_copy:
            # Create loan - get loan period from user's membership
            if request.user.membership_fee:
                loan_period = request.user.membership_fee.loan_period
            else:
                # Default to basic membership loan period if no membership assigned
                loan_period = 14
            
            due_date = timezone.now().date() + timedelta(days=loan_period)
            
            BookLoan.objects.create(
                user=request.user,
                book_copy=available_copy,
                borrow_date=timezone.now().date(),
                due_date=due_date,
                status='borrowed'
            )
            
            messages.success(
                request,
                f'Successfully borrowed "{book.title}". Due date: {due_date}.'
            )
            return redirect('circulation:my_loans')
        
        messages.error(request, 'Unable to borrow book. Please try again.')
        return redirect('library:book_detail', pk=book_id)


@method_decorator(login_required, name='dispatch')
class BorrowCopyView(View):
    """Borrow specific copy"""
    
    def post(self, request, copy_id):
        copy = get_object_or_404(BookCopy, id=copy_id)
        
        # Check if copy is available
        if not copy.is_available():
            messages.error(request, 'This copy is not available.')
            return redirect('library:book_detail', pk=copy.book.id)
        
        # Create loan - get loan period from user's membership
        if request.user.membership_fee:
            loan_period = request.user.membership_fee.loan_period
        else:
            # Default to basic membership loan period if no membership assigned
            loan_period = 14
        
        due_date = timezone.now().date() + timedelta(days=loan_period)
        
        BookLoan.objects.create(
            user=request.user,
            book_copy=copy,
            borrow_date=timezone.now().date(),
            due_date=due_date,
            status='borrowed'
        )
        
        messages.success(
            request,
            f'Successfully borrowed "{copy.book.title}".'
        )
        return redirect('circulation:my_loans')


@method_decorator(login_required, name='dispatch')
class ReserveBookView(View):
    """Reserve book view"""
    template_name = 'circulation/reserve.html'
    
    def get(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        
        # Check if user already has a reservation for this book
        existing_reservation = Reservation.objects.filter(
            user=request.user,
            book=book,
            status='active'
        ).first()
        
        if existing_reservation:
            messages.info(
                request,
                'You already have an active reservation for this book.'
            )
            return redirect('library:book_detail', pk=book_id)
        
        # Get queue position
        queue_position = Reservation.objects.filter(
            book=book,
            status='active'
        ).count() + 1
        
        return render(request, self.template_name, {
            'book': book,
            'queue_position': queue_position
        })
    
    def post(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        
        # Create reservation
        queue_position = Reservation.objects.filter(
            book=book,
            status='active'
        ).count() + 1
        
        Reservation.objects.create(
            user=request.user,
            book=book,
            reservation_date=timezone.now().date(),
            queue_position=queue_position,
            status='active'
        )
        
        messages.success(
            request,
            f'Successfully reserved "{book.title}". '
            f'You are #{queue_position} in the queue.'
        )
        return redirect('circulation:my_reservations')


@method_decorator(login_required, name='dispatch')
class ExtendLoanView(View):
    """Extend loan view"""
    
    def post(self, request, loan_id):
        loan = get_object_or_404(
            BookLoan,
            id=loan_id,
            user=request.user,
            status='borrowed'
        )
        
        # Check if loan can be extended (not overdue)
        if loan.due_date < timezone.now().date():
            messages.error(request, 'Cannot extend overdue books.')
            return redirect('circulation:my_loans')
        
        # Check if user has extension days available
        if request.user.membership_fee:
            extension_days = request.user.membership_fee.extension_days
        else:
            # Default to no extensions if no membership assigned
            extension_days = 0
        
        if extension_days > 0:
            loan.due_date += timedelta(days=extension_days)
            loan.save()
            
            messages.success(
                request,
                f'Loan extended. New due date: {loan.due_date}.'
            )
        else:
            messages.error(request, 'No extension days available.')
        
        return redirect('circulation:my_loans')


@method_decorator(login_required, name='dispatch')
class ReturnBookView(View):
    """Return book view"""
    
    def post(self, request, loan_id):
        loan = get_object_or_404(
            BookLoan,
            id=loan_id,
            user=request.user,
            status='borrowed'
        )
        
        # Process return
        return_date = timezone.now().date()
        loan.return_date = return_date
        loan.status = 'returned'
        loan.save()
        
        # Check for fines if overdue
        if return_date > loan.due_date:
            days_overdue = (return_date - loan.due_date).days
            # Calculate fine based on rules (simplified)
            fine_per_day = 2  # MVR per day
            fine_amount = days_overdue * fine_per_day
            
            Fine.objects.create(
                user=request.user,
                book_loan=loan,
                amount=fine_amount,
                fine_date=timezone.now(),
                description=f'Late return fee for {days_overdue} days',
                paid=False
            )
            
            messages.warning(
                request,
                f'Book returned. A fine of MVR {fine_amount} '
                f'has been applied for late return.'
            )
        else:
            messages.success(request, 'Book returned successfully.')
        
        return redirect('circulation:my_loans')


# Staff views
@method_decorator(login_required, name='dispatch')
class ManageLoansView(ListView):
    """Manage all loans (staff only)"""
    template_name = 'circulation/manage_loans.html'
    context_object_name = 'loans'
    paginate_by = 25
    
    def get_queryset(self):
        if not self.request.user.is_staff:
            return BookLoan.objects.none()
        
        return BookLoan.objects.filter(
            status='borrowed'
        ).select_related(
            'user', 'book_copy__book'
        ).order_by('due_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_staff:
            today = timezone.now().date()
            context['overdue_count'] = BookLoan.objects.filter(
                status='borrowed',
                due_date__lt=today
            ).count()
            
            context['total_borrowed'] = BookLoan.objects.filter(
                status='borrowed'
            ).count()
        
        return context
