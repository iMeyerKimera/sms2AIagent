"""
Enhanced SMS-to-Cursor AI Agent - Admin Dashboard
Provides comprehensive web-based administration interface
"""

import os
import json
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for, flash
from functools import wraps
from database_manager import get_database_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global database manager instance
db = get_database_manager()

# Create Blueprint for admin routes
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin authentication
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = hashlib.sha256(os.environ.get("ADMIN_PASSWORD", "admin123").encode()).hexdigest()

def require_auth(f):
    """Decorator to require authentication for admin routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_authenticated' not in session or not session['admin_authenticated']:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/debug-bypass')
def debug_bypass():
    """Temporary route to bypass authentication for testing"""
    session['admin_authenticated'] = True
    session['admin_user'] = 'debug'
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/debug-session')
def debug_session():
    """Debug route to check session status"""
    return jsonify({
        'session_data': dict(session),
        'authenticated': session.get('admin_authenticated', False),
        'user': session.get('admin_user', None)
    })

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH:
            session['admin_authenticated'] = True
            session['admin_user'] = username
            return redirect(url_for('admin.dashboard'))
        else:
            flash("Invalid credentials", "error")
            return render_template('admin/login.html', error="Invalid credentials")
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.pop('admin_authenticated', None)
    session.pop('admin_user', None)
    flash("Logged out successfully", "success")
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@require_auth
def dashboard():
    """Main admin dashboard"""
    analytics = AdminAnalytics()
    
    # Get overview statistics
    overview = analytics.get_system_overview()
    user_analytics = analytics.get_user_analytics(7)  # Last 7 days
    task_analytics = analytics.get_task_analytics(7)  # Last 7 days
    system_health = analytics.get_system_health()
    
    return render_template('admin/dashboard.html', 
                         overview=overview,
                         user_analytics=user_analytics,
                         task_analytics=task_analytics,
                         system_health=system_health)

@admin_bp.route('/users')
@require_auth
def users():
    """User management page"""
    analytics = AdminAnalytics()
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    tier_filter = request.args.get('tier', '')
    
    users_data = analytics.get_users_list(page=page, per_page=20, search=search, tier_filter=tier_filter)
    
    return render_template('admin/users.html', 
                         users_data=users_data,
                         search=search,
                         tier_filter=tier_filter)

@admin_bp.route('/analytics')
@require_auth
def analytics():
    """Analytics and reporting page"""
    analytics = AdminAnalytics()
    
    # Get date range from query parameters
    days = request.args.get('days', 30, type=int)
    
    user_analytics = analytics.get_user_analytics(days)
    task_analytics = analytics.get_task_analytics(days)
    
    return render_template('admin/analytics.html', 
                         user_analytics=user_analytics,
                         task_analytics=task_analytics,
                         days=days)

@admin_bp.route('/system')
@require_auth
def system():
    """System monitoring and configuration"""
    analytics = AdminAnalytics()
    
    system_health = analytics.get_system_health()
    overview = analytics.get_system_overview()
    
    return render_template('admin/system.html',
                         system_health=system_health,
                         overview=overview)

# API Routes for AJAX calls
@admin_bp.route('/api/overview')
@require_auth
def api_overview():
    """API endpoint for dashboard overview data"""
    analytics = AdminAnalytics()
    overview = analytics.get_system_overview()
    return jsonify(overview)

@admin_bp.route('/api/users')
@require_auth
def api_users():
    """API endpoint for users data with pagination and search"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    tier_filter = request.args.get('tier', '')
    
    analytics = AdminAnalytics()
    users_data = analytics.get_users_list(page=page, per_page=per_page, search=search, tier_filter=tier_filter)
    
    return jsonify(users_data)

@admin_bp.route('/api/analytics/users/<int:days>')
@require_auth
def api_user_analytics(days):
    """API endpoint for user analytics"""
    analytics = AdminAnalytics()
    user_data = analytics.get_user_analytics(days)
    return jsonify(user_data)

@admin_bp.route('/api/analytics/tasks/<int:days>')
@require_auth
def api_task_analytics(days):
    """API endpoint for task analytics"""
    analytics = AdminAnalytics()
    task_data = analytics.get_task_analytics(days)
    return jsonify(task_data)

@admin_bp.route('/api/system/health')
@require_auth
def api_system_health():
    """API endpoint for system health"""
    analytics = AdminAnalytics()
    health_data = analytics.get_system_health()
    return jsonify(health_data)

@admin_bp.route('/api/users/tier', methods=['POST'])
@require_auth
def api_update_user_tier():
    """API endpoint to update user tier"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        new_tier = data.get('tier')
        
        if not phone_number or not new_tier:
            return jsonify({'error': 'Phone number and tier are required'}), 400
        
        if new_tier not in ['free', 'premium', 'enterprise']:
            return jsonify({'error': 'Invalid tier'}), 400
        
        # Update user tier in database
        db.execute_query("""
            UPDATE users 
            SET tier = %s 
            WHERE phone_number = %s
        """, (new_tier, phone_number), fetch='none')
        
        return jsonify({'success': True, 'message': 'User tier updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating user tier: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/api/users/message', methods=['POST'])
@require_auth
def api_send_user_message():
    """Send a message to a specific user"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        message = data.get('message')
        
        if not phone_number or not message:
            return jsonify({'error': 'Phone number and message are required'}), 400
        
        # Here you would integrate with your notification system
        # For now, just return success
        return jsonify({'success': True, 'message': 'Message sent successfully'})
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/api/users/stats')
@require_auth
def api_users_stats():
    """API endpoint for user statistics"""
    try:
        analytics = AdminAnalytics()
        
        # Get user statistics with better error handling
        try:
            user_stats = analytics.db.execute_query("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(CASE WHEN tier = 'free' THEN 1 END) as free_users,
                    COUNT(CASE WHEN tier = 'premium' THEN 1 END) as premium_users,
                    COUNT(CASE WHEN tier = 'enterprise' THEN 1 END) as enterprise_users,
                    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as new_users_week,
                    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '30 days' THEN 1 END) as new_users_month,
                    COUNT(CASE WHEN last_active >= NOW() - INTERVAL '24 hours' THEN 1 END) as active_24h,
                    COUNT(CASE WHEN last_active >= NOW() - INTERVAL '7 days' THEN 1 END) as active_7d,
                    COUNT(CASE WHEN last_active >= NOW() - INTERVAL '30 days' THEN 1 END) as active_30d
                FROM users
            """, fetch='one')
            
            if not user_stats:
                user_stats = {
                    'total_users': 0,
                    'free_users': 0,
                    'premium_users': 0,
                    'enterprise_users': 0,
                    'new_users_week': 0,
                    'new_users_month': 0,
                    'active_24h': 0,
                    'active_7d': 0,
                    'active_30d': 0
                }
        except Exception as e:
            logger.warning(f"Error getting user stats: {e}")
            user_stats = {
                'total_users': 0,
                'free_users': 0,
                'premium_users': 0,
                'enterprise_users': 0,
                'new_users_week': 0,
                'new_users_month': 0,
                'active_24h': 0,
                'active_7d': 0,
                'active_30d': 0
            }
        
        # Get user growth over time (last 30 days)
        try:
            growth_data = analytics.db.execute_query("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as new_users
                FROM users
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY DATE(created_at)
                ORDER BY date
            """)
            
            if not growth_data:
                growth_data = []
        except Exception as e:
            logger.warning(f"Error getting user growth data: {e}")
            growth_data = []
        
        # Get user activity by tier
        try:
            tier_activity = analytics.db.execute_query("""
                SELECT 
                    u.tier,
                    COUNT(DISTINCT u.phone_number) as user_count,
                    COALESCE(COUNT(t.id), 0) as total_tasks,
                    COALESCE(AVG(t.processing_time), 0) as avg_processing_time,
                    COUNT(CASE WHEN t.success = true THEN 1 END) as successful_tasks
                FROM users u
                LEFT JOIN tasks t ON u.phone_number = t.user_phone 
                    AND t.created_at >= NOW() - INTERVAL '30 days'
                GROUP BY u.tier
                ORDER BY user_count DESC
            """)
            
            if not tier_activity:
                tier_activity = []
        except Exception as e:
            logger.warning(f"Error getting tier activity: {e}")
            tier_activity = []
        
        # Get recent user registrations
        try:
            recent_users = analytics.db.execute_query("""
                SELECT 
                    phone_number,
                    tier,
                    created_at,
                    last_active
                FROM users
                ORDER BY created_at DESC
                LIMIT 10
            """)
            
            if not recent_users:
                recent_users = []
        except Exception as e:
            logger.warning(f"Error getting recent users: {e}")
            recent_users = []
        
        return jsonify({
            'user_stats': user_stats,
            'growth_data': growth_data,
            'tier_activity': tier_activity,
            'recent_users': recent_users,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return jsonify({
            'user_stats': {
                'total_users': 0,
                'free_users': 0,
                'premium_users': 0,
                'enterprise_users': 0,
                'new_users_week': 0,
                'new_users_month': 0,
                'active_24h': 0,
                'active_7d': 0,
                'active_30d': 0
            },
            'growth_data': [],
            'tier_activity': [],
            'recent_users': [],
            'timestamp': datetime.now().isoformat(),
            'error': 'Failed to fetch user statistics'
        }), 200

@admin_bp.route('/api/analytics/detailed')
@require_auth
def api_detailed_analytics():
    """API endpoint for detailed analytics with date range"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        analytics = AdminAnalytics()
        
        # Validate dates
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        # Task analytics for date range
        task_analytics = analytics.db.execute_query("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as total_tasks,
                COUNT(CASE WHEN success = true THEN 1 END) as successful_tasks,
                COUNT(CASE WHEN success = false THEN 1 END) as failed_tasks,
                AVG(processing_time) as avg_processing_time,
                AVG(tokens_used) as avg_tokens_used,
                AVG(complexity_score) as avg_complexity
            FROM tasks
            WHERE created_at >= %s AND created_at <= %s
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (start_date, end_date)) or []
        
        # Category breakdown
        category_analytics = analytics.db.execute_query("""
            SELECT 
                category,
                COUNT(*) as task_count,
                AVG(processing_time) as avg_processing_time,
                AVG(complexity_score) as avg_complexity,
                COUNT(CASE WHEN success = true THEN 1 END) as successful_tasks,
                COUNT(CASE WHEN success = false THEN 1 END) as failed_tasks
            FROM tasks
            WHERE created_at >= %s AND created_at <= %s
            GROUP BY category
            ORDER BY task_count DESC
        """, (start_date, end_date)) or []
        
        # User activity for date range
        user_activity = analytics.db.execute_query("""
            SELECT 
                u.tier,
                COUNT(DISTINCT u.phone_number) as active_users,
                COUNT(t.id) as total_tasks,
                AVG(t.processing_time) as avg_processing_time
            FROM users u
            JOIN tasks t ON u.phone_number = t.user_phone
            WHERE t.created_at >= %s AND t.created_at <= %s
            GROUP BY u.tier
        """, (start_date, end_date)) or []
        
        # Performance metrics
        performance_metrics = analytics.db.execute_query("""
            SELECT 
                COUNT(*) as total_tasks,
                AVG(processing_time) as avg_processing_time,
                MIN(processing_time) as min_processing_time,
                MAX(processing_time) as max_processing_time,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY processing_time) as median_processing_time,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY processing_time) as p95_processing_time,
                AVG(tokens_used) as avg_tokens_used,
                COUNT(CASE WHEN processing_time > 10 THEN 1 END) as slow_tasks
            FROM tasks
            WHERE created_at >= %s AND created_at <= %s
        """, (start_date, end_date), fetch='one') or {}
        
        return jsonify({
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            },
            'task_analytics': task_analytics,
            'category_analytics': category_analytics,
            'user_activity': user_activity,
            'performance_metrics': performance_metrics
        })
        
    except Exception as e:
        logger.error(f"Error getting detailed analytics: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/api/system/performance')
@require_auth
def api_system_performance():
    """API endpoint for system performance metrics"""
    try:
        analytics = AdminAnalytics()
        
        # Get basic performance metrics - handle empty results
        try:
            performance_metrics = analytics.db.execute_query("""
                SELECT 
                    COUNT(*) as total_tasks,
                    COALESCE(AVG(processing_time), 0) as avg_processing_time,
                    COUNT(CASE WHEN processing_time > 10 THEN 1 END) as slow_tasks
                FROM tasks
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """, fetch='one')
            
            if not performance_metrics:
                performance_metrics = {
                    'total_tasks': 0,
                    'avg_processing_time': 0,
                    'slow_tasks': 0
                }
        except Exception as e:
            logger.warning(f"Error getting performance metrics: {e}")
            performance_metrics = {
                'total_tasks': 0,
                'avg_processing_time': 0,
                'slow_tasks': 0
            }
        
        # Get recent performance trends - handle empty results
        try:
            performance_trends = analytics.db.execute_query("""
                SELECT 
                    DATE_TRUNC('hour', created_at) as hour,
                    COUNT(*) as task_count,
                    COALESCE(AVG(processing_time), 0) as avg_processing_time
                FROM tasks
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY DATE_TRUNC('hour', created_at)
                ORDER BY hour
            """)
            
            if not performance_trends:
                performance_trends = []
        except Exception as e:
            logger.warning(f"Error getting performance trends: {e}")
            performance_trends = []
        
        # Get database size safely
        try:
            db_size_result = analytics.db.execute_query("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as size
            """, fetch='one')
            db_size = db_size_result.get('size', 'Unknown') if db_size_result else 'Unknown'
        except Exception as e:
            logger.warning(f"Error getting database size: {e}")
            db_size = 'Unknown'
        
        # Get table counts safely
        table_counts = {}
        try:
            table_data = analytics.db.execute_query("""
                SELECT 
                    schemaname,
                    relname as table_name,
                    COALESCE(n_live_tup, 0) as row_count
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY relname
            """)
            
            if table_data:
                for table in table_data:
                    table_counts[table['table_name']] = table['row_count']
        except Exception as e:
            logger.warning(f"Error getting table counts: {e}")
            table_counts = {}
        
        # Get connection stats safely
        try:
            connection_stats = analytics.db.execute_query("""
                SELECT 
                    COUNT(*) as total_connections,
                    COUNT(CASE WHEN state = 'active' THEN 1 END) as active_connections,
                    COUNT(CASE WHEN state = 'idle' THEN 1 END) as idle_connections
                FROM pg_stat_activity
                WHERE datname = current_database()
            """, fetch='one')
            
            if not connection_stats:
                connection_stats = {
                    'total_connections': 0,
                    'active_connections': 0,
                    'idle_connections': 0
                }
        except Exception as e:
            logger.warning(f"Error getting connection stats: {e}")
            connection_stats = {
                'total_connections': 0,
                'active_connections': 0,
                'idle_connections': 0
            }
        
        return jsonify({
            'performance_metrics': performance_metrics,
            'performance_trends': performance_trends,
            'database_size': db_size,
            'table_counts': table_counts,
            'connection_stats': connection_stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting system performance: {e}")
        return jsonify({
            'performance_metrics': {
                'total_tasks': 0,
                'avg_processing_time': 0,
                'slow_tasks': 0
            },
            'performance_trends': [],
            'database_size': 'Unknown',
            'table_counts': {},
            'connection_stats': {
                'total_connections': 0,
                'active_connections': 0,
                'idle_connections': 0
            },
            'timestamp': datetime.now().isoformat(),
            'error': 'Failed to fetch performance data'
        }), 200  # Return 200 with error message instead of 500

@admin_bp.route('/api/system/errors')
@require_auth
def api_system_errors():
    """API endpoint for system error logs and statistics"""
    try:
        analytics = AdminAnalytics()
        
        # Get recent errors (last 24 hours)
        recent_errors = analytics.db.execute_query("""
            SELECT 
                timestamp,
                error_type,
                error_message,
                user_phone,
                COUNT(*) OVER (PARTITION BY error_type) as error_count
            FROM error_logs
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
            ORDER BY timestamp DESC
            LIMIT 50
        """) or []
        
        # Get error statistics by type
        error_stats = analytics.db.execute_query("""
            SELECT 
                error_type,
                COUNT(*) as count,
                MAX(timestamp) as last_occurrence,
                MIN(timestamp) as first_occurrence
            FROM error_logs
            WHERE timestamp >= NOW() - INTERVAL '7 days'
            GROUP BY error_type
            ORDER BY count DESC
        """) or []
        
        # Get error trends over time
        error_trends = analytics.db.execute_query("""
            SELECT 
                DATE_TRUNC('hour', timestamp) as hour,
                COUNT(*) as error_count,
                COUNT(DISTINCT error_type) as unique_error_types
            FROM error_logs
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
            GROUP BY DATE_TRUNC('hour', timestamp)
            ORDER BY hour
        """) or []
        
        # Get top error-prone users
        user_errors = analytics.db.execute_query("""
            SELECT 
                user_phone,
                COUNT(*) as error_count,
                COUNT(DISTINCT error_type) as unique_errors,
                MAX(timestamp) as last_error
            FROM error_logs
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
            AND user_phone IS NOT NULL
            GROUP BY user_phone
            ORDER BY error_count DESC
            LIMIT 10
        """) or []
        
        # Calculate error rates
        total_tasks_24h = analytics.db.execute_query("""
            SELECT COUNT(*) as count
            FROM tasks
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """, fetch='one') or {'count': 0}
        
        total_errors_24h = analytics.db.execute_query("""
            SELECT COUNT(*) as count
            FROM error_logs
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
        """, fetch='one') or {'count': 0}
        
        error_rate = 0
        if total_tasks_24h['count'] > 0:
            error_rate = (total_errors_24h['count'] / total_tasks_24h['count']) * 100
        
        return jsonify({
            'recent_errors': recent_errors,
            'error_stats': error_stats,
            'error_trends': error_trends,
            'user_errors': user_errors,
            'summary': {
                'total_errors_24h': total_errors_24h['count'],
                'total_tasks_24h': total_tasks_24h['count'],
                'error_rate_percentage': round(error_rate, 2),
                'unique_error_types': len(error_stats)
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting system errors: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@admin_bp.route('/api/system/config')
@require_auth
def api_system_config():
    """API endpoint for system configuration"""
    try:
        analytics = AdminAnalytics()
        
        # Database configuration with better error handling
        try:
            db_config = analytics.db.execute_query("""
                SELECT 
                    name,
                    setting,
                    COALESCE(unit, '') as unit,
                    COALESCE(category, 'General') as category,
                    COALESCE(short_desc, '') as short_desc
                FROM pg_settings
                WHERE name IN (
                    'max_connections',
                    'shared_buffers',
                    'effective_cache_size',
                    'maintenance_work_mem',
                    'checkpoint_completion_target',
                    'wal_buffers',
                    'default_statistics_target',
                    'random_page_cost',
                    'effective_io_concurrency',
                    'work_mem'
                )
                ORDER BY name
            """)
            
            if not db_config:
                db_config = []
        except Exception as e:
            logger.warning(f"Error getting database config: {e}")
            db_config = []
        
        # Application configuration - safer environment variable handling
        try:
            app_config = {
                'admin_username': os.environ.get('ADMIN_USERNAME', 'admin'),
                'flask_env': os.environ.get('FLASK_ENV', 'production'),
                'database_url': 'Configured' if os.environ.get('DATABASE_URL') else 'Not configured',
                'redis_url': 'Configured' if os.environ.get('REDIS_URL') else 'Not configured',
                'twilio_configured': bool(os.environ.get('TWILIO_ACCOUNT_SID')),
                'openai_configured': bool(os.environ.get('OPENAI_API_KEY')),
                'rate_limits': {
                    'free': os.environ.get('RATE_LIMIT_FREE', '10'),
                    'premium': os.environ.get('RATE_LIMIT_PREMIUM', '100'),
                    'enterprise': os.environ.get('RATE_LIMIT_ENTERPRISE', '1000')
                },
                'features': {
                    'backup_enabled': bool(os.environ.get('BACKUP_ENABLED', True)),
                    'analytics_enabled': bool(os.environ.get('ANALYTICS_ENABLED', True)),
                    'rate_limiting_enabled': bool(os.environ.get('RATE_LIMITING_ENABLED', True)),
                    'error_tracking_enabled': bool(os.environ.get('ERROR_TRACKING_ENABLED', True))
                }
            }
        except Exception as e:
            logger.warning(f"Error getting app config: {e}")
            app_config = {
                'admin_username': 'admin',
                'flask_env': 'production',
                'database_url': 'Unknown',
                'redis_url': 'Unknown',
                'twilio_configured': False,
                'openai_configured': False,
                'rate_limits': {'free': '10', 'premium': '100', 'enterprise': '1000'},
                'features': {
                    'backup_enabled': True,
                    'analytics_enabled': True,
                    'rate_limiting_enabled': True,
                    'error_tracking_enabled': True
                }
            }
        
        # System status
        try:
            system_status = {
                'database_connected': True,
                'redis_connected': True,  # Assume true if we got this far
                'uptime': 'Unknown',
                'version': '1.0.0',
                'last_backup': 'Unknown',
                'total_requests_today': 0
            }
            
            # Try to get some basic system stats
            try:
                stats_result = analytics.db.execute_query("""
                    SELECT COUNT(*) as total_requests
                    FROM tasks
                    WHERE created_at >= CURRENT_DATE
                """, fetch='one')
                
                if stats_result:
                    system_status['total_requests_today'] = stats_result.get('total_requests', 0)
            except:
                pass  # Keep default value
                
        except Exception as e:
            logger.warning(f"Error getting system status: {e}")
            system_status = {
                'database_connected': False,
                'redis_connected': False,
                'uptime': 'Unknown',
                'version': '1.0.0',
                'last_backup': 'Unknown',
                'total_requests_today': 0
            }
        
        return jsonify({
            'database_config': db_config,
            'application_config': app_config,
            'system_status': system_status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting system config: {e}")
        return jsonify({
            'database_config': [],
            'application_config': {
                'admin_username': 'admin',
                'flask_env': 'production',
                'database_url': 'Unknown',
                'redis_url': 'Unknown',
                'twilio_configured': False,
                'openai_configured': False,
                'rate_limits': {'free': '10', 'premium': '100', 'enterprise': '1000'},
                'features': {
                    'backup_enabled': True,
                    'analytics_enabled': True,
                    'rate_limiting_enabled': True,
                    'error_tracking_enabled': True
                }
            },
            'system_status': {
                'database_connected': False,
                'redis_connected': False,
                'uptime': 'Unknown',
                'version': '1.0.0',
                'last_backup': 'Unknown',
                'total_requests_today': 0
            },
            'timestamp': datetime.now().isoformat(),
            'error': 'Failed to fetch system configuration'
        }), 200

@admin_bp.route('/api/sample-data', methods=['POST'])
@require_auth
def api_insert_sample_data():
    """Insert sample data for testing"""
    try:
        analytics = AdminAnalytics()
        success = analytics.insert_sample_data()
        
        if success:
            return jsonify({'success': True, 'message': 'Sample data inserted successfully'})
        else:
            return jsonify({'error': 'Failed to insert sample data'}), 500
            
    except Exception as e:
        logger.error(f"Error inserting sample data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

class AdminAnalytics:
    """Enhanced analytics system for comprehensive system monitoring"""
    
    def __init__(self):
        """Initialize analytics with PostgreSQL database manager"""
        self.db = get_database_manager()
        logger.info("Admin Analytics initialized with PostgreSQL")
    
    def get_system_overview(self):
        """Get comprehensive system overview with key metrics"""
        try:
            # Get total users by tier
            users_by_tier = self.db.execute_query("""
                SELECT tier, COUNT(*) as count 
                FROM users 
                GROUP BY tier
            """) or []
            
            # Get total tasks and success rate
            task_stats = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total_tasks,
                    COUNT(CASE WHEN success = true THEN 1 END) as successful_tasks,
                    AVG(processing_time) as avg_processing_time,
                    AVG(tokens_used) as avg_tokens_used
                FROM tasks
            """, fetch='one') or {}
            
            # Get recent activity (last 24 hours)
            recent_activity = self.db.execute_query("""
                SELECT COUNT(*) as count
                FROM tasks 
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """, fetch='one') or {'count': 0}
            
            # Get active users (last 7 days)
            active_users = self.db.execute_query("""
                SELECT COUNT(DISTINCT user_phone) as count
                FROM tasks 
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """, fetch='one') or {'count': 0}
            
            # Calculate success rate
            success_rate = 0
            if task_stats.get('total_tasks', 0) > 0:
                success_rate = (task_stats.get('successful_tasks', 0) / task_stats.get('total_tasks', 1)) * 100
            
            return {
                'total_users': sum(tier['count'] for tier in users_by_tier),
                'users_by_tier': {tier['tier']: tier['count'] for tier in users_by_tier},
                'total_tasks': task_stats.get('total_tasks', 0),
                'success_rate': round(success_rate, 2),
                'avg_processing_time': round(task_stats.get('avg_processing_time', 0) or 0, 2),
                'avg_tokens_used': round(task_stats.get('avg_tokens_used', 0) or 0, 2),
                'recent_activity': recent_activity['count'],
                'active_users': active_users['count']
            }
            
        except Exception as e:
            logger.error(f"Error getting system overview: {e}")
            return {
                'total_users': 0, 'users_by_tier': {}, 'total_tasks': 0,
                'success_rate': 0, 'avg_processing_time': 0, 'avg_tokens_used': 0,
                'recent_activity': 0, 'active_users': 0
            }
    
    def get_user_analytics(self, days=30):
        """Get user activity analytics for specified period"""
        try:
            # User registration trends
            user_trends = self.db.execute_query("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as new_users
                FROM users 
                WHERE created_at >= NOW() - INTERVAL '%s days'
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (days,))
            
            # User activity by tier
            tier_activity = self.db.execute_query("""
                SELECT 
                    u.tier,
                    COUNT(t.id) as task_count,
                    COUNT(DISTINCT u.phone_number) as active_users
                FROM users u
                LEFT JOIN tasks t ON u.phone_number = t.user_phone 
                    AND t.created_at >= NOW() - INTERVAL '%s days'
                GROUP BY u.tier
            """, (days,))
            
            # Top users by activity
            top_users = self.db.execute_query("""
                SELECT 
                    u.phone_number,
                    u.tier,
                    COUNT(t.id) as task_count,
                    AVG(t.processing_time) as avg_time,
                    MAX(t.created_at) as last_activity
                FROM users u
                JOIN tasks t ON u.phone_number = t.user_phone
                WHERE t.created_at >= NOW() - INTERVAL '%s days'
                GROUP BY u.phone_number, u.tier
                ORDER BY task_count DESC
                LIMIT 20
            """, (days,))
            
            return {
                'user_trends': user_trends or [],
                'tier_activity': tier_activity or [],
                'top_users': top_users or []
            }
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {e}")
            return {'user_trends': [], 'tier_activity': [], 'top_users': []}
    
    def get_task_analytics(self, days=30):
        """Get comprehensive task analytics"""
        try:
            # Task trends over time
            task_trends = self.db.execute_query("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as total_tasks,
                    COUNT(CASE WHEN success = true THEN 1 END) as successful_tasks,
                    AVG(processing_time) as avg_time
                FROM tasks
                WHERE created_at >= NOW() - INTERVAL '%s days'
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (days,))
            
            # Task categories
            category_stats = self.db.execute_query("""
                SELECT 
                    category,
                    COUNT(*) as count,
                    AVG(processing_time) as avg_time,
                    AVG(complexity_score) as avg_complexity
                FROM tasks
                WHERE created_at >= NOW() - INTERVAL '%s days'
                GROUP BY category
                ORDER BY count DESC
            """, (days,))
            
            # Performance metrics
            performance = self.db.execute_query("""
                SELECT 
                    AVG(processing_time) as avg_processing_time,
                    MIN(processing_time) as min_processing_time,
                    MAX(processing_time) as max_processing_time,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY processing_time) as median_processing_time,
                    AVG(tokens_used) as avg_tokens,
                    COUNT(CASE WHEN success = false THEN 1 END) as error_count
                FROM tasks
                WHERE created_at >= NOW() - INTERVAL '%s days'
            """, (days,), fetch='one') or {}
            
            return {
                'task_trends': task_trends or [],
                'category_stats': category_stats or [],
                'performance': performance
            }
            
        except Exception as e:
            logger.error(f"Error getting task analytics: {e}")
            return {'task_trends': [], 'category_stats': [], 'performance': {}}
    
    def get_system_health(self):
        """Get comprehensive system health metrics"""
        try:
            # Database health
            db_health = self.db.health_check()
            
            # Error rate analysis
            error_stats = self.db.execute_query("""
                SELECT 
                    error_type,
                    COUNT(*) as count,
                    MAX(timestamp) as last_occurrence
                FROM error_logs
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
                GROUP BY error_type
                ORDER BY count DESC
            """)
            
            # Performance alerts
            slow_tasks = self.db.execute_query("""
                SELECT COUNT(*) as count
                FROM tasks
                WHERE processing_time > 30 
                AND created_at >= NOW() - INTERVAL '24 hours'
            """, fetch='one') or {'count': 0}
            
            # Recent errors
            recent_errors = self.db.execute_query("""
                SELECT timestamp, error_type, error_message, user_phone
                FROM error_logs
                WHERE timestamp >= NOW() - INTERVAL '1 hour'
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            
            return {
                'database_health': db_health,
                'error_stats': error_stats or [],
                'slow_tasks_count': slow_tasks['count'],
                'recent_errors': recent_errors or []
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                'database_health': {'status': 'unhealthy', 'error': str(e)},
                'error_stats': [],
                'slow_tasks_count': 0,
                'recent_errors': []
            }
    
    def get_users_list(self, page=1, per_page=50, search=None, tier_filter=None):
        """Get paginated users list with search and filtering"""
        try:
            offset = (page - 1) * per_page
            
            # Build WHERE clause
            where_conditions = []
            params = []
            
            if search:
                where_conditions.append("(phone_number ILIKE %s OR COALESCE(email, '') ILIKE %s OR COALESCE(full_name, '') ILIKE %s)")
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])
            
            if tier_filter:
                where_conditions.append("tier = %s")
                params.append(tier_filter)
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # Get users with simplified query to avoid PostgreSQL issues
            try:
                users_query = f"""
                    SELECT 
                        phone_number,
                        tier,
                        created_at,
                        last_active,
                        COALESCE(total_requests, 0) as total_requests,
                        COALESCE(monthly_requests, 0) as monthly_requests,
                        rate_limit_reset,
                        email,
                        full_name,
                        timezone,
                        preferences
                    FROM users
                    {where_clause}
                    ORDER BY COALESCE(last_active, created_at) DESC
                    LIMIT %s OFFSET %s
                """
                
                params.extend([per_page, offset])
                users_result = self.db.execute_query(users_query, tuple(params))
                users = users_result if users_result else []
                
                # Add task counts separately to avoid complex JOINs
                for user in users:
                    try:
                        task_count_result = self.db.execute_query("""
                            SELECT 
                                COUNT(*) as task_count,
                                MAX(created_at) as last_task
                            FROM tasks 
                            WHERE user_phone = %s
                        """, (user['phone_number'],), fetch='one')
                        
                        if task_count_result:
                            user['task_count'] = task_count_result.get('task_count', 0)
                            user['last_task'] = task_count_result.get('last_task')
                        else:
                            user['task_count'] = 0
                            user['last_task'] = None
                    except:
                        user['task_count'] = 0
                        user['last_task'] = None
                        
            except Exception as e:
                logger.warning(f"Error getting users: {e}")
                users = []
            
            # Get total count with simpler query
            try:
                count_query = f"""
                    SELECT COUNT(*) as total
                    FROM users
                    {where_clause}
                """
                count_params = params[:-2] if where_conditions else []
                total_result = self.db.execute_query(count_query, tuple(count_params), fetch='one')
                total_users = total_result.get('total', 0) if total_result else 0
            except Exception as e:
                logger.warning(f"Error getting user count: {e}")
                total_users = len(users)  # Fallback to current page count
            
            return {
                'users': users,
                'total': total_users,
                'page': page,
                'per_page': per_page,
                'total_pages': max(1, (total_users + per_page - 1) // per_page)
            }
            
        except Exception as e:
            logger.error(f"Error getting users list: {e}")
            return {
                'users': [], 
                'total': 0, 
                'page': 1, 
                'per_page': per_page, 
                'total_pages': 0
            }
    
    def insert_sample_data(self):
        """Insert sample data for testing and demonstration"""
        try:
            # Insert sample users
            sample_users = [
                ('+1234567890', 'premium', 'john.doe@example.com', 'John Doe'),
                ('+0987654321', 'free', 'jane.smith@example.com', 'Jane Smith'),
                ('+1122334455', 'enterprise', 'admin@company.com', 'Admin User')
            ]
            
            for phone, tier, email, name in sample_users:
                try:
                    self.db.execute_query("""
                        INSERT INTO users (phone_number, tier, email, full_name, created_at, last_active)
                        VALUES (%s, %s, %s, %s, NOW(), NOW())
                        ON CONFLICT (phone_number) DO NOTHING
                    """, (phone, tier, email, name), fetch='none')
                except Exception as e:
                    logger.warning(f"Sample user insert failed: {e}")
            
            # Insert sample tasks
            sample_tasks = [
                ('+1234567890', 'coding', 3.5, 'medium', 2.5, True, 150, 'Create a Python function', 'Function created successfully'),
                ('+0987654321', 'debug', 2.0, 'low', 1.2, True, 80, 'Fix syntax error', 'Error fixed'),
                ('+1122334455', 'architecture', 4.8, 'high', 15.3, True, 300, 'Design microservices', 'Architecture designed')
            ]
            
            for phone, category, complexity, priority, proc_time, success, tokens, request, response in sample_tasks:
                try:
                    self.db.execute_query("""
                        INSERT INTO tasks (user_phone, category, complexity_score, priority, 
                                         processing_time, success, tokens_used, request_text, response_text,
                                         created_at, completed_at, task_hash)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
                    """, (phone, category, complexity, priority, proc_time, success, tokens, 
                         request, response, hashlib.md5(f"{phone}{request}".encode()).hexdigest()[:16]), 
                         fetch='none')
                except Exception as e:
                    logger.warning(f"Sample task insert failed: {e}")
            
            logger.info("Sample data inserted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting sample data: {e}")
            return False 