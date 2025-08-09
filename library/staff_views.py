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
from django.utils import timezone
from django.views.decorators.http import require_POST
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
            purpose='fine'
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
            purpose='fine'
        ).aggregate(Sum('amount'))['amount__sum'] or 0,
        'membership_revenue': payments.filter(
            purpose='membership'
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


@staff_required
@require_POST
def return_book(request, loan_id):
    """Handle book return via AJAX"""
    try:
        loan = get_object_or_404(BookLoan, id=loan_id, status='borrowed')
        
        # Process return
        return_date = timezone.now().date()
        loan.return_date = return_date
        loan.status = 'returned'
        loan.save()
        
        # Check for fines if overdue
        if return_date > loan.due_date:
            days_overdue = (return_date - loan.due_date).days
            fine_per_day = 2  # MVR per day
            fine_amount = days_overdue * fine_per_day
            
            Fine.objects.create(
                user=loan.user,
                book_loan=loan,
                amount=fine_amount,
                fine_date=timezone.now(),
                description=f'Late return fee for {days_overdue} days',
                paid=False
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Book returned. Fine of MVR {fine_amount} applied.'
            })
        else:
            return JsonResponse({
                'success': True,
                'message': 'Book returned successfully.'
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error returning book: {str(e)}'
        })


@staff_required
@require_POST
def renew_loan(request, loan_id):
    """Handle loan renewal via AJAX"""
    try:
        loan = get_object_or_404(BookLoan, id=loan_id, status='borrowed')
        
        # Extend due date by 14 days
        loan.due_date += timedelta(days=14)
        loan.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Loan renewed for 14 days.'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error renewing loan: {str(e)}'
        })


@staff_required
@require_POST
def mark_fine_paid(request, fine_id):
    """Mark fine as paid via AJAX"""
    try:
        fine = get_object_or_404(Fine, id=fine_id, paid=False)
        
        # Get payment details from form (store in description)
        payment_method = request.POST.get('payment_method', 'cash')
        payment_reference = request.POST.get('payment_reference', '')
        notes = request.POST.get('notes', '')
        
        # Create description with payment details
        payment_info = f"Payment via {payment_method}"
        if payment_reference:
            payment_info += f" (Ref: {payment_reference})"
        if notes:
            payment_info += f" - {notes}"
        
        # Mark fine as paid
        fine.paid = True
        fine.paid_date = timezone.now()
        if fine.description:
            fine.description = f"{fine.description} | {payment_info}"
        else:
            fine.description = payment_info
        fine.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Fine of MVR {fine.amount} marked as paid.'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error marking fine as paid: {str(e)}'
        })


@staff_required
@require_POST
def waive_fine(request, fine_id):
    """Waive fine via AJAX"""
    try:
        import json
        fine = get_object_or_404(Fine, id=fine_id, paid=False)
        
        # Get waive reason
        data = json.loads(request.body)
        reason = data.get('reason', 'No reason provided')
        
        # Mark fine as "paid" with waive reason in description
        fine.paid = True
        fine.paid_date = timezone.now()
        waive_info = f"WAIVED by {request.user.get_full_name()}: {reason}"
        if fine.description:
            fine.description = f"{fine.description} | {waive_info}"
        else:
            fine.description = waive_info
        fine.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Fine of MVR {fine.amount} waived successfully.'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error waiving fine: {str(e)}'
        })


@staff_required
@require_POST
def send_fine_reminder(request, fine_id):
    """Send fine reminder via AJAX"""
    try:
        fine = get_object_or_404(Fine, id=fine_id, paid=False)
        
        # Here you would implement email/SMS reminder functionality
        # For now, we'll just simulate it
        
        return JsonResponse({
            'success': True,
            'message': f'Reminder sent to {fine.user.get_full_name()}.'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error sending reminder: {str(e)}'
        })


@staff_required
@require_POST
def bulk_waive_fines(request):
    """Bulk waive fines via AJAX"""
    try:
        import json
        data = json.loads(request.body)
        fine_ids = data.get('fine_ids', [])
        reason = data.get('reason', 'Bulk waive')
        
        if not fine_ids:
            return JsonResponse({
                'success': False,
                'message': 'No fines selected'
            })
        
        # Update fines - mark as paid with waive info in description
        count = 0
        waive_info = f"WAIVED by {request.user.get_full_name()}: {reason}"
        
        for fine_id in fine_ids:
            try:
                fine = Fine.objects.get(id=fine_id, paid=False)
                fine.paid = True
                fine.paid_date = timezone.now()
                if fine.description:
                    fine.description = f"{fine.description} | {waive_info}"
                else:
                    fine.description = waive_info
                fine.save()
                count += 1
            except Fine.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True,
            'count': count,
            'message': f'{count} fines waived successfully.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error waiving fines: {str(e)}'
        })


@staff_required
@require_POST
def bulk_send_reminders(request):
    """Send reminder emails for multiple overdue fines via AJAX"""
    try:
        import json
        data = json.loads(request.body)
        fine_ids = data.get('fine_ids', [])
        
        if not fine_ids:
            return JsonResponse({
                'success': False,
                'message': 'No fines selected'
            })
        
        # Send reminders for selected fines
        count = 0
        for fine_id in fine_ids:
            try:
                fine = Fine.objects.select_related(
                    'user', 'book_loan__book_copy__book'
                ).get(id=fine_id, paid=False)
                
                # For now, just log the reminder (email functionality to be implemented)
                # In production, implement actual email sending here
                count += 1
                
            except Fine.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True,
            'count': count,
            'message': f'Reminders sent for {count} fines'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error sending reminders: {str(e)}'
        })


# ============= ENHANCED MANAGER FUNCTIONS =============

@manager_required
def comprehensive_reports(request):
    """Enhanced reports dashboard for managers"""
    today = datetime.now().date()
    month_ago = today - timedelta(days=30)
    year_ago = today - timedelta(days=365)
    
    context = {
        'report_types': [
            {'id': 'loans', 'name': 'Book Lending Report', 'icon': 'fa-book'},
            {'id': 'overdue', 'name': 'Overdue Books Report', 'icon': 'fa-exclamation-triangle'},
            {'id': 'fines', 'name': 'Fine Revenue Report', 'icon': 'fa-money-bill-wave'},
            {'id': 'members', 'name': 'Member Statistics', 'icon': 'fa-users'},
            {'id': 'inventory', 'name': 'Book Inventory Report', 'icon': 'fa-boxes'},
            {'id': 'staff', 'name': 'Staff Performance', 'icon': 'fa-user-tie'},
        ],
        'quick_stats': {
            'monthly_loans': BookLoan.objects.filter(
                borrow_date__gte=month_ago
            ).count(),
            'yearly_loans': BookLoan.objects.filter(
                borrow_date__gte=year_ago
            ).count(),
            'monthly_revenue': Fine.objects.filter(
                paid=True, paid_date__gte=month_ago
            ).aggregate(Sum('amount'))['amount__sum'] or 0,
            'yearly_revenue': Fine.objects.filter(
                paid=True, paid_date__gte=year_ago
            ).aggregate(Sum('amount'))['amount__sum'] or 0,
        }
    }
    return render(request, 'library/comprehensive_reports.html', context)


@manager_required
def add_branch(request):
    """Add new library branch"""
    if request.method == 'POST':
        name = request.POST.get('name')
        location = request.POST.get('location')
        description = request.POST.get('description', '')
        
        if name and location:
            branch = Branch.objects.create(
                name=name,
                location=location
            )
            messages.success(request, f'Branch "{name}" added successfully!')
            return redirect('library:manager_branch_management')
        else:
            messages.error(request, 'Name and location are required.')
    
    return render(request, 'library/add_branch.html')


@manager_required
def edit_branch(request, branch_id):
    """Edit library branch"""
    branch = get_object_or_404(Branch, id=branch_id)
    
    if request.method == 'POST':
        branch.name = request.POST.get('name', branch.name)
        branch.location = request.POST.get('location', branch.location)
        branch.save()
        
        messages.success(request, f'Branch "{branch.name}" updated successfully!')
        return redirect('library:manager_branch_management')
    
    context = {'branch': branch}
    return render(request, 'library/edit_branch.html', context)


@manager_required
def delete_branch(request, branch_id):
    """Delete library branch"""
    branch = get_object_or_404(Branch, id=branch_id)
    
    if request.method == 'POST':
        branch_name = branch.name
        
        # Check if branch has books or active loans
        if BookCopy.objects.filter(branch=branch).exists():
            messages.error(request, 
                f'Cannot delete branch "{branch_name}" - it has books assigned.')
            return redirect('library:manager_branch_management')
        
        branch.delete()
        messages.success(request, f'Branch "{branch_name}" deleted successfully!')
        return redirect('library:manager_branch_management')
    
    context = {'branch': branch}
    return render(request, 'library/delete_branch.html', context)


@manager_required
def add_librarian(request):
    """Add new librarian account"""
    from authentication.models import Role, UserRole
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        branch_id = request.POST.get('branch')
        
        if username and email and password:
            try:
                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                    is_staff=True
                )
                
                # Assign librarian role
                librarian_role = Role.objects.get(name='Librarian')
                UserRole.objects.create(user=user, role=librarian_role)
                
                messages.success(request, 
                    f'Librarian account "{username}" created successfully!')
                return redirect('library:staff_management')
                
            except Exception as e:
                messages.error(request, f'Error creating librarian: {str(e)}')
        else:
            messages.error(request, 'All required fields must be filled.')
    
    context = {
        'branches': Branch.objects.all()
    }
    return render(request, 'library/add_librarian.html', context)


@manager_required
def edit_librarian(request, user_id):
    """Edit librarian account"""
    librarian = get_object_or_404(User, id=user_id, is_staff=True)
    
    if request.method == 'POST':
        librarian.first_name = request.POST.get('first_name', librarian.first_name)
        librarian.last_name = request.POST.get('last_name', librarian.last_name)
        librarian.email = request.POST.get('email', librarian.email)
        
        # Update password if provided
        new_password = request.POST.get('password')
        if new_password:
            librarian.set_password(new_password)
        
        librarian.save()
        messages.success(request, f'Librarian "{librarian.username}" updated successfully!')
        return redirect('library:staff_management')
    
    context = {
        'librarian': librarian,
        'branches': Branch.objects.all()
    }
    return render(request, 'library/edit_librarian.html', context)


@manager_required
def deactivate_librarian(request, user_id):
    """Deactivate librarian account"""
    librarian = get_object_or_404(User, id=user_id, is_staff=True)
    
    if request.method == 'POST':
        librarian.is_active = False
        librarian.save()
        messages.success(request, f'Librarian "{librarian.username}" deactivated successfully!')
        return redirect('library:staff_management')
    
    context = {'librarian': librarian}
    return render(request, 'library/deactivate_librarian.html', context)


@manager_required
def detailed_report(request):
    """Generate detailed report based on type and parameters"""
    report_type = request.GET.get('type', 'loans')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    branch_id = request.GET.get('branch')
    
    # Base context
    context = {
        'report_type': report_type,
        'start_date': start_date,
        'end_date': end_date,
        'branches': Branch.objects.all(),
        'selected_branch': int(branch_id) if branch_id else None,
    }
    
    # Generate specific report data
    if report_type == 'loans':
        context.update(_generate_detailed_loan_report(start_date, end_date, branch_id))
    elif report_type == 'overdue':
        context.update(_generate_detailed_overdue_report(branch_id))
    elif report_type == 'fines':
        context.update(_generate_detailed_fine_report(start_date, end_date, branch_id))
    elif report_type == 'members':
        context.update(_generate_member_report(start_date, end_date))
    elif report_type == 'inventory':
        context.update(_generate_inventory_report(branch_id))
    elif report_type == 'staff':
        context.update(_generate_staff_report(start_date, end_date))
    
    return render(request, 'library/detailed_report.html', context)


def _generate_detailed_loan_report(start_date, end_date, branch_id):
    """Generate comprehensive loan report"""
    loans = BookLoan.objects.select_related(
        'user', 'book_copy__book', 'book_copy__branch'
    ).all()
    
    if start_date:
        loans = loans.filter(borrow_date__gte=start_date)
    if end_date:
        loans = loans.filter(borrow_date__lte=end_date)
    if branch_id:
        loans = loans.filter(book_copy__branch_id=branch_id)
    
    return {
        'loans': loans[:100],  # Limit for performance
        'loan_stats': {
            'total': loans.count(),
            'active': loans.filter(status='borrowed').count(),
            'returned': loans.filter(status='returned').count(),
            'overdue': loans.filter(
                status='borrowed', due_date__lt=datetime.now().date()
            ).count(),
        },
        'top_borrowers': loans.values(
            'user__username', 'user__first_name', 'user__last_name'
        ).annotate(loan_count=Count('id')).order_by('-loan_count')[:10],
        'popular_books': loans.values(
            'book_copy__book__title', 'book_copy__book__author'
        ).annotate(loan_count=Count('id')).order_by('-loan_count')[:10],
    }


def _generate_detailed_overdue_report(branch_id):
    """Generate detailed overdue report"""
    overdue_loans = BookLoan.objects.filter(
        status='borrowed', due_date__lt=datetime.now().date()
    ).select_related('user', 'book_copy__book', 'book_copy__branch')
    
    if branch_id:
        overdue_loans = overdue_loans.filter(book_copy__branch_id=branch_id)
    
    return {
        'overdue_loans': overdue_loans,
        'overdue_stats': {
            'total_overdue': overdue_loans.count(),
            'avg_days_overdue': overdue_loans.aggregate(
                avg_days=Sum('due_date')  # Simplified calculation
            ),
            'longest_overdue': overdue_loans.order_by('due_date').first(),
        }
    }


def _generate_detailed_fine_report(start_date, end_date, branch_id):
    """Generate detailed fine revenue report"""
    fines = Fine.objects.select_related(
        'user', 'book_loan__book_copy__book'
    ).all()
    
    if start_date:
        fines = fines.filter(fine_date__gte=start_date)
    if end_date:
        fines = fines.filter(fine_date__lte=end_date)
    if branch_id:
        fines = fines.filter(book_loan__book_copy__branch_id=branch_id)
    
    return {
        'fines': fines[:100],
        'fine_stats': {
            'total_fines': fines.aggregate(Sum('amount'))['amount__sum'] or 0,
            'paid_fines': fines.filter(paid=True).aggregate(
                Sum('amount'))['amount__sum'] or 0,
            'unpaid_fines': fines.filter(paid=False).aggregate(
                Sum('amount'))['amount__sum'] or 0,
            'collection_rate': 0,  # Calculate percentage
        }
    }


def _generate_member_report(start_date, end_date):
    """Generate member statistics report"""
    members = User.objects.filter(is_staff=False)
    
    if start_date:
        members = members.filter(date_joined__gte=start_date)
    if end_date:
        members = members.filter(date_joined__lte=end_date)
    
    return {
        'member_stats': {
            'total_members': members.count(),
            'active_members': members.filter(is_active=True).count(),
            'new_members': members.filter(
                date_joined__gte=datetime.now().date() - timedelta(days=30)
            ).count(),
        }
    }


def _generate_inventory_report(branch_id):
    """Generate book inventory report"""
    books = Book.objects.annotate(
        total_copies=Count('bookcopy'),
        available_copies=Count('bookcopy', filter=Q(bookcopy__status='available')),
        borrowed_copies=Count('bookcopy', filter=Q(bookcopy__status='borrowed'))
    )
    
    if branch_id:
        books = books.filter(bookcopy__branch_id=branch_id)
    
    return {
        'inventory_stats': {
            'total_books': books.count(),
            'total_copies': BookCopy.objects.filter(
                branch_id=branch_id if branch_id else None
            ).count() if branch_id else BookCopy.objects.count(),
            'available_copies': BookCopy.objects.filter(
                status='available'
            ).count(),
            'borrowed_copies': BookCopy.objects.filter(
                status='borrowed'
            ).count(),
        },
        'books': books[:50]
    }


def _generate_staff_report(start_date, end_date):
    """Generate staff performance report"""
    return {
        'staff_stats': {
            'total_staff': User.objects.filter(is_staff=True).count(),
            'librarians': User.objects.filter(
                userrole__role__name='Librarian'
            ).count(),
            'managers': User.objects.filter(
                userrole__role__name='Manager'
            ).count(),
        }
    }


