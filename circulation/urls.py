"""
Circulation URLs
"""

from django.urls import path
from . import views

app_name = 'circulation'

urlpatterns = [
    # User views
    path('my-loans/', views.MyLoansView.as_view(), name='my_loans'),
    path('my-reservations/', views.MyReservationsView.as_view(),
         name='my_reservations'),
    path('my-fines/', views.MyFinesView.as_view(), name='my_fines'),
    
    # Actions
    path('borrow/<int:book_id>/', views.BorrowBookView.as_view(),
         name='borrow'),
    path('borrow-copy/<int:copy_id>/', views.BorrowCopyView.as_view(),
         name='borrow_copy'),
    path('reserve/<int:book_id>/', views.ReserveBookView.as_view(),
         name='reserve'),
    path('extend/<int:loan_id>/', views.ExtendLoanView.as_view(),
         name='extend'),
    path('return/<int:loan_id>/', views.ReturnBookView.as_view(),
         name='return'),
    
    # Staff views
    path('manage/loans/', views.ManageLoansView.as_view(),
         name='manage_loans'),
]
