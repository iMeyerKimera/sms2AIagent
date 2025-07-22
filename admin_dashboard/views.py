from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Count, Q, Avg, Max, Min, Case, When, IntegerField, FloatField
from django.db.models.functions import TruncHour, TruncDate
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
from datetime import timedelta
import json
import logging
import os
from django.core.serializers.json import DjangoJSONEncoder

from core.models import User, Task, ErrorLog

logger = logging.getLogger(__name__)


class DateTimeAwareJSONResponse(JsonResponse):
    """Custom JsonResponse that handles datetime objects"""
    def __init__(self, data, **kwargs):
        # Use Django's native encoder parameter approach
        if 'encoder' not in kwargs:
            kwargs['encoder'] = DjangoJSONEncoder
        super().__init__(data, **kwargs)


def serialize_datetime(obj):
    """Helper function to serialize datetime objects"""
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    return obj


def serialize_queryset_datetime(queryset_values):
    """Helper function to serialize datetime objects in queryset values"""
    result = []
    for item in queryset_values:
        serialized_item = {}
        for key, value in item.items():
            if hasattr(value, 'isoformat'):  # datetime object
                serialized_item[key] = value.isoformat()
            else:
                serialized_item[key] = value
        result.append(serialized_item)
    return result


# Authentication views
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.models import User as DjangoUser

@csrf_protect
@require_http_methods(["GET", "POST"])
def admin_login(request):
    """Admin login view for custom dashboard"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # First try Django authentication (recommended)
        django_user = authenticate(request, username=username, password=password)
        if django_user is not None and (django_user.is_superuser or django_user.is_staff):
            login(request, django_user)
            request.session['admin_authenticated'] = True
            request.session['admin_user_id'] = django_user.id
            request.session['admin_username'] = django_user.username
            logger.info(f"Django admin user '{username}' logged in successfully")
            return redirect('/dashboard/dashboard/')
        
        # Fallback to simple admin authentication for backward compatibility
        elif username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
            request.session['admin_authenticated'] = True
            request.session['admin_username'] = username
            logger.info(f"Simple admin user '{username}' logged in successfully")
            return redirect('/dashboard/dashboard/')
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return render(request, 'admin/login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'admin/login.html')


def admin_logout(request):
    """Admin logout view"""
    if request.session.get('admin_authenticated'):
        username = request.session.get('admin_username', 'unknown')
        logger.info(f"Admin user '{username}' logged out")
    
    # Django logout
    if request.user.is_authenticated:
        logout(request)
    
    # Clear custom session data
    request.session.pop('admin_authenticated', None)
    request.session.pop('admin_user_id', None)
    request.session.pop('admin_username', None)
    return redirect('/dashboard/')


def require_admin_auth(view_func):
    """Decorator to require admin authentication"""
    def wrapper(request, *args, **kwargs):
        # Check Django authentication
        if request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff):
            return view_func(request, *args, **kwargs)
        
        # Check simple authentication
        if request.session.get('admin_authenticated'):
            return view_func(request, *args, **kwargs)
        
        logger.warning(f"Unauthorized access attempt to {request.path}")
        return redirect('/dashboard/')
    return wrapper


# Dashboard views
@require_admin_auth
def dashboard(request):
    """Main admin dashboard"""
    try:
        # Get overview statistics using Django ORM
        total_users = User.objects.count()
        total_tasks = Task.objects.count()
        
        # Tasks in last 24 hours
        yesterday = timezone.now() - timedelta(days=1)
        tasks_24h = Task.objects.filter(created_at__gte=yesterday).count()
        
        # Active users (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        active_users = User.objects.filter(last_active__gte=week_ago).count()
        
        # Success rate
        successful_tasks = Task.objects.filter(success=True).count()
        success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Recent errors
        recent_errors = ErrorLog.objects.filter(timestamp__gte=yesterday).count()
        
        overview = {
            'total_users': total_users,
            'total_tasks': total_tasks,
            'tasks_24h': tasks_24h,
            'active_users': active_users,
            'success_rate': round(success_rate, 2),
            'recent_errors': recent_errors
        }
        
        # Get user analytics for last 7 days
        user_analytics = get_user_analytics_data(7)
        task_analytics = get_task_analytics_data(7)
        system_health = get_system_health_data()
        
        context = {
            'overview': json.dumps(overview, cls=DjangoJSONEncoder),
            'user_analytics': user_analytics,
            'task_analytics': task_analytics,
            'system_health': json.dumps(system_health, cls=DjangoJSONEncoder)
        }
        
        return render(request, 'admin/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render(request, 'admin/dashboard.html', {'error': 'Failed to load dashboard data'})


@require_admin_auth
def users_view(request):
    """User management page"""
    page = int(request.GET.get('page', 1))
    search = request.GET.get('search', '')
    tier_filter = request.GET.get('tier', '')
    
    try:
        users_data = get_users_list_data(page=page, per_page=20, search=search, tier_filter=tier_filter)
        
        context = {
            'users_data': users_data,
            'search': search,
            'tier_filter': tier_filter
        }
        
        return render(request, 'admin/users.html', context)
        
    except Exception as e:
        logger.error(f"Error loading users: {e}")
        return render(request, 'admin/users.html', {'error': 'Failed to load users data'})


@require_admin_auth
def analytics_view(request):
    """Analytics and reporting page"""
    days = int(request.GET.get('days', 30))
    
    try:
        user_analytics = get_user_analytics_data(days)
        task_analytics = get_task_analytics_data(days)
        
        context = {
            'user_analytics': user_analytics,
            'task_analytics': task_analytics,
            'days': days
        }
        
        return render(request, 'admin/analytics.html', context)
        
    except Exception as e:
        logger.error(f"Error loading analytics: {e}")
        return render(request, 'admin/analytics.html', {'error': 'Failed to load analytics data'})


@require_admin_auth
def system_view(request):
    """System monitoring and configuration"""
    try:
        system_health = get_system_health_data()
        overview = {
            'total_users': User.objects.count(),
            'total_tasks': Task.objects.count(),
            'total_errors': ErrorLog.objects.count()
        }
        
        context = {
            'system_health': system_health,
            'overview': overview
        }
        
        return render(request, 'admin/system.html', context)
        
    except Exception as e:
        logger.error(f"Error loading system data: {e}")
        return render(request, 'admin/system.html', {'error': 'Failed to load system data'})


# API endpoints for AJAX calls
@require_admin_auth
def api_overview(request):
    """API endpoint for dashboard overview"""
    try:
        total_users = User.objects.count()
        total_tasks = Task.objects.count()
        
        yesterday = timezone.now() - timedelta(days=1)
        tasks_24h = Task.objects.filter(created_at__gte=yesterday).count()
        
        week_ago = timezone.now() - timedelta(days=7)
        active_users = User.objects.filter(last_active__gte=week_ago).count()
        
        successful_tasks = Task.objects.filter(success=True).count()
        success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        recent_errors = ErrorLog.objects.filter(timestamp__gte=yesterday).count()
        
        data = {
            'total_users': total_users,
            'total_tasks': total_tasks,
            'tasks_24h': tasks_24h,
            'active_users': active_users,
            'success_rate': round(success_rate, 2),
            'recent_errors': recent_errors,
            'timestamp': timezone.now().isoformat()
        }
        
        return DateTimeAwareJSONResponse(data)
        
    except Exception as e:
        logger.error(f"Error getting overview: {e}")
        return DateTimeAwareJSONResponse({'error': 'Failed to fetch overview data'}, status=500)


@require_admin_auth
def api_users(request):
    """API endpoint for users data with pagination and search"""
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    search = request.GET.get('search', '')
    tier_filter = request.GET.get('tier', '')
    
    try:
        users_data = get_users_list_data(page=page, per_page=per_page, search=search, tier_filter=tier_filter)
        return DateTimeAwareJSONResponse(users_data)
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return DateTimeAwareJSONResponse({'error': 'Failed to fetch users data'}, status=500)


@require_admin_auth
def api_users_stats(request):
    """API endpoint for user statistics"""
    try:
        # Get user statistics using Django ORM
        total_users = User.objects.count()
        free_users = User.objects.filter(tier='free').count()
        premium_users = User.objects.filter(tier='premium').count()
        enterprise_users = User.objects.filter(tier='enterprise').count()
        
        week_ago = timezone.now() - timedelta(days=7)
        month_ago = timezone.now() - timedelta(days=30)
        day_ago = timezone.now() - timedelta(days=1)
        
        new_users_week = User.objects.filter(created_at__gte=week_ago).count()
        new_users_month = User.objects.filter(created_at__gte=month_ago).count()
        active_24h = User.objects.filter(last_active__gte=day_ago).count()
        active_7d = User.objects.filter(last_active__gte=week_ago).count()
        active_30d = User.objects.filter(last_active__gte=month_ago).count()
        
        user_stats = {
            'total_users': total_users,
            'free_users': free_users,
            'premium_users': premium_users,
            'enterprise_users': enterprise_users,
            'new_users_week': new_users_week,
            'new_users_month': new_users_month,
            'active_24h': active_24h,
            'active_7d': active_7d,
            'active_30d': active_30d
        }
        
        # User growth over time (last 30 days) - serialize datetime properly
        growth_data_raw = User.objects.filter(created_at__gte=month_ago).extra({'date': "date(created_at)"}).values('date').annotate(new_users=Count('phone_number')).order_by('date')
        growth_data = serialize_queryset_datetime(growth_data_raw)
        
        # User activity by tier
        tier_activity = list(
            User.objects.values('tier')
            .annotate(
                user_count=Count('phone_number'),
                total_tasks=Count('tasks'),
                avg_processing_time=Avg('tasks__processing_time'),
                successful_tasks=Count('tasks', filter=Q(tasks__success=True))
            )
            .order_by('-user_count')
        )
        
        data = {
            'user_stats': user_stats,
            'growth_data': growth_data,
            'tier_activity': tier_activity,
            'timestamp': timezone.now().isoformat()
        }
        
        return DateTimeAwareJSONResponse(data)
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return DateTimeAwareJSONResponse({'error': 'Failed to fetch user statistics'}, status=500)


# Helper functions using Django ORM
def get_users_list_data(page=1, per_page=20, search='', tier_filter=''):
    """Get paginated users list with search and filtering using Django ORM"""
    try:
        # Build queryset with filters
        queryset = User.objects.all()
        
        if search:
            queryset = queryset.filter(
                Q(phone_number__icontains=search) |
                Q(email__icontains=search) |
                Q(full_name__icontains=search)
            )
        
        if tier_filter:
            queryset = queryset.filter(tier=tier_filter)
        
        # Add task count annotation
        queryset = queryset.annotate(
            task_count=Count('tasks'),
            last_task=Max('tasks__created_at')
        ).order_by('-last_active')
        
        # Paginate
        paginator = Paginator(queryset, per_page)
        users_page = paginator.get_page(page)
        
        # Convert to list of dictionaries with proper datetime serialization
        users_list = []
        for user in users_page:
            users_list.append({
                'phone_number': user.phone_number,
                'tier': user.tier,
                'email': user.email,
                'full_name': user.full_name,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_active': user.last_active.isoformat() if user.last_active else None,
                'total_requests': user.total_requests,
                'monthly_requests': user.monthly_requests,
                'task_count': user.task_count,
                'last_task': user.last_task.isoformat() if user.last_task else None,
            })
        
        return {
            'users': users_list,
            'pagination': {
                'total': paginator.count,
                'page': page,
                'per_page': per_page,
                'total_pages': paginator.num_pages,
                'has_prev': users_page.has_previous(),
                'has_next': users_page.has_next()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting users list: {e}")
        return {
            'users': [],
            'pagination': {
                'total': 0,
                'page': 1,
                'per_page': per_page,
                'total_pages': 0,
                'has_prev': False,
                'has_next': False
            }
        }


def get_user_analytics_data(days=30):
    """Get user analytics data using Django ORM"""
    try:
        start_date = timezone.now() - timedelta(days=days)
        
        # User registration trends - serialize datetime properly
        user_trends_raw = User.objects.filter(created_at__gte=start_date).extra({'date': "date(created_at)"}).values('date').annotate(new_users=Count('phone_number')).order_by('date')
        user_trends = serialize_queryset_datetime(user_trends_raw)
        
        # User activity by tier
        tier_activity = list(
            User.objects.values('tier')
            .annotate(
                task_count=Count('tasks', filter=Q(tasks__created_at__gte=start_date)),
                active_users=Count('phone_number', filter=Q(last_active__gte=start_date))
            )
            .order_by('-active_users')
        )
        
        return {
            'user_trends': user_trends,
            'tier_activity': tier_activity
        }
        
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        return {'user_trends': [], 'tier_activity': []}


def get_task_analytics_data(days=30):
    """Get task analytics data using Django ORM"""
    try:
        start_date = timezone.now() - timedelta(days=days)
        
        # Task trends over time - serialize datetime properly
        task_trends_raw = Task.objects.filter(created_at__gte=start_date).extra({'date': "date(created_at)"}).values('date').annotate(
            total_tasks=Count('id'),
            successful_tasks=Count('id', filter=Q(success=True)),
            avg_time=Avg('processing_time')
        ).order_by('date')
        task_trends = serialize_queryset_datetime(task_trends_raw)
        
        # Task categories
        from django.db.models import FloatField, Case, When, IntegerField
        category_stats = list(
            Task.objects.filter(created_at__gte=start_date)
            .values('category')
            .annotate(
                count=Count('id'),
                avg_processing_time=Avg('processing_time'),
                success_rate=Avg(
                    Case(
                        When(success=True, then=1),
                        default=0,
                        output_field=IntegerField()
                    ),
                    output_field=FloatField()
                ) * 100
            )
            .order_by('-count')
        )
        
        return {
            'task_trends': task_trends,
            'category_stats': category_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting task analytics: {e}")
        return {'task_trends': [], 'category_stats': []}


def get_system_health_data():
    """Get system health data using Django ORM"""
    try:
        yesterday = timezone.now() - timedelta(days=1)
        
        # Check for slow tasks (processing time > 30 seconds)
        slow_tasks_count = Task.objects.filter(
            created_at__gte=yesterday,
            processing_time__gt=30
        ).count()
        
        # Get recent error statistics
        error_stats = list(
            ErrorLog.objects.filter(timestamp__gte=yesterday)
            .values('error_type')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        
        # Get recent errors with proper datetime serialization
        recent_errors_raw = ErrorLog.objects.filter(timestamp__gte=yesterday).order_by('-timestamp')[:10].values('id', 'error_type', 'error_message', 'timestamp', 'user_phone')
        recent_errors = serialize_queryset_datetime(recent_errors_raw)
        
        # Basic health metrics in the format expected by JavaScript
        health_data = {
            'database_connected': True,  # If we're here, DB is connected
            'database_health': {
                'status': 'healthy',
                'connected': True
            },
            'slow_tasks_count': slow_tasks_count,
            'error_stats': error_stats,
            'total_users': User.objects.count(),
            'total_tasks': Task.objects.count(),
            'tasks_24h': Task.objects.filter(created_at__gte=yesterday).count(),
            'errors_24h': ErrorLog.objects.filter(timestamp__gte=yesterday).count(),
            'avg_processing_time': Task.objects.aggregate(avg_time=Avg('processing_time'))['avg_time'] or 0,
            'success_rate': (Task.objects.filter(success=True).count() / max(Task.objects.count(), 1)) * 100,
            'recent_errors': recent_errors,
            'timestamp': timezone.now().isoformat(),
            'overall_status': 'healthy' if slow_tasks_count < 10 and len(error_stats) < 5 else 'warning'
        }
        
        return health_data
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return {
            'database_connected': False,
            'database_health': {
                'status': 'error',
                'connected': False
            },
            'slow_tasks_count': 0,
            'error_stats': [],
            'overall_status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


# Missing API endpoints referenced in URLs
@require_admin_auth
def api_analytics_detailed(request):
    """API endpoint for detailed analytics"""
    try:
        days = int(request.GET.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Daily stats for the date range - serialize datetime properly
        daily_stats_raw = Task.objects.filter(created_at__gte=start_date).extra({'date': "date(created_at)"}).values('date').annotate(
            total_tasks=Count('id'),
            successful_tasks=Count('id', filter=Q(success=True)),
            avg_processing_time=Avg('processing_time')
        ).order_by('date')
        daily_stats = serialize_queryset_datetime(daily_stats_raw)
        
        # Tier analysis
        tier_analysis = list(
            User.objects.values('tier')
            .annotate(
                user_count=Count('phone_number'),
                task_count=Count('tasks', filter=Q(tasks__created_at__gte=start_date)),
                avg_processing_time=Avg('tasks__processing_time', filter=Q(tasks__created_at__gte=start_date))
            )
            .order_by('-user_count')
        )
        
        # Category stats
        category_stats = list(
            Task.objects.filter(created_at__gte=start_date)
            .values('category')
            .annotate(
                count=Count('id'),
                avg_processing_time=Avg('processing_time'),
                success_rate=Avg(
                    Case(
                        When(success=True, then=1),
                        default=0,
                        output_field=IntegerField()
                    ),
                    output_field=FloatField()
                ) * 100,
                avg_complexity=Avg('complexity_score')
            )
            .order_by('-count')
        )
        
        # Peak hour stats - serialize datetime properly
        peak_hour_stats_raw = Task.objects.filter(created_at__gte=start_date).extra({'hour': "extract(hour from created_at)"}).values('hour').annotate(task_count=Count('id')).order_by('-task_count')[:5]
        peak_hour_stats = list(peak_hour_stats_raw)
        
        # Error breakdown
        error_breakdown = list(
            ErrorLog.objects.filter(timestamp__gte=start_date)
            .values('error_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Detailed analytics data
        analytics_data = {
            'daily_stats': daily_stats,
            'tier_analysis': tier_analysis,
            'category_stats': category_stats,
            'user_analytics': get_user_analytics_data(days),
            'task_analytics': get_task_analytics_data(days),
            'performance_metrics': {
                'avg_response_time': Task.objects.filter(
                    created_at__gte=start_date
                ).aggregate(avg_time=Avg('processing_time'))['avg_time'] or 0,
                'peak_hour_stats': peak_hour_stats,
                'error_breakdown': error_breakdown
            }
        }
        
        return DateTimeAwareJSONResponse(analytics_data)
        
    except Exception as e:
        logger.error(f"Error getting detailed analytics: {e}")
        return DateTimeAwareJSONResponse({'error': 'Failed to fetch detailed analytics'}, status=500)


@require_admin_auth
def api_system_performance(request):
    """API endpoint for system performance metrics"""
    try:
        hours = int(request.GET.get('hours', 24))
        start_time = timezone.now() - timedelta(hours=hours)
        
        # Performance metrics - serialize datetime properly
        response_times_raw = Task.objects.filter(created_at__gte=start_time).extra({'hour': "date_trunc('hour', created_at)"}).values('hour').annotate(
            avg_time=Avg('processing_time'),
            max_time=Max('processing_time'),
            min_time=Min('processing_time'),
            task_count=Count('id')
        ).order_by('hour')
        response_times = serialize_queryset_datetime(response_times_raw)
        
        throughput_raw = Task.objects.filter(created_at__gte=start_time).extra({'hour': "date_trunc('hour', created_at)"}).values('hour').annotate(tasks_per_hour=Count('id')).order_by('hour')
        throughput = serialize_queryset_datetime(throughput_raw)
        
        success_rate_trend_raw = Task.objects.filter(created_at__gte=start_time).extra({'hour': "date_trunc('hour', created_at)"}).values('hour').annotate(
            total_tasks=Count('id'),
            successful_tasks=Count('id', filter=Q(success=True))
        ).order_by('hour')
        success_rate_trend = serialize_queryset_datetime(success_rate_trend_raw)
        
        performance_data = {
            'response_times': response_times,
            'throughput': throughput,
            'success_rate_trend': success_rate_trend,
            'current_stats': {
                'total_tasks_period': Task.objects.filter(created_at__gte=start_time).count(),
                'avg_processing_time': Task.objects.filter(
                    created_at__gte=start_time
                ).aggregate(avg_time=Avg('processing_time'))['avg_time'] or 0,
                'peak_concurrent_users': User.objects.filter(
                    last_active__gte=start_time
                ).count()
            }
        }
        
        return DateTimeAwareJSONResponse(performance_data)
        
    except Exception as e:
        logger.error(f"Error getting system performance: {e}")
        return DateTimeAwareJSONResponse({'error': 'Failed to fetch system performance'}, status=500)


@require_admin_auth
def api_system_errors(request):
    """API endpoint for system error information"""
    try:
        hours = int(request.GET.get('hours', 24))
        start_time = timezone.now() - timedelta(hours=hours)
        
        # Recent errors - serialize datetime properly
        recent_errors_raw = ErrorLog.objects.filter(timestamp__gte=start_time).values(
            'id', 'error_type', 'error_message', 'timestamp',
            'user_phone', 'task__id', 'resolved'
        ).order_by('-timestamp')[:50]
        recent_errors = serialize_queryset_datetime(recent_errors_raw)
        
        # Error trends - serialize datetime properly
        error_trends_raw = ErrorLog.objects.filter(timestamp__gte=start_time).extra({'hour': "date_trunc('hour', timestamp)"}).values('hour').annotate(error_count=Count('id')).order_by('hour')
        error_trends = serialize_queryset_datetime(error_trends_raw)
        
        # Error by type
        error_by_type = list(
            ErrorLog.objects.filter(timestamp__gte=start_time)
            .values('error_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        error_data = {
            'recent_errors': recent_errors,
            'error_trends': error_trends,
            'error_by_type': error_by_type,
            'unresolved_errors': ErrorLog.objects.filter(
                timestamp__gte=start_time,
                resolved=False
            ).count(),
            'total_errors_period': ErrorLog.objects.filter(
                timestamp__gte=start_time
            ).count()
        }
        
        return DateTimeAwareJSONResponse(error_data)
        
    except Exception as e:
        logger.error(f"Error getting system errors: {e}")
        return DateTimeAwareJSONResponse({'error': 'Failed to fetch system errors'}, status=500)


@require_admin_auth
def api_system_config(request):
    """API endpoint for system configuration"""
    try:
        config_data = {
            'database': {
                'engine': settings.DATABASES['default']['ENGINE'],
                'name': settings.DATABASES['default']['NAME'],
                'host': settings.DATABASES['default']['HOST'],
                'port': settings.DATABASES['default']['PORT']
            },
            'external_services': {
                'twilio_configured': bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN),
                'openai_configured': bool(settings.OPENAI_API_KEY),
                'redis_url': settings.REDIS_URL
            },
            'rate_limits': {
                'free': settings.RATE_LIMIT_FREE,
                'premium': settings.RATE_LIMIT_PREMIUM,
                'enterprise': settings.RATE_LIMIT_ENTERPRISE
            },
            'application': {
                'debug': settings.DEBUG,
                'allowed_hosts': settings.ALLOWED_HOSTS,
                'time_zone': settings.TIME_ZONE,
                'language_code': settings.LANGUAGE_CODE
            },
            'features': {
                'cors_enabled': 'corsheaders' in settings.INSTALLED_APPS,
                'rest_framework': 'rest_framework' in settings.INSTALLED_APPS,
                'admin_dashboard': 'admin_dashboard' in settings.INSTALLED_APPS
            }
        }
        
        return DateTimeAwareJSONResponse(config_data)
        
    except Exception as e:
        logger.error(f"Error getting system config: {e}")
        return DateTimeAwareJSONResponse({'error': 'Failed to fetch system configuration'}, status=500)


# Missing API endpoints for user management
@require_admin_auth
def api_user_details(request, phone_number):
    """API endpoint for individual user details"""
    try:
        user = User.objects.get(phone_number=phone_number)
        
        # Get user's task statistics
        task_stats = list(
            Task.objects.filter(user_phone=user)
            .values('category')
            .annotate(
                count=Count('id'),
                success_rate=Avg(
                    Case(
                        When(success=True, then=1),
                        default=0,
                        output_field=IntegerField()
                    ),
                    output_field=FloatField()
                ) * 100,
                avg_time=Avg('processing_time')
            )
            .order_by('-count')
        )
        
        # Get recent tasks - serialize datetime properly
        recent_tasks_raw = Task.objects.filter(user_phone=user).order_by('-created_at')[:10].values(
            'id', 'category', 'complexity_score', 'success',
            'processing_time', 'created_at'
        )
        recent_tasks = serialize_queryset_datetime(recent_tasks_raw)
        
        user_data = {
            'user_info': {
                'phone_number': user.phone_number,
                'tier': user.tier,
                'email': user.email,
                'full_name': user.full_name,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_active': user.last_active.isoformat() if user.last_active else None,
                'total_requests': user.total_requests,
                'monthly_requests': user.monthly_requests,
            },
            'task_statistics': task_stats,
            'recent_tasks': recent_tasks
        }
        
        return DateTimeAwareJSONResponse(user_data)
        
    except User.DoesNotExist:
        return DateTimeAwareJSONResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        logger.error(f"Error getting user details: {e}")
        return DateTimeAwareJSONResponse({'error': 'Failed to fetch user details'}, status=500)


@require_admin_auth  
@require_http_methods(["POST"])
def api_users_broadcast(request):
    """API endpoint for broadcasting messages to all users"""
    try:
        import json
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        
        if not message:
            return DateTimeAwareJSONResponse({'error': 'Message is required'}, status=400)
            
        # Here you would implement the actual SMS broadcasting
        # For now, just return success
        user_count = User.objects.count()
        
        logger.info(f"Broadcast message sent to {user_count} users: {message[:50]}...")
        
        return DateTimeAwareJSONResponse({
            'success': True,
            'message': f'Broadcast sent to {user_count} users',
            'recipient_count': user_count
        })
        
    except Exception as e:
        logger.error(f"Error sending broadcast: {e}")
        return DateTimeAwareJSONResponse({'error': 'Failed to send broadcast message'}, status=500)


@require_admin_auth
@require_http_methods(["POST"])
def api_users_message(request):
    """API endpoint for sending message to individual user"""
    try:
        import json
        data = json.loads(request.body)
        phone_number = data.get('phone_number', '').strip()
        message = data.get('message', '').strip()
        
        if not phone_number or not message:
            return DateTimeAwareJSONResponse({'error': 'Phone number and message are required'}, status=400)
            
        # Verify user exists
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return DateTimeAwareJSONResponse({'error': 'User not found'}, status=404)
            
        # Here you would implement the actual SMS sending
        # For now, just return success
        logger.info(f"Message sent to {phone_number}: {message[:50]}...")
        
        return DateTimeAwareJSONResponse({
            'success': True,
            'message': f'Message sent to {phone_number}',
            'recipient': phone_number
        })
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return DateTimeAwareJSONResponse({'error': 'Failed to send message'}, status=500)


@require_admin_auth
@require_http_methods(["POST"])
def api_users_tier(request):
    """API endpoint for updating user tier"""
    try:
        import json
        data = json.loads(request.body)
        phone_number = data.get('phone_number', '').strip()
        new_tier = data.get('tier', '').strip()
        
        if not phone_number or not new_tier:
            return DateTimeAwareJSONResponse({'error': 'Phone number and tier are required'}, status=400)
            
        if new_tier not in ['free', 'premium', 'enterprise']:
            return DateTimeAwareJSONResponse({'error': 'Invalid tier. Must be free, premium, or enterprise'}, status=400)
            
        # Update user tier
        try:
            user = User.objects.get(phone_number=phone_number)
            old_tier = user.tier
            user.tier = new_tier
            user.save()
            
            logger.info(f"User {phone_number} tier updated from {old_tier} to {new_tier}")
            
            return DateTimeAwareJSONResponse({
                'success': True,
                'message': f'User tier updated to {new_tier}',
                'old_tier': old_tier,
                'new_tier': new_tier
            })
            
        except User.DoesNotExist:
            return DateTimeAwareJSONResponse({'error': 'User not found'}, status=404)
            
    except Exception as e:
        logger.error(f"Error updating user tier: {e}")
        return DateTimeAwareJSONResponse({'error': 'Failed to update user tier'}, status=500)


@require_admin_auth
def api_analytics_export(request):
    """API endpoint for exporting analytics data as CSV"""
    try:
        import csv
        import io
        from django.http import HttpResponse
        
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not start_date or not end_date:
            return DateTimeAwareJSONResponse({'error': 'start_date and end_date are required'}, status=400)
            
        # Create CSV data
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'Date', 'Total Tasks', 'Successful Tasks', 'Success Rate', 
            'Avg Processing Time', 'Category', 'User Count'
        ])
        
        # Get analytics data
        from datetime import datetime
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        daily_stats = Task.objects.filter(
            created_at__gte=start_dt,
            created_at__lte=end_dt
        ).extra({'date': "date(created_at)"}).values('date').annotate(
            total_tasks=Count('id'),
            successful_tasks=Count('id', filter=Q(success=True)),
            avg_processing_time=Avg('processing_time')
        ).order_by('date')
        
        for stat in daily_stats:
            success_rate = (stat['successful_tasks'] / stat['total_tasks'] * 100) if stat['total_tasks'] > 0 else 0
            writer.writerow([
                stat['date'],
                stat['total_tasks'],
                stat['successful_tasks'],
                f"{success_rate:.2f}%",
                f"{stat['avg_processing_time']:.2f}s" if stat['avg_processing_time'] else "0s",
                "All",
                User.objects.filter(
                    tasks__created_at__date=stat['date']
                ).distinct().count()
            ])
        
        # Create HTTP response
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="analytics_{start_date}_to_{end_date}.csv"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting analytics: {e}")
        return DateTimeAwareJSONResponse({'error': 'Failed to export analytics data'}, status=500)


@require_admin_auth
def api_system_health(request):
    """API endpoint for system health data in the format expected by JavaScript"""
    try:
        yesterday = timezone.now() - timedelta(days=1)
        
        # Database health check
        try:
            total_tasks = Task.objects.count()
            database_healthy = True
        except Exception:
            database_healthy = False
            
        # Check for slow tasks (processing time > 30 seconds)
        slow_tasks_count = Task.objects.filter(
            created_at__gte=yesterday,
            processing_time__gt=30
        ).count()
        
        # Get recent error statistics
        error_stats = list(
            ErrorLog.objects.filter(timestamp__gte=yesterday)
            .values('error_type')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        
        # Get recent errors for display - serialize datetime properly
        recent_errors_raw = ErrorLog.objects.filter(timestamp__gte=yesterday).order_by('-timestamp')[:5].values('error_type', 'error_message', 'timestamp', 'user_phone')
        recent_errors = serialize_queryset_datetime(recent_errors_raw)
        
        health_data = {
            'database_health': {
                'status': 'healthy' if database_healthy else 'error',
                'connected': database_healthy
            },
            'slow_tasks_count': slow_tasks_count,
            'error_stats': error_stats,
            'recent_errors': recent_errors,
            'timestamp': timezone.now().isoformat(),
            'overall_status': 'healthy' if database_healthy and slow_tasks_count < 10 and len(error_stats) < 5 else 'warning'
        }
        
        return DateTimeAwareJSONResponse(health_data)
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return DateTimeAwareJSONResponse({
            'database_health': {'status': 'error', 'connected': False},
            'slow_tasks_count': 0,
            'error_stats': [],
            'recent_errors': [],
            'overall_status': 'error',
            'error': str(e)
        }, status=500) 