"""
Library URLs
"""

from django.urls import path
from . import views, staff_views

app_name = 'library'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('books/', views.BookSearchView.as_view(), name='book_search'),
    path('books/search/', views.BookSearchView.as_view(), name='book_search_alternate'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book_detail'),
    path('borrowing-rules/', views.BorrowingRulesView.as_view(), name='borrowing_rules'),
    
    # Staff/Admin views
    path('manage/books/', views.ManageBooksView.as_view(), name='manage_books'),
    path('manage/books/<int:pk>/edit/', views.EditBookView.as_view(),
         name='edit_book'),
    path('manage/books/<int:pk>/delete/', views.DeleteBookView.as_view(),
         name='delete_book'),
    path('manage/books/<int:pk>/add-copy/', views.AddBookCopyView.as_view(),
         name='add_book_copy'),
    path('manage/books/<int:pk>/copies/', views.ManageBookCopiesView.as_view(),
         name='manage_book_copies'),
    path('manage/books/add/', views.AddBookView.as_view(), name='add_book'),
    
    # Book copy management
    path('manage/book-copies/<int:pk>/edit/', views.EditBookCopyView.as_view(),
         name='edit_book_copy'),
    path('manage/book-copies/<int:pk>/delete/',
         views.DeleteBookCopyView.as_view(), name='delete_book_copy'),
    
    # Branch management
    path('manage/branches/', views.BranchManagementView.as_view(),
         name='branch_management'),
    path('branches/<int:pk>/', views.BranchDetailView.as_view(),
         name='branch_detail'),
    path('set-branch/<int:branch_id>/', views.set_active_branch,
         name='set_active_branch'),
    path('ajax/sections/', views.get_sections_for_branch,
         name='get_sections_for_branch'),
    
    # Staff management views
    path('staff/', staff_views.staff_dashboard, name='staff_dashboard'),
    path('staff/books/', staff_views.BookManagementView.as_view(),
         name='staff_book_management'),
    path('staff/reservations/', staff_views.approve_reservations,
         name='approve_reservations'),
    path('staff/loans/', staff_views.loan_management, name='loan_management'),
    path('staff/fines/', staff_views.fine_management, name='fine_management'),
    
    # Loan management endpoints
    path('loans/<int:loan_id>/return/', staff_views.return_book,
         name='return_book'),
    path('loans/<int:loan_id>/renew/', staff_views.renew_loan,
         name='renew_loan'),
    
    # Fine management endpoints
    path('fines/<int:fine_id>/pay/', staff_views.mark_fine_paid,
         name='mark_fine_paid'),
    path('fines/<int:fine_id>/waive/', staff_views.waive_fine,
         name='waive_fine'),
    path('fines/<int:fine_id>/remind/', staff_views.send_fine_reminder,
         name='send_fine_reminder'),
    path('fines/bulk-waive/', staff_views.bulk_waive_fines,
         name='bulk_waive_fines'),
    path('fines/bulk-remind/', staff_views.bulk_send_reminders,
         name='bulk_send_reminders'),
    
    # Manager views
    path('manager/', staff_views.manager_dashboard, name='manager_dashboard'),
    path('manager/branches/', staff_views.branch_management,
         name='manager_branch_management'),
    path('manager/staff/', staff_views.staff_management,
         name='staff_management'),
    path('manager/reports/', staff_views.generate_report,
         name='generate_report'),
    
    # Enhanced Manager Functions
    path('manager/reports/comprehensive/', staff_views.comprehensive_reports,
         name='comprehensive_reports'),
    path('manager/reports/detailed/', staff_views.detailed_report,
         name='detailed_report'),
    
    # Branch Management
    path('manager/branches/add/', staff_views.add_branch, name='add_branch'),
    path('manager/branches/<int:branch_id>/edit/', staff_views.edit_branch,
         name='edit_branch'),
    path('manager/branches/<int:branch_id>/delete/', staff_views.delete_branch,
         name='delete_branch'),
    
    # Librarian Management  
    path('manager/librarians/add/', staff_views.add_librarian,
         name='add_librarian'),
    path('manager/librarians/<int:user_id>/edit/', staff_views.edit_librarian,
         name='edit_librarian'),
    path('manager/librarians/<int:user_id>/deactivate/',
         staff_views.deactivate_librarian, name='deactivate_librarian'),
]
