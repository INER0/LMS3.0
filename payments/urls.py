"""
Payments URLs
"""

from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.PaymentHomeView.as_view(), name='home'),
    path('membership/', views.MembershipPaymentView.as_view(), name='membership'),
    path('fines/', views.FinePaymentView.as_view(), name='fines'),
    path('fine/<int:fine_id>/pay/', views.PayFineView.as_view(), name='pay_fine'),
    path('services/', views.DigitalServicePaymentView.as_view(), name='services'),
    path('history/', views.PaymentHistoryView.as_view(), name='history'),
    
    # Staff/Admin views
    path('manage/', views.PaymentManageView.as_view(), name='manage'),
    path('reports/', views.PaymentReportsView.as_view(), name='reports'),
    path('process/<uuid:transaction_id>/', 
         views.ProcessPaymentView.as_view(), name='process'),
]
