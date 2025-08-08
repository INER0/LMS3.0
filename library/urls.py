"""
Library URLs
"""

from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('books/', views.BookSearchView.as_view(), name='book_search'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book_detail'),
    path('borrowing-rules/', views.BorrowingRulesView.as_view(), name='borrowing_rules'),
    
    # Staff/Admin views
    path('manage/books/', views.ManageBooksView.as_view(), name='manage_books'),
]
