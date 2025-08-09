"""
Library URLs
"""

from django.urls import path
from . import views, staff_views

app_name = 'library'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('books/', views.BookSearchView.as_view(), name='book_search'),
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
    
    # Manager views
    path('manager/', staff_views.manager_dashboard, name='manager_dashboard'),
    path('manager/branches/', staff_views.branch_management,
         name='manager_branch_management'),
    path('manager/staff/', staff_views.staff_management,
         name='staff_management'),
    path('manager/reports/', staff_views.generate_report,
         name='generate_report'),
]
