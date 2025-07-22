from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'core'

# REST API router for viewsets
router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'errors', views.ErrorLogViewSet)

urlpatterns = [
    # Main SMS processing endpoint (Twilio webhook)
    path('sms/receive', views.sms_receive, name='sms_receive'),
    
    # SMS sending endpoint
    path('sms/send', views.sms_send, name='sms_send'),
    
    # Health check endpoint
    path('health', views.health_check, name='health_check'),
    
    # User management endpoints
    path('users/register', views.register_user, name='register_user'),
    path('users/<str:phone_number>/profile', views.user_profile, name='user_profile'),
    path('users/<str:phone_number>/tasks', views.user_tasks, name='user_tasks'),
    
    # Task processing endpoints
    path('tasks/process', views.process_task, name='process_task'),
    path('tasks/<int:task_id>/status', views.task_status, name='task_status'),
    
    # Analytics endpoints
    path('analytics/overview', views.analytics_overview, name='analytics_overview'),
    path('analytics/user-stats', views.user_statistics, name='user_statistics'),
    path('analytics/task-stats', views.task_statistics, name='task_statistics'),
    
    # REST API endpoints
    path('api/', include(router.urls)),
    
    # Default home endpoint
    path('', views.home, name='home'),
] 