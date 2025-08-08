"""
Payment views for Library Management System
"""

from django.shortcuts import render
from django.views.generic import TemplateView, ListView, View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


@method_decorator(login_required, name='dispatch')
class PaymentHomeView(TemplateView):
    """Payment home page"""
    template_name = 'payments/home.html'


@method_decorator(login_required, name='dispatch')
class MembershipPaymentView(View):
    """Membership payment view"""
    template_name = 'payments/membership.html'
    
    def get(self, request):
        return render(request, self.template_name)


@method_decorator(login_required, name='dispatch')
class FinePaymentView(ListView):
    """Fine payment view"""
    template_name = 'payments/fines.html'
    context_object_name = 'fines'
    
    def get_queryset(self):
        return []


@method_decorator(login_required, name='dispatch')
class PayFineView(View):
    """Pay specific fine"""
    template_name = 'payments/pay_fine.html'
    
    def get(self, request, fine_id):
        return render(request, self.template_name, {'fine_id': fine_id})


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
