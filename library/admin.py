"""
Admin configuration for library models
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Branch, BranchManager, Section, Publisher, Author, Book, 
    BookAuthor, BookCopy, BookCondition, BookBorrowHistory,
    SystemSetting, UserNotification
)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'created_at']
    search_fields = ['name', 'location']
    ordering = ['name']


@admin.register(BranchManager)
class BranchManagerAdmin(admin.ModelAdmin):
    list_display = ['branch', 'user']
    list_filter = ['branch']
    search_fields = ['branch__name', 'user__username']


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'branch']
    list_filter = ['branch']
    search_fields = ['name', 'branch__name']
    ordering = ['branch', 'name']


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']


class BookAuthorInline(admin.TabularInline):
    model = BookAuthor
    extra = 1


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'isbn', 'category', 'publication_year', 'publisher', 'section']
    list_filter = ['category', 'language', 'publication_year', 'section__branch']
    search_fields = ['title', 'isbn', 'bookauthor__author__name']
    ordering = ['title']
    inlines = [BookAuthorInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('publisher', 'section')


@admin.register(BookAuthor)
class BookAuthorAdmin(admin.ModelAdmin):
    list_display = ['book', 'author']
    list_filter = ['author']
    search_fields = ['book__title', 'author__name']


class BookConditionInline(admin.TabularInline):
    model = BookCondition
    extra = 0
    readonly_fields = ['updated_at']


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    list_display = ['book', 'barcode', 'condition', 'purchase_price', 'availability_status']
    list_filter = ['condition', 'last_seen']
    search_fields = ['book__title', 'barcode']
    ordering = ['book', 'barcode']
    inlines = [BookConditionInline]
    
    def availability_status(self, obj):
        if obj.is_available():
            return format_html('<span style="color: green;">✓ Available</span>')
        else:
            return format_html('<span style="color: red;">✗ Not Available</span>')
    availability_status.short_description = 'Status'


@admin.register(BookCondition)
class BookConditionAdmin(admin.ModelAdmin):
    list_display = ['book_copy', 'condition', 'updated_at']
    list_filter = ['condition', 'updated_at']
    search_fields = ['book_copy__book__title', 'book_copy__barcode']
    readonly_fields = ['updated_at']
    ordering = ['-updated_at']


@admin.register(BookBorrowHistory)
class BookBorrowHistoryAdmin(admin.ModelAdmin):
    list_display = ['book_copy', 'user', 'borrow_date', 'return_date']
    list_filter = ['borrow_date', 'return_date']
    search_fields = ['book_copy__book__title', 'user__username']
    ordering = ['-borrow_date']


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value']
    search_fields = ['key']
    ordering = ['key']


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'sent_at', 'read', 'message_preview']
    list_filter = ['type', 'sent_at', 'read']
    search_fields = ['user__username', 'message']
    ordering = ['-sent_at']
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message Preview'
