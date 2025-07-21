from rest_framework import serializers
from .models import User, Task, ErrorLog


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    rate_limit = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'phone_number', 'tier', 'email', 'full_name', 
            'created_at', 'last_active', 'total_requests', 
            'monthly_requests', 'rate_limit_reset', 'timezone', 
            'preferences', 'rate_limit'
        ]
        read_only_fields = ['created_at', 'total_requests', 'monthly_requests', 'rate_limit_reset']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users"""
    
    class Meta:
        model = User
        fields = ['phone_number', 'tier', 'email', 'full_name', 'timezone', 'preferences']


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model"""
    user_phone = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'user_phone', 'sms_content', 'ai_response', 
            'category', 'processing_time', 'tokens_used', 
            'complexity_score', 'success', 'error_message', 
            'created_at', 'completed_at', 'metadata'
        ]
        read_only_fields = ['id', 'created_at', 'completed_at', 'processing_time']


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new tasks"""
    
    class Meta:
        model = Task
        fields = ['user_phone', 'sms_content', 'category', 'metadata']


class ErrorLogSerializer(serializers.ModelSerializer):
    """Serializer for ErrorLog model"""
    user_phone = serializers.StringRelatedField(read_only=True)
    task = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = ErrorLog
        fields = [
            'id', 'user_phone', 'task', 'error_type', 
            'error_message', 'stack_trace', 'timestamp', 
            'resolved', 'metadata'
        ]
        read_only_fields = ['id', 'timestamp']


class SMSReceiveSerializer(serializers.Serializer):
    """Serializer for incoming SMS webhook data"""
    From = serializers.CharField(max_length=20)
    Body = serializers.CharField()
    MessageSid = serializers.CharField(required=False)
    AccountSid = serializers.CharField(required=False)
    
    
class SMSSendSerializer(serializers.Serializer):
    """Serializer for outgoing SMS data"""
    to = serializers.CharField(max_length=20)
    message = serializers.CharField()
    from_number = serializers.CharField(max_length=20, required=False)


class AnalyticsOverviewSerializer(serializers.Serializer):
    """Serializer for analytics overview data"""
    total_users = serializers.IntegerField()
    total_tasks = serializers.IntegerField()
    tasks_24h = serializers.IntegerField()
    active_users = serializers.IntegerField()
    success_rate = serializers.FloatField()
    avg_processing_time = serializers.FloatField()
    recent_errors = serializers.IntegerField()
    timestamp = serializers.DateTimeField()


class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics"""
    total_users = serializers.IntegerField()
    free_users = serializers.IntegerField()
    premium_users = serializers.IntegerField()
    enterprise_users = serializers.IntegerField()
    new_users_week = serializers.IntegerField()
    new_users_month = serializers.IntegerField()
    active_24h = serializers.IntegerField()
    active_7d = serializers.IntegerField()
    active_30d = serializers.IntegerField()


class TaskStatsSerializer(serializers.Serializer):
    """Serializer for task statistics"""
    total_tasks = serializers.IntegerField()
    successful_tasks = serializers.IntegerField()
    failed_tasks = serializers.IntegerField()
    avg_processing_time = serializers.FloatField()
    tasks_by_category = serializers.DictField()
    tasks_24h = serializers.IntegerField()
    tasks_week = serializers.IntegerField()
    tasks_month = serializers.IntegerField() 