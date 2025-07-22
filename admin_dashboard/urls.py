from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    # Authentication
    path('', views.admin_login, name='login'),  # Default dashboard login
    path('login/', views.admin_login, name='login_explicit'),
    path('logout/', views.admin_logout, name='logout'),
    
    # Dashboard views
    path('dashboard/', views.dashboard, name='dashboard'),
    path('users/', views.users_view, name='users'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('system/', views.system_view, name='system'),
    
    # API endpoints to maintain compatibility with existing frontend
    path('api/overview', views.api_overview, name='api_overview'),
    path('api/users', views.api_users, name='api_users'),
    path('api/users/stats', views.api_users_stats, name='api_users_stats'),
    path('api/users/<str:phone_number>', views.api_user_details, name='api_user_details'),
    path('api/users/broadcast', views.api_users_broadcast, name='api_users_broadcast'),
    path('api/users/message', views.api_users_message, name='api_users_message'),
    path('api/users/tier', views.api_users_tier, name='api_users_tier'),
    
    # Additional API endpoints that were in the original Flask app
    path('api/analytics/detailed', views.api_analytics_detailed, name='api_analytics_detailed'),
    path('api/analytics/export', views.api_analytics_export, name='api_analytics_export'),
    path('api/system/performance', views.api_system_performance, name='api_system_performance'),
    path('api/system/health', views.api_system_health, name='api_system_health'),
    path('api/system/errors', views.api_system_errors, name='api_system_errors'),
    path('api/system/config', views.api_system_config, name='api_system_config'),
] 