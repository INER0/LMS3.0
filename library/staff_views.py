"""
Staff management views for librarians and managers
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.db.models import Q, Count, Sum
from django.http import JsonResponse, HttpResponse
from datetime import datetime, timedelta
from decimal import Decimal
import csv

from authentication.utils import staff_required, manager_required
from authentication.models import User
from library.models import Book, BookCopy, Branch
from circulation.models import BookLoan, Reservation, Fine
from payments.models import Payment


@staff_required
def staff_dashboard(request):
    """Staff dashboard with quick actions and stats"""
    context = {
        'total_books': Book.objects.count(),
        'total_copies': BookCopy.objects.count(),
        'active_loans': BookLoan.objects.filter(status='borrowed').count(),
        'pending_reservations': Reservation.objects.filter(
            status='active'
        ).count(),
        'overdue_loans': BookLoan.objects.filter(
            status='borrowed',
            due_date__lt=datetime.now().date()
        ).count(),
        'unpaid_fines': Fine.objects.filter(paid=False).count(),
    }
    return render(request, 'library/staff_dashboard.html', context)


@method_decorator(staff_required, name='dispatch')
class BookManagementView(ListView):
    """Enhanced book management for staff"""
    model = Book
    template_name = 'library/staff_book_management.html'
    context_object_name = 'books'
    paginate_by = 20

    def get_queryset(self):
        queryset = Book.objects.select_related('publisher').prefetch_related(
            'authors', 'bookcopy_set'
        ).annotate(
            total_copies=Count('bookcopy'),
            available_copies=Count(
                'bookcopy',
                filter=Q(bookcopy__condition='good') &
                       ~Q(bookcopy__in=BookLoan.objects.filter(
                           status='borrowed'
                       ).values('book_copy'))
            )
        ).order_by('title')

        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(isbn__icontains=search) |
                Q(authors__name__icontains=search)
            ).distinct()

        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Filter by availability
        availability = self.request.GET.get('availability')
        if availability == 'available':
            queryset = queryset.filter(available_copies__gt=0)
        elif availability == 'unavailable':
            queryset = queryset.filter(available_copies=0)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Book.CATEGORY_CHOICES
        context['branches'] = Branch.objects.all()
        return context


@staff_required
def approve_reservations(request):
    """View and approve pending reservations"""
    reservations = Reservation.objects.filter(
        status='active'
    ).select_related('user', 'book').order_by('reservation_date')

    if request.method == 'POST':
        reservation_id = request.POST.get('reservation_id')
        action = request.POST.get('action')

        reservation = get_object_or_404(Reservation, id=reservation_id)

        if action == 'approve':
            # Check if book is available
            available_copy = BookCopy.objects.filter(
                book=reservation.book,
                condition='good'
            ).exclude(
                id__in=BookLoan.objects.filter(
                    status='borrowed'
                ).values('book_copy_id')
            ).first()

            if available_copy:
                # Create loan
                loan_period = 14  # Default loan period
                if reservation.user.membership_fee:
                    loan_period = reservation.user.membership_fee.loan_period

                BookLoan.objects.create(
                    user=reservation.user,
                    book_copy=available_copy,
                    borrow_date=datetime.now().date(),
                    due_date=datetime.now().date() + timedelta(
                        days=loan_period
                    ),
                    status='borrowed'
                )

                # Update reservation status
                reservation.status = 'fulfilled'
                reservation.save()

                messages.success(
                    request,
                    f'Reservation approved for {reservation.user.username}'
                )
            else:
                messages.error(
                    request,
                    'No available copies for this book'
                )

        elif action == 'reject':
            reservation.status = 'rejected'
            reservation.save()
            messages.success(
                request,
                f'Reservation rejected for {reservation.user.username}'
            )

        return redirect('library:approve_reservations')

    context = {
        'reservations': reservations,
        'pending_count': reservations.count()
    }
    return render(request, 'library/approve_reservations.html', context)


@staff_required
def loan_management(request):
    """Manage active loans and overdue books"""
    loans = BookLoan.objects.filter(
        status='borrowed'
    ).select_related('user', 'book_copy__book').order_by('due_date')

    # Filter overdue
    if request.GET.get('filter') == 'overdue':
        loans = loans.filter(due_date__lt=datetime.now().date())

    context = {
        'loans': loans,
        'overdue_count': BookLoan.objects.filter(
            status='borrowed',
            due_date__lt=datetime.now().date()
        ).count()
    }
    return render(request, 'library/loan_management.html', context)


@staff_required
def fine_management(request):
    """Manage fines"""
    fines = Fine.objects.select_related(
        'user',
        'book_loan__user',
        'book_loan__book_copy__book',
        'book_loan__book_copy__branch'
    ).order_by('-fine_date')

    # Filter unpaid
    if request.GET.get('filter') == 'unpaid':
        fines = fines.filter(paid=False)

    context = {
        'fines': fines,
        'stats': {
            'unpaid_count': Fine.objects.filter(paid=False).count(),
            'unpaid_amount': Fine.objects.filter(
                paid=False
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0'),
            'paid_today': Fine.objects.filter(
                paid=True,
                paid_date__date=datetime.now().date()
            ).count(),
            'monthly_collection': Fine.objects.filter(
                paid=True,
                paid_date__month=datetime.now().month
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        },
        'branches': Branch.objects.all(),
        'unpaid_count': Fine.objects.filter(paid=False).count(),
        'total_unpaid_amount': Fine.objects.filter(
            paid=False
        ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    }
    return render(request, 'library/fine_management.html', context)


@manager_required
def manager_dashboard(request):
    """Manager dashboard with comprehensive stats and reports"""
    # Date range for reports
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    context = {
        # Basic stats
        'total_books': Book.objects.count(),
        'total_members': User.objects.filter(is_staff=False).count(),
        'total_branches': Branch.objects.count(),
        'total_staff': User.objects.filter(
            userrole__role__name__in=['librarian', 'manager']
        ).distinct().count(),

        # Loan stats
        'active_loans': BookLoan.objects.filter(status='borrowed').count(),
        'weekly_loans': BookLoan.objects.filter(
            borrow_date__gte=week_ago
        ).count(),
        'monthly_loans': BookLoan.objects.filter(
            borrow_date__gte=month_ago
        ).count(),

        # Fine stats
        'total_fines': Fine.objects.aggregate(
            Sum('amount')
        )['amount__sum'] or 0,
        'unpaid_fines': Fine.objects.filter(paid=False).aggregate(
            Sum('amount')
        )['amount__sum'] or 0,
        'monthly_fine_revenue': Payment.objects.filter(
            payment_date__gte=month_ago,
            payment_type='fine_payment'
        ).aggregate(Sum('amount'))['amount__sum'] or 0,

        # Top stats
        'most_borrowed_books': Book.objects.annotate(
            loan_count=Count('bookcopy__bookloan')
        ).order_by('-loan_count')[:5],

        'overdue_count': BookLoan.objects.filter(
            status='borrowed',
            due_date__lt=today
        ).count(),
    }
    return render(request, 'library/manager_dashboard.html', context)


@manager_required
def branch_management(request):
    """Manage library branches"""
    branches = Branch.objects.annotate(
        section_count=Count('section'),
        book_count=Count('section__bookcopy')
    ).order_by('name')

    context = {'branches': branches}
    return render(request, 'library/branch_management.html', context)


@manager_required
def staff_management(request):
    """Manage librarian accounts"""
    staff_users = User.objects.filter(
        userrole__role__name__in=['librarian', 'manager']
    ).select_related().prefetch_related('userrole_set__role').distinct()

    context = {'staff_users': staff_users}
    return render(request, 'library/staff_management.html', context)


@manager_required
def generate_report(request):
    """Generate various reports"""
    report_type = request.GET.get('type', 'loans')

    if report_type == 'loans':
        data = _generate_loan_report(request)
    elif report_type == 'overdue':
        data = _generate_overdue_report(request)
    elif report_type == 'fines':
        data = _generate_fine_report(request)
    elif report_type == 'revenue':
        data = _generate_revenue_report(request)
    else:
        data = {'error': 'Invalid report type'}

    if request.GET.get('format') == 'csv':
        return _export_csv(data, report_type)

    return JsonResponse(data)


def _generate_loan_report(request):
    """Generate loan statistics report"""
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    loans = BookLoan.objects.all()
    if start_date:
        loans = loans.filter(borrow_date__gte=start_date)
    if end_date:
        loans = loans.filter(borrow_date__lte=end_date)

    return {
        'total_loans': loans.count(),
        'active_loans': loans.filter(status='borrowed').count(),
        'returned_loans': loans.filter(status='returned').count(),
        'overdue_loans': loans.filter(
            status='borrowed',
            due_date__lt=datetime.now().date()
        ).count(),
        'loans_by_month': list(loans.extra(
            select={'month': "strftime('%%Y-%%m', borrow_date)"}
        ).values('month').annotate(count=Count('id')).order_by('month')),
    }


def _generate_overdue_report(request):
    """Generate overdue books report"""
    overdue_loans = BookLoan.objects.filter(
        status='borrowed',
        due_date__lt=datetime.now().date()
    ).select_related('user', 'book_copy__book')

    return {
        'overdue_loans': [
            {
                'user': loan.user.username,
                'book': loan.book_copy.book.title,
                'due_date': loan.due_date.isoformat(),
                'days_overdue': (datetime.now().date() - loan.due_date).days
            }
            for loan in overdue_loans
        ]
    }


def _generate_fine_report(request):
    """Generate fine statistics report"""
    fines = Fine.objects.all()

    return {
        'total_fines': fines.aggregate(Sum('amount'))['amount__sum'] or 0,
        'paid_fines': fines.filter(paid=True).aggregate(
            Sum('amount')
        )['amount__sum'] or 0,
        'unpaid_fines': fines.filter(paid=False).aggregate(
            Sum('amount')
        )['amount__sum'] or 0,
        'fine_count': fines.count(),
    }


def _generate_revenue_report(request):
    """Generate revenue report"""
    payments = Payment.objects.all()

    return {
        'total_revenue': payments.aggregate(Sum('amount'))['amount__sum'] or 0,
        'fine_revenue': payments.filter(
            payment_type='fine_payment'
        ).aggregate(Sum('amount'))['amount__sum'] or 0,
        'membership_revenue': payments.filter(
            payment_type='membership_fee'
        ).aggregate(Sum('amount'))['amount__sum'] or 0,
    }


def _export_csv(data, report_type):
    """Export report data as CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="{report_type}_report.csv"'
    )

    writer = csv.writer(response)

    if report_type == 'loans':
        writer.writerow(['Metric', 'Count'])
        writer.writerow(['Total Loans', data['total_loans']])
        writer.writerow(['Active Loans', data['active_loans']])
        writer.writerow(['Returned Loans', data['returned_loans']])
        writer.writerow(['Overdue Loans', data['overdue_loans']])

    elif report_type == 'overdue':
        writer.writerow(['User', 'Book', 'Due Date', 'Days Overdue'])
        for loan in data['overdue_loans']:
            writer.writerow([
                loan['user'], loan['book'],
                loan['due_date'], loan['days_overdue']
            ])

    return response
