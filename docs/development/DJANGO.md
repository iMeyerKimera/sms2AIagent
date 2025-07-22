# 🐍 Django Integration Guide

**Complete Django implementation details for SMS-to-AI Agent**

---

## 📋 **Overview**

The SMS-to-AI Agent is built on Django, leveraging the framework's robust features for web development, ORM, admin interface, and REST API capabilities. This guide covers the complete Django implementation including models, views, serializers, and advanced features.

---

## 🏗️ **Project Structure**

### **Django Project Layout**

```
sms2AIagent/
├── manage.py                   # Django management script
├── sms_agent/                  # Main Django project
│   ├── __init__.py
│   ├── settings/               # Environment-specific settings
│   │   ├── __init__.py
│   │   ├── base.py            # Base settings
│   │   ├── development.py     # Development configuration
│   │   ├── production.py      # Production configuration
│   │   └── testing.py         # Testing configuration
│   ├── urls.py                # Main URL routing
│   ├── wsgi.py                # WSGI configuration
│   └── asgi.py                # ASGI configuration (future async support)
├── core/                       # Core application
│   ├── __init__.py
│   ├── admin.py               # Django admin configuration
│   ├── apps.py                # App configuration
│   ├── models.py              # Data models
│   ├── views.py               # API views and business logic
│   ├── serializers.py         # DRF serializers
│   ├── urls.py                # App URL routing
│   ├── permissions.py         # Custom permissions
│   ├── validators.py          # Custom validators
│   ├── utils.py               # Utility functions
│   ├── managers.py            # Custom model managers
│   ├── signals.py             # Django signals
│   ├── tasks.py               # Background tasks (if using Celery)
│   └── migrations/            # Database migrations
├── admin_dashboard/            # Custom admin interface
│   ├── __init__.py
│   ├── views.py               # Dashboard views
│   ├── urls.py                # Dashboard URL routing
│   ├── forms.py               # Dashboard forms
│   └── templatetags/          # Custom template tags
├── templates/                  # HTML templates
│   ├── admin/                 # Custom admin templates
│   ├── dashboard/             # Dashboard templates
│   └── base.html              # Base template
├── static/                     # Static files
│   ├── css/
│   ├── js/
│   └── img/
└── requirements/               # Dependencies
    ├── base.txt               # Base requirements
    ├── development.txt        # Development dependencies
    └── production.txt         # Production dependencies
```

---

## 🗄️ **Django Models**

### **Core Models Implementation**

```python
# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils import timezone
from django.contrib.postgres.fields import JSONField
import uuid

class TimestampedModel(models.Model):
    """Abstract base model with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class User(TimestampedModel):
    """SMS user model with tier management"""
    
    TIER_CHOICES = [
        ('free', 'Free'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in E.164 format"
    )
    
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        primary_key=True,
        help_text="E.164 format phone number"
    )
    tier = models.CharField(
        max_length=20,
        choices=TIER_CHOICES,
        default='free'
    )
    email = models.EmailField(blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True)
    last_active = models.DateTimeField(default=timezone.now)
    total_requests = models.PositiveIntegerField(default=0)
    monthly_requests = models.PositiveIntegerField(default=0)
    rate_limit_reset = models.DateTimeField(default=timezone.now)
    timezone = models.CharField(max_length=50, default='UTC')
    preferences = JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'core_user'
        indexes = [
            models.Index(fields=['tier']),
            models.Index(fields=['last_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.phone_number} ({self.tier})"
    
    def update_activity(self):
        """Update last active timestamp and increment request count"""
        self.last_active = timezone.now()
        self.total_requests += 1
        self.monthly_requests += 1
        self.save(update_fields=['last_active', 'total_requests', 'monthly_requests'])
    
    def reset_monthly_requests(self):
        """Reset monthly request counter"""
        self.monthly_requests = 0
        self.save(update_fields=['monthly_requests'])
    
    def can_make_request(self):
        """Check if user can make a request based on tier limits"""
        from .utils import get_rate_limit_for_tier
        limit = get_rate_limit_for_tier(self.tier)
        return self.monthly_requests < limit

class Task(TimestampedModel):
    """SMS processing task model"""
    
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('coding', 'Coding'),
        ('debug', 'Debug'),
        ('design', 'Design'),
        ('documentation', 'Documentation'),
        ('analysis', 'Analysis'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_phone = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    sms_content = models.TextField(help_text="Original SMS message content")
    ai_response = models.TextField(blank=True, help_text="Generated AI response")
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='general'
    )
    processing_time = models.FloatField(
        default=0.0,
        help_text="Processing time in seconds"
    )
    tokens_used = models.PositiveIntegerField(
        default=0,
        help_text="AI tokens consumed"
    )
    complexity_score = models.FloatField(
        default=1.0,
        help_text="Task complexity score (0.0-1.0)"
    )
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    metadata = JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'core_task'
        indexes = [
            models.Index(fields=['user_phone', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['success', '-created_at']),
            models.Index(fields=['-completed_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Task {self.id} - {self.category} ({self.user_phone})"
    
    def mark_completed(self, ai_response, processing_time, tokens_used):
        """Mark task as completed with results"""
        self.ai_response = ai_response
        self.processing_time = processing_time
        self.tokens_used = tokens_used
        self.completed_at = timezone.now()
        self.success = True
        self.save()
    
    def mark_failed(self, error_message):
        """Mark task as failed with error details"""
        self.error_message = error_message
        self.success = False
        self.completed_at = timezone.now()
        self.save()

class ErrorLog(TimestampedModel):
    """System error logging model"""
    
    ERROR_TYPE_CHOICES = [
        ('openai_timeout', 'OpenAI Timeout'),
        ('openai_error', 'OpenAI Error'),
        ('twilio_error', 'Twilio Error'),
        ('database_error', 'Database Error'),
        ('validation_error', 'Validation Error'),
        ('system_error', 'System Error'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_phone = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='error_logs'
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='error_logs'
    )
    error_type = models.CharField(max_length=50, choices=ERROR_TYPE_CHOICES)
    error_message = models.TextField()
    stack_trace = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    metadata = JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'core_errorlog'
        indexes = [
            models.Index(fields=['error_type', '-timestamp']),
            models.Index(fields=['user_phone', '-timestamp']),
            models.Index(fields=['resolved', '-timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.error_type} - {self.timestamp}"
    
    def resolve(self, notes=""):
        """Mark error as resolved"""
        self.resolved = True
        self.resolution_notes = notes
        self.save()
```

### **Custom Model Managers**

```python
# core/managers.py
from django.db import models
from django.utils import timezone
from datetime import timedelta

class UserManager(models.Manager):
    """Custom manager for User model"""
    
    def active_users(self):
        """Get active users"""
        return self.filter(is_active=True)
    
    def by_tier(self, tier):
        """Get users by tier"""
        return self.filter(tier=tier)
    
    def active_in_period(self, days=30):
        """Get users active in the last N days"""
        cutoff = timezone.now() - timedelta(days=days)
        return self.filter(last_active__gte=cutoff)
    
    def premium_users(self):
        """Get premium tier users"""
        return self.filter(tier__in=['premium', 'enterprise'])

class TaskManager(models.Manager):
    """Custom manager for Task model"""
    
    def successful(self):
        """Get successful tasks"""
        return self.filter(success=True)
    
    def failed(self):
        """Get failed tasks"""
        return self.filter(success=False)
    
    def by_category(self, category):
        """Get tasks by category"""
        return self.filter(category=category)
    
    def completed_today(self):
        """Get tasks completed today"""
        today = timezone.now().date()
        return self.filter(completed_at__date=today)
    
    def processing_stats(self):
        """Get processing statistics"""
        from django.db.models import Avg, Count, Sum
        return self.aggregate(
            total_tasks=Count('id'),
            avg_processing_time=Avg('processing_time'),
            total_tokens=Sum('tokens_used'),
            success_rate=Avg('success')
        )

class ErrorLogManager(models.Manager):
    """Custom manager for ErrorLog model"""
    
    def unresolved(self):
        """Get unresolved errors"""
        return self.filter(resolved=False)
    
    def by_type(self, error_type):
        """Get errors by type"""
        return self.filter(error_type=error_type)
    
    def recent(self, hours=24):
        """Get recent errors"""
        cutoff = timezone.now() - timedelta(hours=hours)
        return self.filter(timestamp__gte=cutoff)
```

---

## 🔌 **Django REST Framework Implementation**

### **Serializers**

```python
# core/serializers.py
from rest_framework import serializers
from .models import User, Task, ErrorLog
from django.utils import timezone

class UserSerializer(serializers.ModelSerializer):
    """User model serializer"""
    
    stats = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'phone_number', 'tier', 'email', 'full_name', 
            'created_at', 'last_active', 'total_requests',
            'monthly_requests', 'timezone', 'preferences', 'stats'
        ]
        read_only_fields = ['total_requests', 'monthly_requests', 'created_at']
    
    def get_stats(self, obj):
        """Get user statistics"""
        tasks = obj.tasks.all()
        if not tasks.exists():
            return {}
        
        successful_tasks = tasks.filter(success=True)
        return {
            'success_rate': round(
                (successful_tasks.count() / tasks.count()) * 100, 2
            ),
            'avg_response_time': round(
                successful_tasks.aggregate(
                    avg=models.Avg('processing_time')
                )['avg'] or 0, 2
            ),
            'favorite_categories': list(
                tasks.values('category')
                .annotate(count=models.Count('category'))
                .order_by('-count')
                .values_list('category', flat=True)[:3]
            )
        }

class TaskSerializer(serializers.ModelSerializer):
    """Task model serializer"""
    
    user_phone = serializers.CharField(source='user_phone.phone_number', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'user_phone', 'sms_content', 'ai_response',
            'category', 'processing_time', 'tokens_used',
            'complexity_score', 'success', 'error_message',
            'created_at', 'completed_at', 'metadata'
        ]
        read_only_fields = [
            'id', 'processing_time', 'tokens_used', 'success',
            'error_message', 'completed_at', 'created_at'
        ]

class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks"""
    
    user_phone = serializers.CharField()
    
    class Meta:
        model = Task
        fields = ['user_phone', 'sms_content', 'category']
    
    def validate_user_phone(self, value):
        """Validate user exists and is active"""
        try:
            user = User.objects.get(phone_number=value)
            if not user.is_active:
                raise serializers.ValidationError("User is not active")
            if not user.can_make_request():
                raise serializers.ValidationError("User has exceeded rate limit")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
    
    def create(self, validated_data):
        """Create task with user lookup"""
        user_phone = validated_data.pop('user_phone')
        user = User.objects.get(phone_number=user_phone)
        validated_data['user_phone'] = user
        return super().create(validated_data)

class ErrorLogSerializer(serializers.ModelSerializer):
    """Error log serializer"""
    
    user_phone = serializers.CharField(
        source='user_phone.phone_number', 
        read_only=True
    )
    task_id = serializers.CharField(source='task.id', read_only=True)
    
    class Meta:
        model = ErrorLog
        fields = [
            'id', 'user_phone', 'task_id', 'error_type',
            'error_message', 'stack_trace', 'timestamp',
            'resolved', 'resolution_notes', 'metadata'
        ]
        read_only_fields = ['id', 'timestamp']

class AnalyticsSerializer(serializers.Serializer):
    """Analytics data serializer"""
    
    total_users = serializers.IntegerField()
    active_users_24h = serializers.IntegerField()
    active_users_7d = serializers.IntegerField()
    total_tasks = serializers.IntegerField()
    tasks_24h = serializers.IntegerField()
    success_rate = serializers.FloatField()
    avg_response_time = serializers.FloatField()
    tier_distribution = serializers.DictField()
    top_categories = serializers.ListField()
```

### **API Views**

```python
# core/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
import logging

from .models import User, Task, ErrorLog
from .serializers import (
    UserSerializer, TaskSerializer, TaskCreateSerializer,
    ErrorLogSerializer, AnalyticsSerializer
)
from .permissions import IsAdminOrReadOnly
from .utils import send_sms, process_with_ai

logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    """User management viewset"""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tier', 'is_active']
    lookup_field = 'phone_number'
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, phone_number=None):
        """Send SMS message to user"""
        user = self.get_object()
        message = request.data.get('message')
        
        if not message:
            return Response(
                {'error': 'Message is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = send_sms(user.phone_number, message)
            logger.info(f"SMS sent to {user.phone_number}: {result.sid}")
            return Response({'message_sid': result.sid})
        except Exception as e:
            logger.error(f"Failed to send SMS to {user.phone_number}: {e}")
            return Response(
                {'error': 'Failed to send message'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def update_tier(self, request, phone_number=None):
        """Update user tier"""
        user = self.get_object()
        new_tier = request.data.get('tier')
        reason = request.data.get('reason', '')
        
        if new_tier not in ['free', 'premium', 'enterprise']:
            return Response(
                {'error': 'Invalid tier'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_tier = user.tier
        user.tier = new_tier
        user.save()
        
        logger.info(
            f"User {user.phone_number} tier updated: {old_tier} -> {new_tier}. "
            f"Reason: {reason}"
        )
        
        return Response({
            'message': f'Tier updated to {new_tier}',
            'old_tier': old_tier,
            'new_tier': new_tier
        })

class TaskViewSet(viewsets.ModelViewSet):
    """Task management viewset"""
    
    queryset = Task.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'success', 'user_phone']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        return TaskSerializer
    
    def get_queryset(self):
        """Filter tasks by date range if provided"""
        queryset = super().get_queryset()
        
        created_after = self.request.query_params.get('created_after')
        created_before = self.request.query_params.get('created_before')
        
        if created_after:
            queryset = queryset.filter(created_at__gte=created_after)
        if created_before:
            queryset = queryset.filter(created_at__lte=created_before)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get task analytics"""
        queryset = self.get_queryset()
        
        # Basic stats
        total_tasks = queryset.count()
        successful_tasks = queryset.filter(success=True).count()
        success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Performance stats
        performance_stats = queryset.aggregate(
            avg_processing_time=Avg('processing_time'),
            avg_tokens_used=Avg('tokens_used')
        )
        
        # Category breakdown
        category_stats = (
            queryset.values('category')
            .annotate(
                count=Count('id'),
                success_rate=Avg('success') * 100,
                avg_processing_time=Avg('processing_time')
            )
            .order_by('-count')
        )
        
        # Daily stats for the last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        daily_stats = []
        
        for i in range(30):
            date = (thirty_days_ago + timedelta(days=i)).date()
            day_tasks = queryset.filter(created_at__date=date)
            daily_stats.append({
                'date': date.isoformat(),
                'total_tasks': day_tasks.count(),
                'successful_tasks': day_tasks.filter(success=True).count(),
                'avg_processing_time': day_tasks.aggregate(
                    avg=Avg('processing_time')
                )['avg'] or 0
            })
        
        analytics_data = {
            'total_tasks': total_tasks,
            'successful_tasks': successful_tasks,
            'success_rate': round(success_rate, 2),
            'avg_processing_time': round(
                performance_stats['avg_processing_time'] or 0, 2
            ),
            'avg_tokens_used': round(
                performance_stats['avg_tokens_used'] or 0, 2
            ),
            'category_breakdown': {
                item['category']: {
                    'count': item['count'],
                    'success_rate': round(item['success_rate'], 1),
                    'avg_processing_time': round(item['avg_processing_time'] or 0, 2)
                }
                for item in category_stats
            },
            'daily_stats': daily_stats
        }
        
        return Response(analytics_data)

class ErrorLogViewSet(viewsets.ModelViewSet):
    """Error log management viewset"""
    
    queryset = ErrorLog.objects.all()
    serializer_class = ErrorLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['error_type', 'resolved', 'user_phone']
    
    def get_queryset(self):
        """Filter by date range if provided"""
        queryset = super().get_queryset()
        
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset
    
    @action(detail=True, methods=['patch'])
    def resolve(self, request, pk=None):
        """Mark error as resolved"""
        error_log = self.get_object()
        notes = request.data.get('resolution_notes', '')
        
        error_log.resolve(notes)
        
        return Response({
            'message': 'Error marked as resolved',
            'resolution_notes': notes
        })
```

---

## 🔐 **Authentication & Permissions**

### **Custom Permissions**

```python
# core/permissions.py
from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects.
    """
    
    def has_permission(self, request, view):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions only for admin users
        return request.user.is_authenticated and request.user.is_staff

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners or admins to access objects.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin users can access everything
        if request.user.is_staff:
            return True
        
        # Users can only access their own objects
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'user_phone'):
            return obj.user_phone.phone_number == getattr(request.user, 'phone_number', None)
        
        return False

class RateLimitPermission(permissions.BasePermission):
    """
    Permission class to enforce rate limiting.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Admin users are not rate limited
        if request.user.is_staff:
            return True
        
        # Check rate limit for regular users
        if hasattr(request.user, 'can_make_request'):
            return request.user.can_make_request()
        
        return True
```

### **Authentication Configuration**

```python
# sms_agent/settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

---

## 📊 **Django Admin Configuration**

### **Advanced Admin Interface**

```python
# core/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from .models import User, Task, ErrorLog

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Enhanced user admin interface"""
    
    list_display = [
        'phone_number', 'tier', 'full_name', 'email',
        'total_requests', 'monthly_requests', 'is_active',
        'last_active', 'created_at'
    ]
    list_filter = ['tier', 'is_active', 'created_at', 'last_active']
    search_fields = ['phone_number', 'email', 'full_name']
    readonly_fields = ['created_at', 'updated_at', 'last_active']
    
    fieldsets = (
        (None, {
            'fields': ('phone_number', 'tier', 'is_active')
        }),
        ('Personal Information', {
            'fields': ('full_name', 'email', 'timezone')
        }),
        ('Usage Statistics', {
            'fields': ('total_requests', 'monthly_requests', 'rate_limit_reset'),
            'classes': ('collapse',)
        }),
        ('Preferences', {
            'fields': ('preferences',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_active'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['reset_monthly_requests', 'upgrade_to_premium', 'downgrade_to_free']
    
    def reset_monthly_requests(self, request, queryset):
        """Reset monthly requests for selected users"""
        count = queryset.update(monthly_requests=0)
        self.message_user(request, f'Reset monthly requests for {count} users.')
    reset_monthly_requests.short_description = "Reset monthly requests"
    
    def upgrade_to_premium(self, request, queryset):
        """Upgrade selected users to premium"""
        count = queryset.update(tier='premium')
        self.message_user(request, f'Upgraded {count} users to premium.')
    upgrade_to_premium.short_description = "Upgrade to premium"
    
    def downgrade_to_free(self, request, queryset):
        """Downgrade selected users to free"""
        count = queryset.update(tier='free')
        self.message_user(request, f'Downgraded {count} users to free.')
    downgrade_to_free.short_description = "Downgrade to free"

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Enhanced task admin interface"""
    
    list_display = [
        'id', 'user_phone_display', 'category', 'success',
        'processing_time', 'tokens_used', 'created_at'
    ]
    list_filter = ['category', 'success', 'created_at', 'user_phone__tier']
    search_fields = ['user_phone__phone_number', 'sms_content', 'ai_response']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('id', 'user_phone', 'category', 'success')
        }),
        ('Content', {
            'fields': ('sms_content', 'ai_response')
        }),
        ('Performance Metrics', {
            'fields': ('processing_time', 'tokens_used', 'complexity_score'),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_phone_display(self, obj):
        """Display user phone with link to user admin"""
        url = reverse('admin:core_user_change', args=[obj.user_phone.phone_number])
        return format_html('<a href="{}">{}</a>', url, obj.user_phone.phone_number)
    user_phone_display.short_description = 'User Phone'
    user_phone_display.admin_order_field = 'user_phone__phone_number'
    
    def get_queryset(self, request):
        """Optimize queries with select_related"""
        return super().get_queryset(request).select_related('user_phone')

@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    """Enhanced error log admin interface"""
    
    list_display = [
        'id', 'error_type', 'user_phone_display', 'resolved',
        'timestamp'
    ]
    list_filter = ['error_type', 'resolved', 'timestamp']
    search_fields = ['error_message', 'user_phone__phone_number']
    readonly_fields = ['id', 'timestamp']
    
    fieldsets = (
        (None, {
            'fields': ('id', 'error_type', 'user_phone', 'task', 'resolved')
        }),
        ('Error Details', {
            'fields': ('error_message', 'stack_trace')
        }),
        ('Resolution', {
            'fields': ('resolution_notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_resolved', 'mark_unresolved']
    
    def user_phone_display(self, obj):
        """Display user phone with link to user admin"""
        if obj.user_phone:
            url = reverse('admin:core_user_change', args=[obj.user_phone.phone_number])
            return format_html('<a href="{}">{}</a>', url, obj.user_phone.phone_number)
        return '-'
    user_phone_display.short_description = 'User Phone'
    user_phone_display.admin_order_field = 'user_phone__phone_number'
    
    def mark_resolved(self, request, queryset):
        """Mark selected errors as resolved"""
        count = queryset.update(resolved=True)
        self.message_user(request, f'Marked {count} errors as resolved.')
    mark_resolved.short_description = "Mark as resolved"
    
    def mark_unresolved(self, request, queryset):
        """Mark selected errors as unresolved"""
        count = queryset.update(resolved=False)
        self.message_user(request, f'Marked {count} errors as unresolved.')
    mark_unresolved.short_description = "Mark as unresolved"

# Custom admin site configuration
admin.site.site_header = "SMS-to-AI Agent Administration"
admin.site.site_title = "SMS-to-AI Agent Admin"
admin.site.index_title = "Welcome to SMS-to-AI Agent Administration"
```

---

## 🎯 **Django Signals**

### **Signal Handlers**

```python
# core/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import User, Task, ErrorLog
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def user_created_handler(sender, instance, created, **kwargs):
    """Handle user creation"""
    if created:
        logger.info(f"New user created: {instance.phone_number} ({instance.tier})")
        # Send welcome message or perform other initialization

@receiver(pre_save, sender=User)
def user_tier_change_handler(sender, instance, **kwargs):
    """Handle user tier changes"""
    if instance.pk:  # Only for existing users
        try:
            old_instance = User.objects.get(pk=instance.pk)
            if old_instance.tier != instance.tier:
                logger.info(
                    f"User {instance.phone_number} tier changed: "
                    f"{old_instance.tier} -> {instance.tier}"
                )
                # Reset monthly requests on tier upgrade
                if instance.tier in ['premium', 'enterprise']:
                    instance.monthly_requests = 0
        except User.DoesNotExist:
            pass

@receiver(post_save, sender=Task)
def task_completed_handler(sender, instance, created, **kwargs):
    """Handle task completion"""
    if not created and instance.completed_at and instance.success:
        # Update user activity
        instance.user_phone.update_activity()
        logger.info(
            f"Task {instance.id} completed for {instance.user_phone.phone_number} "
            f"in {instance.processing_time}s"
        )

@receiver(post_save, sender=ErrorLog)
def error_logged_handler(sender, instance, created, **kwargs):
    """Handle error logging"""
    if created:
        logger.error(
            f"New error logged: {instance.error_type} - {instance.error_message}"
        )
        # Send alert to administrators for critical errors
        if instance.error_type in ['database_error', 'system_error']:
            # Send notification (implement notification service)
            pass
```

---

## 🧪 **Testing**

### **Model Tests**

```python
# core/tests/test_models.py
from django.test import TestCase
from django.utils import timezone
from core.models import User, Task, ErrorLog

class UserModelTests(TestCase):
    """Test cases for User model"""
    
    def setUp(self):
        self.user = User.objects.create(
            phone_number='+1234567890',
            tier='free',
            email='test@example.com'
        )
    
    def test_user_creation(self):
        """Test user creation"""
        self.assertEqual(self.user.phone_number, '+1234567890')
        self.assertEqual(self.user.tier, 'free')
        self.assertTrue(self.user.is_active)
        self.assertEqual(self.user.total_requests, 0)
    
    def test_update_activity(self):
        """Test activity update"""
        old_requests = self.user.total_requests
        self.user.update_activity()
        self.assertEqual(self.user.total_requests, old_requests + 1)
    
    def test_can_make_request(self):
        """Test rate limiting"""
        # Free tier should allow requests initially
        self.assertTrue(self.user.can_make_request())
        
        # Exceed rate limit
        self.user.monthly_requests = 100  # Assuming free limit is lower
        self.assertFalse(self.user.can_make_request())

class TaskModelTests(TestCase):
    """Test cases for Task model"""
    
    def setUp(self):
        self.user = User.objects.create(
            phone_number='+1234567890',
            tier='premium'
        )
        self.task = Task.objects.create(
            user_phone=self.user,
            sms_content="Test message",
            category="general"
        )
    
    def test_task_creation(self):
        """Test task creation"""
        self.assertEqual(self.task.user_phone, self.user)
        self.assertEqual(self.task.category, "general")
        self.assertTrue(self.task.success)
        self.assertIsNone(self.task.completed_at)
    
    def test_mark_completed(self):
        """Test task completion"""
        response = "Test response"
        processing_time = 2.5
        tokens_used = 100
        
        self.task.mark_completed(response, processing_time, tokens_used)
        
        self.assertEqual(self.task.ai_response, response)
        self.assertEqual(self.task.processing_time, processing_time)
        self.assertEqual(self.task.tokens_used, tokens_used)
        self.assertTrue(self.task.success)
        self.assertIsNotNone(self.task.completed_at)
    
    def test_mark_failed(self):
        """Test task failure"""
        error_message = "Test error"
        
        self.task.mark_failed(error_message)
        
        self.assertEqual(self.task.error_message, error_message)
        self.assertFalse(self.task.success)
        self.assertIsNotNone(self.task.completed_at)
```

### **API Tests**

```python
# core/tests/test_api.py
from django.test import TestCase
from django.contrib.auth.models import User as AuthUser
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from rest_framework import status
from core.models import User, Task

class UserAPITests(APITestCase):
    """Test cases for User API"""
    
    def setUp(self):
        # Create admin user for authentication
        self.admin_user = AuthUser.objects.create_user(
            username='admin',
            password='testpass',
            is_staff=True
        )
        self.token = Token.objects.create(user=self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Create test user
        self.user = User.objects.create(
            phone_number='+1234567890',
            tier='free',
            email='test@example.com'
        )
    
    def test_list_users(self):
        """Test listing users"""
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_get_user_detail(self):
        """Test getting user details"""
        response = self.client.get(f'/api/users/{self.user.phone_number}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone_number'], self.user.phone_number)
    
    def test_update_user_tier(self):
        """Test updating user tier"""
        data = {'tier': 'premium', 'reason': 'Test upgrade'}
        response = self.client.post(
            f'/api/users/{self.user.phone_number}/update_tier/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.tier, 'premium')

class TaskAPITests(APITestCase):
    """Test cases for Task API"""
    
    def setUp(self):
        # Create admin user for authentication
        self.admin_user = AuthUser.objects.create_user(
            username='admin',
            password='testpass',
            is_staff=True
        )
        self.token = Token.objects.create(user=self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Create test user and task
        self.user = User.objects.create(
            phone_number='+1234567890',
            tier='premium'
        )
        self.task = Task.objects.create(
            user_phone=self.user,
            sms_content="Test message",
            category="general"
        )
    
    def test_list_tasks(self):
        """Test listing tasks"""
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_task(self):
        """Test creating a task"""
        data = {
            'user_phone': self.user.phone_number,
            'sms_content': 'New test message',
            'category': 'coding'
        }
        response = self.client.post('/api/tasks/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 2)
    
    def test_task_analytics(self):
        """Test task analytics endpoint"""
        response = self.client.get('/api/tasks/analytics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_tasks', response.data)
        self.assertIn('success_rate', response.data)
```

---

## 🔗 **Related Documentation**

- **[Architecture Guide](ARCHITECTURE.md)** - System architecture overview
- **[Database Guide](DATABASE.md)** - Database schema and operations
- **[API Reference](../user-guides/API_REFERENCE.md)** - REST API documentation
- **[Configuration Guide](../getting-started/CONFIGURATION.md)** - Django settings configuration

---

**🐍 Your Django implementation is now complete with models, serializers, views, admin interface, and comprehensive testing!** 