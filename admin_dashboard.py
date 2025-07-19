"""
Admin Dashboard Module
Comprehensive admin interface for SMS-to-Cursor AI system monitoring and management
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
import hashlib
import secrets
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Create Blueprint for admin routes
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin authentication
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = hashlib.sha256(os.environ.get("ADMIN_PASSWORD", "admin123").encode()).hexdigest()

def require_admin_auth(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_authenticated'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

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
            return render_template('admin/login.html', error="Invalid credentials")
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.pop('admin_authenticated', None)
    session.pop('admin_user', None)
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@require_admin_auth
def dashboard():
    """Main admin dashboard"""
    analytics = AdminAnalytics()
    
    # Get overview statistics
    overview = analytics.get_system_overview()
    recent_activity = analytics.get_recent_activity()
    performance_metrics = analytics.get_performance_metrics()
    user_growth = analytics.get_user_growth_data()
    
    return render_template('admin/dashboard.html', 
                         overview=overview,
                         recent_activity=recent_activity,
                         performance_metrics=performance_metrics,
                         user_growth=user_growth)

@admin_bp.route('/users')
@require_admin_auth
def users():
    """User management page"""
    analytics = AdminAnalytics()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    users_data = analytics.get_users_paginated(page, per_page)
    
    return render_template('admin/users.html', 
                         users=users_data['users'],
                         pagination=users_data['pagination'])

@admin_bp.route('/users/<phone_number>')
@require_admin_auth
def user_detail(phone_number):
    """Individual user detail page"""
    analytics = AdminAnalytics()
    user_data = analytics.get_user_detail(phone_number)
    
    if not user_data:
        return "User not found", 404
    
    return render_template('admin/user_detail.html', user_data=user_data)

@admin_bp.route('/analytics')
@require_admin_auth
def analytics():
    """Analytics and reporting page"""
    analytics = AdminAnalytics()
    
    # Get date range from query parameters
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    analytics_data = analytics.get_detailed_analytics(start_date, end_date)
    
    return render_template('admin/analytics.html', 
                         analytics=analytics_data,
                         start_date=start_date,
                         end_date=end_date)

@admin_bp.route('/system')
@require_admin_auth
def system():
    """System monitoring and configuration"""
    analytics = AdminAnalytics()
    
    system_health = analytics.get_system_health()
    error_logs = analytics.get_recent_errors()
    config_info = analytics.get_system_config()
    
    return render_template('admin/system.html',
                         system_health=system_health,
                         error_logs=error_logs,
                         config=config_info)

@admin_bp.route('/api/user/<phone_number>/tier', methods=['POST'])
@require_admin_auth
def update_user_tier():
    """API endpoint to update user tier"""
    phone_number = request.json.get('phone_number')
    new_tier = request.json.get('tier')
    
    if new_tier not in ['free', 'premium', 'enterprise']:
        return jsonify({'error': 'Invalid tier'}), 400
    
    analytics = AdminAnalytics()
    success = analytics.update_user_tier(phone_number, new_tier)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to update user tier'}), 500

@admin_bp.route('/api/analytics/realtime')
@require_admin_auth
def realtime_analytics():
    """Real-time analytics API endpoint"""
    analytics = AdminAnalytics()
    data = analytics.get_realtime_metrics()
    return jsonify(data)

class AdminAnalytics:
    """Analytics and data management for admin dashboard"""
    
    def __init__(self):
        self.db_path = "task_analytics.db"
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get high-level system overview statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # Active users (last 30 days)
        cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE last_active >= date('now', '-30 days')
        """)
        active_users = cursor.fetchone()[0]
        
        # Total tasks
        cursor.execute("SELECT COUNT(*) FROM tasks")
        total_tasks = cursor.fetchone()[0]
        
        # Tasks today
        cursor.execute("""
            SELECT COUNT(*) FROM tasks 
            WHERE date(created_at) = date('now')
        """)
        tasks_today = cursor.fetchone()[0]
        
        # Success rate
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN success = 1 THEN 1 END) * 100.0 / COUNT(*) as success_rate
            FROM tasks 
            WHERE created_at >= date('now', '-7 days')
        """)
        success_rate = cursor.fetchone()[0] or 0
        
        # Average processing time
        cursor.execute("""
            SELECT AVG(processing_time) 
            FROM tasks 
            WHERE success = 1 AND created_at >= date('now', '-7 days')
        """)
        avg_processing_time = cursor.fetchone()[0] or 0
        
        # User tier distribution
        cursor.execute("""
            SELECT tier, COUNT(*) 
            FROM users 
            GROUP BY tier
        """)
        tier_distribution = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_tasks': total_tasks,
            'tasks_today': tasks_today,
            'success_rate': round(success_rate, 2),
            'avg_processing_time': round(avg_processing_time, 2),
            'tier_distribution': tier_distribution
        }
    
    def get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent system activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                t.user_phone,
                t.category,
                t.complexity_score,
                t.success,
                t.created_at,
                t.processing_time,
                u.tier
            FROM tasks t
            LEFT JOIN users u ON t.user_phone = u.phone_number
            ORDER BY t.created_at DESC
            LIMIT ?
        """, (limit,))
        
        activities = []
        for row in cursor.fetchall():
            activities.append({
                'user_phone': row[0],
                'category': row[1],
                'complexity_score': row[2],
                'success': bool(row[3]),
                'created_at': row[4],
                'processing_time': row[5],
                'user_tier': row[6]
            })
        
        conn.close()
        return activities
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tasks by category (last 7 days)
        cursor.execute("""
            SELECT category, COUNT(*) 
            FROM tasks 
            WHERE created_at >= date('now', '-7 days')
            GROUP BY category
            ORDER BY COUNT(*) DESC
        """)
        tasks_by_category = dict(cursor.fetchall())
        
        # Processing time trends (last 7 days)
        cursor.execute("""
            SELECT 
                date(created_at) as day,
                AVG(processing_time) as avg_time,
                COUNT(*) as task_count
            FROM tasks 
            WHERE created_at >= date('now', '-7 days') AND success = 1
            GROUP BY date(created_at)
            ORDER BY day
        """)
        processing_trends = [
            {
                'day': row[0],
                'avg_time': round(row[1], 2),
                'task_count': row[2]
            }
            for row in cursor.fetchall()
        ]
        
        # Error rate by category
        cursor.execute("""
            SELECT 
                category,
                COUNT(CASE WHEN success = 0 THEN 1 END) * 100.0 / COUNT(*) as error_rate
            FROM tasks 
            WHERE created_at >= date('now', '-7 days')
            GROUP BY category
        """)
        error_rates = {row[0]: round(row[1], 2) for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'tasks_by_category': tasks_by_category,
            'processing_trends': processing_trends,
            'error_rates': error_rates
        }
    
    def get_user_growth_data(self) -> List[Dict[str, Any]]:
        """Get user growth data for charts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                date(created_at) as day,
                COUNT(*) as new_users
            FROM users 
            WHERE created_at >= date('now', '-30 days')
            GROUP BY date(created_at)
            ORDER BY day
        """)
        
        growth_data = [
            {
                'day': row[0],
                'new_users': row[1]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return growth_data
    
    def get_users_paginated(self, page: int, per_page: int) -> Dict[str, Any]:
        """Get paginated users list"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # Get paginated users
        offset = (page - 1) * per_page
        cursor.execute("""
            SELECT 
                u.phone_number,
                u.tier,
                u.created_at,
                u.last_active,
                u.total_requests,
                u.monthly_requests,
                COUNT(t.id) as recent_tasks
            FROM users u
            LEFT JOIN tasks t ON u.phone_number = t.user_phone 
                AND t.created_at >= date('now', '-7 days')
            GROUP BY u.phone_number
            ORDER BY u.last_active DESC
            LIMIT ? OFFSET ?
        """, (per_page, offset))
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'phone_number': row[0],
                'tier': row[1],
                'created_at': row[2],
                'last_active': row[3],
                'total_requests': row[4],
                'monthly_requests': row[5],
                'recent_tasks': row[6]
            })
        
        conn.close()
        
        # Calculate pagination info
        total_pages = (total_users + per_page - 1) // per_page
        
        return {
            'users': users,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_users': total_users,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages
            }
        }
    
    def get_user_detail(self, phone_number: str) -> Dict[str, Any]:
        """Get detailed information for a specific user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User info
        cursor.execute("SELECT * FROM users WHERE phone_number = ?", (phone_number,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return None
        
        # Task statistics
        cursor.execute("""
            SELECT 
                category,
                COUNT(*) as count,
                AVG(complexity_score) as avg_complexity,
                AVG(processing_time) as avg_time,
                COUNT(CASE WHEN success = 1 THEN 1 END) * 100.0 / COUNT(*) as success_rate
            FROM tasks 
            WHERE user_phone = ?
            GROUP BY category
        """, (phone_number,))
        
        task_stats = [
            {
                'category': row[0],
                'count': row[1],
                'avg_complexity': round(row[2], 2),
                'avg_time': round(row[3], 2),
                'success_rate': round(row[4], 2)
            }
            for row in cursor.fetchall()
        ]
        
        # Recent tasks
        cursor.execute("""
            SELECT category, complexity_score, success, created_at, processing_time
            FROM tasks 
            WHERE user_phone = ?
            ORDER BY created_at DESC 
            LIMIT 20
        """, (phone_number,))
        
        recent_tasks = [
            {
                'category': row[0],
                'complexity_score': row[1],
                'success': bool(row[2]),
                'created_at': row[3],
                'processing_time': row[4]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            'user_info': {
                'phone_number': user[0],
                'tier': user[1],
                'created_at': user[2],
                'last_active': user[3],
                'total_requests': user[4],
                'monthly_requests': user[5]
            },
            'task_statistics': task_stats,
            'recent_tasks': recent_tasks
        }
    
    def get_detailed_analytics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get detailed analytics for a date range"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Daily task volume
        cursor.execute("""
            SELECT 
                date(created_at) as day,
                COUNT(*) as total_tasks,
                COUNT(CASE WHEN success = 1 THEN 1 END) as successful_tasks,
                AVG(processing_time) as avg_processing_time
            FROM tasks 
            WHERE date(created_at) BETWEEN ? AND ?
            GROUP BY date(created_at)
            ORDER BY day
        """, (start_date, end_date))
        
        daily_stats = [
            {
                'day': row[0],
                'total_tasks': row[1],
                'successful_tasks': row[2],
                'success_rate': round((row[2] / row[1]) * 100, 2) if row[1] > 0 else 0,
                'avg_processing_time': round(row[3], 2) if row[3] else 0
            }
            for row in cursor.fetchall()
        ]
        
        # Category breakdown
        cursor.execute("""
            SELECT 
                category,
                COUNT(*) as count,
                AVG(complexity_score) as avg_complexity,
                COUNT(CASE WHEN success = 1 THEN 1 END) * 100.0 / COUNT(*) as success_rate
            FROM tasks 
            WHERE date(created_at) BETWEEN ? AND ?
            GROUP BY category
            ORDER BY count DESC
        """, (start_date, end_date))
        
        category_stats = [
            {
                'category': row[0],
                'count': row[1],
                'avg_complexity': round(row[2], 2),
                'success_rate': round(row[3], 2)
            }
            for row in cursor.fetchall()
        ]
        
        # User tier analysis
        cursor.execute("""
            SELECT 
                u.tier,
                COUNT(t.id) as task_count,
                AVG(t.complexity_score) as avg_complexity,
                COUNT(CASE WHEN t.success = 1 THEN 1 END) * 100.0 / COUNT(t.id) as success_rate
            FROM tasks t
            JOIN users u ON t.user_phone = u.phone_number
            WHERE date(t.created_at) BETWEEN ? AND ?
            GROUP BY u.tier
        """, (start_date, end_date))
        
        tier_analysis = [
            {
                'tier': row[0],
                'task_count': row[1],
                'avg_complexity': round(row[2], 2),
                'success_rate': round(row[3], 2)
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            'daily_stats': daily_stats,
            'category_stats': category_stats,
            'tier_analysis': tier_analysis
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Recent error rate
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN success = 0 THEN 1 END) * 100.0 / COUNT(*) as error_rate
            FROM tasks 
            WHERE created_at >= datetime('now', '-1 hour')
        """)
        recent_error_rate = cursor.fetchone()[0] or 0
        
        # Average response time (last hour)
        cursor.execute("""
            SELECT AVG(processing_time)
            FROM tasks 
            WHERE success = 1 AND created_at >= datetime('now', '-1 hour')
        """)
        avg_response_time = cursor.fetchone()[0] or 0
        
        # Active users (last hour)
        cursor.execute("""
            SELECT COUNT(DISTINCT user_phone)
            FROM tasks 
            WHERE created_at >= datetime('now', '-1 hour')
        """)
        active_users_hour = cursor.fetchone()[0]
        
        conn.close()
        
        # Determine health status
        health_status = "healthy"
        if recent_error_rate > 10:
            health_status = "warning"
        if recent_error_rate > 25 or avg_response_time > 30:
            health_status = "critical"
        
        return {
            'status': health_status,
            'error_rate': round(recent_error_rate, 2),
            'avg_response_time': round(avg_response_time, 2),
            'active_users_hour': active_users_hour,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent error logs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_phone, error_type, error_message, request_text, timestamp
            FROM error_logs
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        errors = [
            {
                'user_phone': row[0],
                'error_type': row[1],
                'error_message': row[2],
                'request_text': row[3][:100] + '...' if len(row[3]) > 100 else row[3],
                'timestamp': row[4]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return errors
    
    def get_system_config(self) -> Dict[str, Any]:
        """Get current system configuration"""
        return {
            'environment': os.environ.get('FLASK_ENV', 'development'),
            'testing_mode': os.environ.get('TESTING_MODE', 'false'),
            'voice_assistant_enabled': os.environ.get('ENABLE_VOICE_ASSISTANT', 'false'),
            'max_sms_length': os.environ.get('MAX_SMS_LENGTH', '160'),
            'database_path': self.db_path,
            'admin_username': ADMIN_USERNAME
        }
    
    def update_user_tier(self, phone_number: str, new_tier: str) -> bool:
        """Update a user's tier"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users 
                SET tier = ?
                WHERE phone_number = ?
            """, (new_tier, phone_number))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating user tier: {e}")
            return False
    
    def get_realtime_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for dashboard updates"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tasks in last 5 minutes
        cursor.execute("""
            SELECT COUNT(*) 
            FROM tasks 
            WHERE created_at >= datetime('now', '-5 minutes')
        """)
        recent_tasks = cursor.fetchone()[0]
        
        # Current active users (last 10 minutes)
        cursor.execute("""
            SELECT COUNT(DISTINCT user_phone)
            FROM tasks 
            WHERE created_at >= datetime('now', '-10 minutes')
        """)
        active_users = cursor.fetchone()[0]
        
        # Success rate (last hour)
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN success = 1 THEN 1 END) * 100.0 / COUNT(*)
            FROM tasks 
            WHERE created_at >= datetime('now', '-1 hour')
        """)
        success_rate = cursor.fetchone()[0] or 100
        
        conn.close()
        
        return {
            'recent_tasks': recent_tasks,
            'active_users': active_users,
            'success_rate': round(success_rate, 1),
            'timestamp': datetime.now().isoformat()
        } 