"""
Payment views for Library Management System
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse
from circulation.models import Fine
from .models import Payment, FinePayment


@method_decorator(login_required, name='dispatch')
class PaymentHomeView(TemplateView):
    """Payment home page"""
    template_name = 'payments/home.html'


@method_decorator(login_required, name='dispatch')
class MembershipPaymentView(View):
    """Membership payment view"""
    template_name = 'payments/membership.html'
    
    def get(self, request):
        from authentication.models import MembershipFee
        
        context = {
            'membership_types': MembershipFee.objects.all(),
            'current_membership': request.user.membership_fee,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        from authentication.models import MembershipFee, User
        from .models import Payment, MembershipPayment
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        membership_type = request.POST.get('membership_type')
        payment_method = request.POST.get('payment_method', 'cash')
        period = request.POST.get('period', 'monthly')
        amount = request.POST.get('amount')
        notes = request.POST.get('notes', '')
        
        if not membership_type or not amount:
            messages.error(request, 'Please select a membership plan.')
            return redirect('payments:membership')
        
        try:
            # Get membership fee details
            membership_fee = MembershipFee.objects.get(membership_type=membership_type)
            
            # Create payment record
            payment = Payment.objects.create(
                user=request.user,
                purpose='membership',
                related_id=membership_fee.id,
                amount=amount,
                payment_method=payment_method,
                status='completed',
                notes=notes
            )
            
            # Calculate validity period
            today = timezone.now().date()
            if period == 'annually':
                valid_until = today + timedelta(days=365)
            else:
                valid_until = today + timedelta(days=30)
            
            # Create membership payment record
            MembershipPayment.objects.create(
                user=request.user,
                payment=payment,
                membership_type=membership_type,
                period=period,
                valid_from=today,
                valid_until=valid_until
            )
            
            # Update user's membership
            request.user.membership_fee = membership_fee
            request.user.membership_status = 'active'
            request.user.save()
            
            messages.success(
                request,
                f'{membership_fee.get_membership_type_display()} membership activated successfully! '
                f'Valid until {valid_until.strftime("%B %d, %Y")}.'
            )
            
            return redirect('library:dashboard')
            
        except MembershipFee.DoesNotExist:
            messages.error(request, 'Invalid membership type selected.')
            return redirect('payments:membership')
        except Exception as e:
            messages.error(request, f'Payment processing failed: {str(e)}')
            return redirect('payments:membership')


@method_decorator(login_required, name='dispatch')
class FinePaymentView(ListView):
    """Fine payment view"""
    template_name = 'payments/fines.html'
    context_object_name = 'fines'
    
    def get_queryset(self):
        return Fine.objects.filter(user=self.request.user, paid=False)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        unpaid_fines = self.get_queryset()
        context['total_unpaid'] = sum(fine.amount for fine in unpaid_fines)
        context['fine_count'] = unpaid_fines.count()
        return context


@method_decorator(login_required, name='dispatch')
class PayFineView(View):
    """Pay specific fine"""
    template_name = 'payments/pay_fine.html'
    
    def get(self, request, fine_id):
        fine = get_object_or_404(
            Fine, id=fine_id, user=request.user, paid=False
        )
        context = {
            'fine': fine,
            'book_title': (
                fine.book_loan.book_copy.book.title
                if fine.book_loan else 'N/A'
            ),
            'book_barcode': (
                fine.book_loan.book_copy.barcode
                if fine.book_loan else 'N/A'
            ),
        }
        return render(request, self.template_name, context)
    
    def post(self, request, fine_id):
        fine = get_object_or_404(
            Fine, id=fine_id, user=request.user, paid=False
        )
        payment_method = request.POST.get('payment_method', 'cash')
        
        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            purpose='fine',
            related_id=fine.id,
            amount=fine.amount,
            payment_method=payment_method,
            status='completed'
        )
        
        # Create fine payment record
        FinePayment.objects.create(
            user=request.user,
            payment=payment,
            fine=fine
        )
        
        # Mark fine as paid
        fine.mark_paid()
        
        messages.success(
            request,
            f'Fine of MVR {fine.amount} has been paid successfully!'
        )
        return redirect('circulation:my_fines')


@method_decorator(login_required, name='dispatch')
class DigitalServicePaymentView(View):
    """Digital service payment view"""
    template_name = 'payments/services.html'
    
    def get(self, request):
        return render(request, self.template_name)


@method_decorator(login_required, name='dispatch')
class PaymentHistoryView(ListView):
    """Payment history view"""
    template_name = 'payments/history.html'
    context_object_name = 'payments'
    
    def get_queryset(self):
        return []


@method_decorator(login_required, name='dispatch')
class PaymentManageView(TemplateView):
    """Payment management dashboard"""
    template_name = 'payments/manage.html'


@method_decorator(login_required, name='dispatch')
class PaymentReportsView(TemplateView):
    """Payment reports"""
    template_name = 'payments/reports.html'


@method_decorator(login_required, name='dispatch')
class ProcessPaymentView(View):
    """Process payment"""
    template_name = 'payments/process.html'
    
    def get(self, request, transaction_id):
        return render(request, self.template_name, {'transaction_id': transaction_id})
