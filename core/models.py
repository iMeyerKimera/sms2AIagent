from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
import json


class User(models.Model):
    """User model for SMS agent users"""
    
    TIER_CHOICES = [
        ('free', 'Free'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        primary_key=True,
        help_text="Primary phone number for the user"
    )
    tier = models.CharField(
        max_length=20,
        choices=TIER_CHOICES,
        default='free',
        help_text="User subscription tier"
    )
    email = models.EmailField(
        max_length=255,
        blank=True,
        null=True,
        help_text="User email address"
    )
    full_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="User full name"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Account creation timestamp"
    )
    last_active = models.DateTimeField(
        default=timezone.now,
        help_text="Last activity timestamp"
    )
    total_requests = models.IntegerField(
        default=0,
        help_text="Total number of requests made"
    )
    monthly_requests = models.IntegerField(
        default=0,
        help_text="Requests made this month"
    )
    rate_limit_reset = models.DateTimeField(
        default=timezone.now,
        help_text="When rate limit resets"
    )
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="User timezone"
    )
    preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="User preferences stored as JSON"
    )
    
    class Meta:
        db_table = 'users'
        ordering = ['-last_active']
        
    def __str__(self):
        return f"{self.phone_number} ({self.tier})"
    
    @property
    def rate_limit(self):
        """Get rate limit based on tier"""
        limits = {
            'free': 10,
            'premium': 100,
            'enterprise': 1000
        }
        return limits.get(self.tier, 10)
    
    def increment_requests(self):
        """Increment request counters"""
        self.total_requests += 1
        self.monthly_requests += 1
        self.last_active = timezone.now()
        self.save(update_fields=['total_requests', 'monthly_requests', 'last_active'])


class Task(models.Model):
    """Task model for tracking SMS processing tasks"""
    
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('support', 'Support'),
        ('information', 'Information'),
        ('emergency', 'Emergency'),
        ('automated', 'Automated'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    user_phone = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text="User who initiated the task"
    )
    sms_content = models.TextField(
        help_text="Original SMS content"
    )
    ai_response = models.TextField(
        blank=True,
        null=True,
        help_text="AI-generated response"
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='general',
        help_text="Task category"
    )
    processing_time = models.FloatField(
        default=0.0,
        help_text="Processing time in seconds"
    )
    tokens_used = models.IntegerField(
        default=0,
        help_text="Number of tokens used for AI processing"
    )
    complexity_score = models.FloatField(
        default=1.0,
        help_text="Complexity score of the task"
    )
    success = models.BooleanField(
        default=True,
        help_text="Whether the task was successful"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if task failed"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Task creation timestamp"
    )
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Task completion timestamp"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional task metadata"
    )
    
    class Meta:
        db_table = 'tasks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_phone', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['success', '-created_at']),
        ]
    
    def __str__(self):
        return f"Task {self.id} - {self.user_phone} ({self.category})"
    
    def mark_completed(self, success=True, error_message=None):
        """Mark task as completed"""
        self.completed_at = timezone.now()
        self.success = success
        if error_message:
            self.error_message = error_message
        self.processing_time = (self.completed_at - self.created_at).total_seconds()
        self.save(update_fields=['completed_at', 'success', 'error_message', 'processing_time'])


class ErrorLog(models.Model):
    """Error log model for tracking system errors"""
    
    ERROR_TYPE_CHOICES = [
        ('sms_error', 'SMS Error'),
        ('ai_error', 'AI Processing Error'),
        ('database_error', 'Database Error'),
        ('api_error', 'API Error'),
        ('validation_error', 'Validation Error'),
        ('rate_limit_error', 'Rate Limit Error'),
        ('system_error', 'System Error'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    user_phone = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='error_logs',
        help_text="User associated with the error (if any)"
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='error_logs',
        help_text="Task associated with the error (if any)"
    )
    error_type = models.CharField(
        max_length=50,
        choices=ERROR_TYPE_CHOICES,
        help_text="Type of error"
    )
    error_message = models.TextField(
        help_text="Detailed error message"
    )
    stack_trace = models.TextField(
        blank=True,
        null=True,
        help_text="Stack trace for debugging"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When the error occurred"
    )
    resolved = models.BooleanField(
        default=False,
        help_text="Whether the error has been resolved"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional error metadata"
    )
    
    class Meta:
        db_table = 'error_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['error_type', '-timestamp']),
            models.Index(fields=['user_phone', '-timestamp']),
            models.Index(fields=['resolved', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.error_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @classmethod
    def log_error(cls, error_type, error_message, user_phone=None, task=None, stack_trace=None, **metadata):
        """Convenience method to log errors"""
        return cls.objects.create(
            user_phone=user_phone,
            task=task,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            metadata=metadata
        ) 