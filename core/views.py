import os
import json
import logging
import asyncio
from datetime import datetime, timedelta

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.conf import settings
from django.db.models import Count, Q, Avg, Max, Min
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from .models import User, Task, ErrorLog
from .serializers import (
    UserSerializer, UserCreateSerializer, TaskSerializer, TaskCreateSerializer,
    ErrorLogSerializer, SMSReceiveSerializer, SMSSendSerializer,
    AnalyticsOverviewSerializer, UserStatsSerializer, TaskStatsSerializer
)

# Import AI processing modules from the original app
try:
    from cursor_agent import CursorAgent
    from task_router import TaskRouter
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

logger = logging.getLogger(__name__)

# Initialize Twilio client
try:
    twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    TWILIO_AVAILABLE = True
except Exception as e:
    logger.error(f"Failed to initialize Twilio client: {e}")
    twilio_client = None
    TWILIO_AVAILABLE = False

# Initialize AI components
if AI_AVAILABLE:
    try:
        cursor_agent = CursorAgent()
        task_router = TaskRouter()
        logger.info("AI components initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AI components: {e}")
        cursor_agent = None
        task_router = None
        AI_AVAILABLE = False


# Home endpoint
@api_view(['GET'])
@permission_classes([AllowAny])
def home(request):
    """Home endpoint providing API information"""
    return Response({
        'message': 'SMS AI Agent API',
        'version': '2.0.0',
        'status': 'running',
        'features': {
            'sms_processing': True,
            'ai_agent': AI_AVAILABLE,
            'twilio_integration': TWILIO_AVAILABLE,
            'admin_dashboard': True,
            'analytics': True
        },
        'endpoints': {
            'sms_receive': '/sms/receive',
            'sms_send': '/sms/send',
            'health': '/health',
            'admin': '/admin/',
            'api': '/api/'
        }
    })


# Health check endpoint
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint"""
    try:
        # Check database connectivity
        user_count = User.objects.count()
        
        # Check external services
        health_data = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'services': {
                'database': True,
                'twilio': TWILIO_AVAILABLE,
                'ai_processing': AI_AVAILABLE
            },
            'stats': {
                'total_users': user_count,
                'total_tasks': Task.objects.count(),
                'errors_24h': ErrorLog.objects.filter(
                    timestamp__gte=timezone.now() - timedelta(days=1)
                ).count()
            }
        }
        
        return Response(health_data)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# SMS Processing endpoints
@csrf_exempt
@require_http_methods(["POST"])
def sms_receive(request):
    """Handle incoming SMS from Twilio webhook"""
    try:
        # Parse Twilio webhook data
        from_number = request.POST.get('From', '').strip()
        message_body = request.POST.get('Body', '').strip()
        message_sid = request.POST.get('MessageSid', '')
        
        logger.info(f"Received SMS from {from_number}: {message_body}")
        
        if not from_number or not message_body:
            logger.error("Missing required SMS data")
            return HttpResponse(status=400)
        
        # Normalize phone number
        phone_number = from_number.replace('+1', '').replace('+', '')
        
        # Get or create user
        user, created = User.objects.get_or_create(
            phone_number=phone_number,
            defaults={'tier': 'free', 'last_active': timezone.now()}
        )
        
        if created:
            logger.info(f"Created new user: {phone_number}")
        
        # Check rate limits
        if not check_rate_limit(user):
            response_message = "Rate limit exceeded. Please try again later."
            send_sms_response(from_number, response_message)
            return HttpResponse(str(MessagingResponse()))
        
        # Create task
        task = Task.objects.create(
            user_phone=user,
            sms_content=message_body,
            category='general',
            metadata={'message_sid': message_sid}
        )
        
        # Process the message asynchronously if AI is available
        if AI_AVAILABLE and cursor_agent:
            try:
                ai_response = process_with_ai(message_body, user, task)
                task.ai_response = ai_response
                task.mark_completed(success=True)
                
                # Send response back to user
                send_sms_response(from_number, ai_response)
                
            except Exception as e:
                logger.error(f"AI processing failed: {e}")
                error_response = "Sorry, I'm having trouble processing your request right now. Please try again later."
                task.mark_completed(success=False, error_message=str(e))
                send_sms_response(from_number, error_response)
                
                # Log the error
                ErrorLog.log_error(
                    error_type='ai_error',
                    error_message=str(e),
                    user_phone=user,
                    task=task
                )
        else:
            # Fallback response when AI is not available
            fallback_response = "Thank you for your message. AI processing is currently unavailable."
            task.ai_response = fallback_response
            task.mark_completed(success=True)
            send_sms_response(from_number, fallback_response)
        
        # Update user stats
        user.increment_requests()
        
        return HttpResponse(str(MessagingResponse()))
        
    except Exception as e:
        logger.error(f"Error processing SMS: {e}")
        ErrorLog.log_error(
            error_type='sms_error',
            error_message=str(e)
        )
        return HttpResponse(status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def sms_send(request):
    """Send SMS endpoint"""
    try:
        serializer = SMSSendSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        to_number = data['to']
        message = data['message']
        from_number = data.get('from_number', settings.TWILIO_PHONE_NUMBER)
        
        if not TWILIO_AVAILABLE:
            return Response(
                {'error': 'SMS service unavailable'}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Send SMS via Twilio
        message_response = twilio_client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        
        return Response({
            'success': True,
            'message_sid': message_response.sid,
            'status': message_response.status
        })
        
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        return Response(
            {'error': 'Failed to send SMS'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# User Management endpoints
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Register a new user"""
    try:
        serializer = UserCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.save()
        response_serializer = UserSerializer(user)
        
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        return Response(
            {'error': 'Failed to register user'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'PUT'])
@permission_classes([AllowAny])
def user_profile(request, phone_number):
    """Get or update user profile"""
    try:
        user = get_object_or_404(User, phone_number=phone_number)
        
        if request.method == 'GET':
            serializer = UserSerializer(user)
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            serializer = UserSerializer(user, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return Response(serializer.data)
            
    except Exception as e:
        logger.error(f"Error with user profile: {e}")
        return Response(
            {'error': 'Failed to process user profile'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def user_tasks(request, phone_number):
    """Get user's tasks"""
    try:
        user = get_object_or_404(User, phone_number=phone_number)
        tasks = Task.objects.filter(user_phone=user).order_by('-created_at')
        
        # Pagination
        paginator = PageNumberPagination()
        paginated_tasks = paginator.paginate_queryset(tasks, request)
        
        serializer = TaskSerializer(paginated_tasks, many=True)
        return paginator.get_paginated_response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting user tasks: {e}")
        return Response(
            {'error': 'Failed to get user tasks'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Task Processing endpoints
@api_view(['POST'])
@permission_classes([AllowAny])
def process_task(request):
    """Process a task manually"""
    try:
        serializer = TaskCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        task = serializer.save()
        
        # Process with AI if available
        if AI_AVAILABLE and cursor_agent:
            try:
                ai_response = process_with_ai(
                    task.sms_content, 
                    task.user_phone, 
                    task
                )
                task.ai_response = ai_response
                task.mark_completed(success=True)
            except Exception as e:
                task.mark_completed(success=False, error_message=str(e))
        
        response_serializer = TaskSerializer(task)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error processing task: {e}")
        return Response(
            {'error': 'Failed to process task'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def task_status(request, task_id):
    """Get task status"""
    try:
        task = get_object_or_404(Task, id=task_id)
        serializer = TaskSerializer(task)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        return Response(
            {'error': 'Failed to get task status'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Analytics endpoints
@api_view(['GET'])
@permission_classes([AllowAny])
def analytics_overview(request):
    """Get analytics overview"""
    try:
        total_users = User.objects.count()
        total_tasks = Task.objects.count()
        
        yesterday = timezone.now() - timedelta(days=1)
        week_ago = timezone.now() - timedelta(days=7)
        
        tasks_24h = Task.objects.filter(created_at__gte=yesterday).count()
        active_users = User.objects.filter(last_active__gte=week_ago).count()
        
        successful_tasks = Task.objects.filter(success=True).count()
        success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        avg_processing_time = Task.objects.aggregate(
            avg_time=Avg('processing_time')
        )['avg_time'] or 0
        
        recent_errors = ErrorLog.objects.filter(timestamp__gte=yesterday).count()
        
        data = {
            'total_users': total_users,
            'total_tasks': total_tasks,
            'tasks_24h': tasks_24h,
            'active_users': active_users,
            'success_rate': round(success_rate, 2),
            'avg_processing_time': round(avg_processing_time, 2),
            'recent_errors': recent_errors,
            'timestamp': timezone.now()
        }
        
        serializer = AnalyticsOverviewSerializer(data)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}")
        return Response(
            {'error': 'Failed to get analytics overview'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def user_statistics(request):
    """Get user statistics"""
    try:
        yesterday = timezone.now() - timedelta(days=1)
        week_ago = timezone.now() - timedelta(days=7)
        month_ago = timezone.now() - timedelta(days=30)
        
        data = {
            'total_users': User.objects.count(),
            'free_users': User.objects.filter(tier='free').count(),
            'premium_users': User.objects.filter(tier='premium').count(),
            'enterprise_users': User.objects.filter(tier='enterprise').count(),
            'new_users_week': User.objects.filter(created_at__gte=week_ago).count(),
            'new_users_month': User.objects.filter(created_at__gte=month_ago).count(),
            'active_24h': User.objects.filter(last_active__gte=yesterday).count(),
            'active_7d': User.objects.filter(last_active__gte=week_ago).count(),
            'active_30d': User.objects.filter(last_active__gte=month_ago).count()
        }
        
        serializer = UserStatsSerializer(data)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting user statistics: {e}")
        return Response(
            {'error': 'Failed to get user statistics'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def task_statistics(request):
    """Get task statistics"""
    try:
        yesterday = timezone.now() - timedelta(days=1)
        week_ago = timezone.now() - timedelta(days=7)
        month_ago = timezone.now() - timedelta(days=30)
        
        total_tasks = Task.objects.count()
        successful_tasks = Task.objects.filter(success=True).count()
        
        # Task counts by category
        tasks_by_category = dict(
            Task.objects.values('category')
            .annotate(count=Count('id'))
            .values_list('category', 'count')
        )
        
        data = {
            'total_tasks': total_tasks,
            'successful_tasks': successful_tasks,
            'failed_tasks': total_tasks - successful_tasks,
            'avg_processing_time': Task.objects.aggregate(
                avg_time=Avg('processing_time')
            )['avg_time'] or 0,
            'tasks_by_category': tasks_by_category,
            'tasks_24h': Task.objects.filter(created_at__gte=yesterday).count(),
            'tasks_week': Task.objects.filter(created_at__gte=week_ago).count(),
            'tasks_month': Task.objects.filter(created_at__gte=month_ago).count()
        }
        
        serializer = TaskStatsSerializer(data)
        return Response(serializer.data)
        
    except Exception as e:
        logger.error(f"Error getting task statistics: {e}")
        return Response(
            {'error': 'Failed to get task statistics'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# REST API ViewSets
class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    lookup_field = 'phone_number'


class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet for Task model"""
    queryset = Task.objects.all().order_by('-created_at')
    serializer_class = TaskSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = Task.objects.all().order_by('-created_at')
        user_phone = self.request.query_params.get('user_phone')
        if user_phone:
            queryset = queryset.filter(user_phone__phone_number=user_phone)
        return queryset


class ErrorLogViewSet(viewsets.ModelViewSet):
    """ViewSet for ErrorLog model"""
    queryset = ErrorLog.objects.all().order_by('-timestamp')
    serializer_class = ErrorLogSerializer
    permission_classes = [AllowAny]


# Helper functions
def check_rate_limit(user):
    """Check if user has exceeded rate limit"""
    try:
        now = timezone.now()
        
        # Reset monthly counter if needed
        if user.rate_limit_reset <= now:
            user.monthly_requests = 0
            # Set next reset to next month
            if now.month == 12:
                user.rate_limit_reset = now.replace(year=now.year + 1, month=1, day=1)
            else:
                user.rate_limit_reset = now.replace(month=now.month + 1, day=1)
            user.save()
        
        # Check if under limit
        return user.monthly_requests < user.rate_limit
        
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}")
        return True  # Allow on error


def send_sms_response(to_number, message):
    """Send SMS response via Twilio"""
    if not TWILIO_AVAILABLE:
        logger.warning("Twilio not available, cannot send SMS")
        return False
    
    try:
        twilio_client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_number
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        return False


def process_with_ai(message, user, task):
    """Process message with AI"""
    if not AI_AVAILABLE:
        raise Exception("AI processing not available")
    
    try:
        start_time = timezone.now()
        
        # Route the task
        if task_router:
            route_result = task_router.route_task(message, user.tier)
            task.category = route_result.get('category', 'general')
            task.complexity_score = route_result.get('complexity', 1.0)
        
        # Process with cursor agent
        ai_result = cursor_agent.create_task(message)
        if ai_result.get('success', False):
            response = ai_result.get('response', 'No response generated')
        else:
            raise Exception(ai_result.get('error', 'AI processing failed'))
        
        # Calculate processing time
        end_time = timezone.now()
        task.processing_time = (end_time - start_time).total_seconds()
        task.save()
        
        return response
        
    except Exception as e:
        logger.error(f"AI processing error: {e}")
        raise 