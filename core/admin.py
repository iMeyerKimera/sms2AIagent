from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import User, Task, ErrorLog


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin interface for User model"""
    list_display = [
        'phone_number', 'tier', 'email', 'full_name', 
        'total_requests', 'monthly_requests', 'created_at', 
        'last_active', 'rate_limit_status'
    ]
    list_filter = ['tier', 'created_at', 'last_active']
    search_fields = ['phone_number', 'email', 'full_name']
    readonly_fields = ['created_at', 'total_requests', 'monthly_requests', 'rate_limit_reset']
    ordering = ['-last_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('phone_number', 'tier', 'email', 'full_name')
        }),
        ('Activity', {
            'fields': ('created_at', 'last_active', 'total_requests', 'monthly_requests', 'rate_limit_reset')
        }),
        ('Settings', {
            'fields': ('timezone', 'preferences'),
            'classes': ('collapse',)
        })
    )
    
    def rate_limit_status(self, obj):
        """Show rate limit status"""
        usage_percent = (obj.monthly_requests / obj.rate_limit * 100) if obj.rate_limit > 0 else 0
        
        if usage_percent >= 90:
            color = 'red'
        elif usage_percent >= 75:
            color = 'orange'
        else:
            color = 'green'
            
        return format_html(
            '<span style="color: {};">{}/{} ({}%)</span>',
            color,
            obj.monthly_requests,
            obj.rate_limit,
            round(usage_percent, 1)
        )
    rate_limit_status.short_description = 'Rate Limit Status'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related()


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin interface for Task model"""
    list_display = [
        'id', 'user_phone', 'category', 'success_status', 
        'processing_time', 'tokens_used', 'complexity_score',
        'created_at', 'completed_at'
    ]
    list_filter = [
        'success', 'category', 'created_at', 'completed_at'
    ]
    search_fields = [
        'user_phone__phone_number', 'sms_content', 'ai_response', 'error_message'
    ]
    readonly_fields = [
        'id', 'created_at', 'completed_at', 'processing_time'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Task Information', {
            'fields': ('id', 'user_phone', 'category', 'created_at', 'completed_at')
        }),
        ('Content', {
            'fields': ('sms_content', 'ai_response')
        }),
        ('Metrics', {
            'fields': ('processing_time', 'tokens_used', 'complexity_score', 'success')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        })
    )
    
    def success_status(self, obj):
        """Show success status with color"""
        if obj.success:
            return format_html('<span style="color: green;">✓ Success</span>')
        else:
            return format_html('<span style="color: red;">✗ Failed</span>')
    success_status.short_description = 'Status'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('user_phone')


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    """Admin interface for ErrorLog model"""
    list_display = [
        'id', 'error_type', 'user_phone', 'task', 
        'resolved_status', 'timestamp'
    ]
    list_filter = [
        'error_type', 'resolved', 'timestamp'
    ]
    search_fields = [
        'error_message', 'user_phone__phone_number', 'task__id'
    ]
    readonly_fields = ['id', 'timestamp']
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Error Information', {
            'fields': ('id', 'error_type', 'timestamp', 'resolved')
        }),
        ('Context', {
            'fields': ('user_phone', 'task')
        }),
        ('Details', {
            'fields': ('error_message', 'stack_trace')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        })
    )
    
    def resolved_status(self, obj):
        """Show resolved status with color"""
        if obj.resolved:
            return format_html('<span style="color: green;">✓ Resolved</span>')
        else:
            return format_html('<span style="color: red;">✗ Unresolved</span>')
    resolved_status.short_description = 'Status'
    
    actions = ['mark_resolved', 'mark_unresolved']
    
    def mark_resolved(self, request, queryset):
        """Mark selected errors as resolved"""
        updated = queryset.update(resolved=True)
        self.message_user(request, f'{updated} error(s) marked as resolved.')
    mark_resolved.short_description = 'Mark selected errors as resolved'
    
    def mark_unresolved(self, request, queryset):
        """Mark selected errors as unresolved"""
        updated = queryset.update(resolved=False)
        self.message_user(request, f'{updated} error(s) marked as unresolved.')
    mark_unresolved.short_description = 'Mark selected errors as unresolved'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('user_phone', 'task')


# Customize admin site
admin.site.site_header = 'SMS AI Agent Administration'
admin.site.site_title = 'SMS AI Agent Admin'
admin.site.index_title = 'Welcome to SMS AI Agent Administration' 