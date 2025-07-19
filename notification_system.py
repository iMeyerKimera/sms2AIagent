"""
Notification System Module
Advanced notification and alert system for SMS-to-Cursor AI platform
"""

import os
import json
import logging
import sqlite3
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
import smtplib
try:
    from email.mime.text import MIMEText as MimeText
    from email.mime.multipart import MIMEMultipart as MimeMultipart
except ImportError:
    from email.MIMEText import MIMEText as MimeText
    from email.MIMEMultipart import MIMEMultipart as MimeMultipart
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    SMS = "sms"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    PUSH = "push"

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class NotificationSystem:
    """Advanced notification system with multiple channels and smart routing"""
    
    def __init__(self):
        self.db_path = "notifications.db"
        self._init_database()
        self._load_config()
        
    def _init_database(self):
        """Initialize notification database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Notification templates
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                type TEXT,
                subject_template TEXT,
                body_template TEXT,
                variables TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Notification history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient TEXT,
                type TEXT,
                subject TEXT,
                body TEXT,
                status TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                delivery_status TEXT,
                error_message TEXT
            )
        ''')
        
        # Subscription preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_phone TEXT PRIMARY KEY,
                email TEXT,
                sms_enabled BOOLEAN DEFAULT 1,
                email_enabled BOOLEAN DEFAULT 0,
                webhook_url TEXT,
                slack_webhook TEXT,
                preferred_channels TEXT,
                quiet_hours_start INTEGER,
                quiet_hours_end INTEGER,
                timezone TEXT DEFAULT 'UTC'
            )
        ''')
        
        # Alert rules
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                condition_type TEXT,
                condition_value TEXT,
                alert_level TEXT,
                notification_channels TEXT,
                enabled BOOLEAN DEFAULT 1,
                cooldown_minutes INTEGER DEFAULT 60,
                last_triggered TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Insert default templates
        self._create_default_templates()
    
    def _load_config(self):
        """Load notification configuration"""
        self.config = {
            'email': {
                'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
                'smtp_port': int(os.environ.get('SMTP_PORT', '587')),
                'smtp_username': os.environ.get('SMTP_USERNAME', ''),
                'smtp_password': os.environ.get('SMTP_PASSWORD', ''),
                'from_email': os.environ.get('FROM_EMAIL', '')
            },
            'slack': {
                'webhook_url': os.environ.get('SLACK_WEBHOOK_URL', ''),
                'default_channel': os.environ.get('SLACK_CHANNEL', '#general')
            },
            'discord': {
                'webhook_url': os.environ.get('DISCORD_WEBHOOK_URL', '')
            },
            'twilio': {
                'account_sid': os.environ.get('TWILIO_ACCOUNT_SID', ''),
                'auth_token': os.environ.get('TWILIO_AUTH_TOKEN', ''),
                'phone_number': os.environ.get('TWILIO_PHONE_NUMBER', '')
            }
        }
    
    def _create_default_templates(self):
        """Create default notification templates"""
        default_templates = [
            {
                'name': 'task_completion',
                'type': 'sms',
                'subject_template': 'Task Completed',
                'body_template': 'Your {category} task has been completed successfully! Processing took {processing_time}s.',
                'variables': 'category,processing_time'
            },
            {
                'name': 'task_failed',
                'type': 'sms',
                'subject_template': 'Task Failed',
                'body_template': 'Sorry, your {category} task failed. Error: {error_message}',
                'variables': 'category,error_message'
            },
            {
                'name': 'rate_limit_warning',
                'type': 'sms',
                'subject_template': 'Rate Limit Warning',
                'body_template': 'You are approaching your {tier} tier limit. {remaining} requests remaining this month.',
                'variables': 'tier,remaining'
            },
            {
                'name': 'system_alert',
                'type': 'email',
                'subject_template': 'System Alert: {alert_type}',
                'body_template': 'System alert triggered:\n\nType: {alert_type}\nSeverity: {severity}\nMessage: {message}\nTime: {timestamp}',
                'variables': 'alert_type,severity,message,timestamp'
            },
            {
                'name': 'user_upgrade',
                'type': 'email',
                'subject_template': 'Welcome to {tier} Tier!',
                'body_template': 'Congratulations! Your account has been upgraded to {tier} tier. You now have access to enhanced features and higher limits.',
                'variables': 'tier'
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for template in default_templates:
            cursor.execute('''
                INSERT OR IGNORE INTO notification_templates 
                (name, type, subject_template, body_template, variables)
                VALUES (?, ?, ?, ?, ?)
            ''', (template['name'], template['type'], template['subject_template'], 
                  template['body_template'], template['variables']))
        
        conn.commit()
        conn.close()
    
    async def send_notification(self, recipient: str, template_name: str, 
                               variables: Dict[str, Any], 
                               channels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send notification using specified template and channels"""
        
        # Get user preferences
        user_prefs = self._get_user_preferences(recipient)
        
        # Determine channels to use
        if not channels:
            channels = self._determine_channels(user_prefs, template_name)
        
        # Check quiet hours
        if self._is_quiet_hours(user_prefs):
            channels = [ch for ch in channels if ch not in ['sms', 'push']]
        
        results = {}
        
        for channel in channels:
            try:
                if channel == 'sms':
                    result = await self._send_sms(recipient, template_name, variables)
                elif channel == 'email':
                    result = await self._send_email(user_prefs.get('email', ''), template_name, variables)
                elif channel == 'webhook':
                    result = await self._send_webhook(user_prefs.get('webhook_url', ''), template_name, variables)
                elif channel == 'slack':
                    result = await self._send_slack(template_name, variables)
                elif channel == 'discord':
                    result = await self._send_discord(template_name, variables)
                else:
                    result = {'success': False, 'error': f'Unknown channel: {channel}'}
                
                results[channel] = result
                
                # Log notification
                self._log_notification(recipient, channel, template_name, variables, result)
                
            except Exception as e:
                logger.error(f"Error sending {channel} notification: {e}")
                results[channel] = {'success': False, 'error': str(e)}
        
        return results
    
    async def _send_sms(self, recipient: str, template_name: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Send SMS notification"""
        try:
            from twilio.rest import Client
            
            template = self._get_template(template_name, 'sms')
            if not template:
                return {'success': False, 'error': 'Template not found'}
            
            message = self._render_template(template['body_template'], variables)
            
            client = Client(
                self.config['twilio']['account_sid'],
                self.config['twilio']['auth_token']
            )
            
            # Send SMS
            twilio_message = client.messages.create(
                body=message,
                from_=self.config['twilio']['phone_number'],
                to=recipient
            )
            
            return {
                'success': True,
                'message_sid': twilio_message.sid,
                'status': twilio_message.status
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _send_email(self, email: str, template_name: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Send email notification"""
        if not email:
            return {'success': False, 'error': 'No email address provided'}
        
        try:
            template = self._get_template(template_name, 'email')
            if not template:
                return {'success': False, 'error': 'Template not found'}
            
            subject = self._render_template(template['subject_template'], variables)
            body = self._render_template(template['body_template'], variables)
            
            # Create message
            msg = MimeMultipart()
            msg['From'] = self.config['email']['from_email']
            msg['To'] = email
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(
                self.config['email']['smtp_server'], 
                self.config['email']['smtp_port']
            )
            server.starttls()
            server.login(
                self.config['email']['smtp_username'],
                self.config['email']['smtp_password']
            )
            
            text = msg.as_string()
            server.sendmail(
                self.config['email']['from_email'], 
                email, 
                text
            )
            server.quit()
            
            return {'success': True, 'message': 'Email sent successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _send_webhook(self, webhook_url: str, template_name: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Send webhook notification"""
        if not webhook_url:
            return {'success': False, 'error': 'No webhook URL provided'}
        
        try:
            template = self._get_template(template_name, 'webhook')
            if not template:
                # Create dynamic webhook payload
                payload = {
                    'event': template_name,
                    'timestamp': datetime.now().isoformat(),
                    'data': variables
                }
            else:
                payload = json.loads(self._render_template(template['body_template'], variables))
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        return {'success': True, 'status_code': response.status}
                    else:
                        return {'success': False, 'error': f'HTTP {response.status}'}
                        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _send_slack(self, template_name: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Send Slack notification"""
        webhook_url = self.config['slack']['webhook_url']
        if not webhook_url:
            return {'success': False, 'error': 'No Slack webhook URL configured'}
        
        try:
            template = self._get_template(template_name, 'slack')
            if template:
                message = self._render_template(template['body_template'], variables)
            else:
                message = f"*{template_name}*\n" + "\n".join([f"• {k}: {v}" for k, v in variables.items()])
            
            payload = {
                'text': message,
                'channel': self.config['slack']['default_channel'],
                'username': 'SMS-Cursor Agent',
                'icon_emoji': ':robot_face:'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        return {'success': True, 'platform': 'slack'}
                    else:
                        return {'success': False, 'error': f'HTTP {response.status}'}
                        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _send_discord(self, template_name: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Send Discord notification"""
        webhook_url = self.config['discord']['webhook_url']
        if not webhook_url:
            return {'success': False, 'error': 'No Discord webhook URL configured'}
        
        try:
            template = self._get_template(template_name, 'discord')
            if template:
                message = self._render_template(template['body_template'], variables)
            else:
                message = f"**{template_name}**\n" + "\n".join([f"• {k}: {v}" for k, v in variables.items()])
            
            payload = {
                'content': message,
                'username': 'SMS-Cursor Agent'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status in [200, 204]:
                        return {'success': True, 'platform': 'discord'}
                    else:
                        return {'success': False, 'error': f'HTTP {response.status}'}
                        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_template(self, name: str, notification_type: str = None) -> Optional[Dict[str, Any]]:
        """Get notification template by name"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if notification_type:
            cursor.execute('''
                SELECT * FROM notification_templates 
                WHERE name = ? AND type = ?
            ''', (name, notification_type))
        else:
            cursor.execute('''
                SELECT * FROM notification_templates 
                WHERE name = ?
            ''', (name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'subject_template': row[3],
                'body_template': row[4],
                'variables': row[5].split(',') if row[5] else []
            }
        return None
    
    def _render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Render template with variables"""
        try:
            return template.format(**variables)
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}")
            return template
    
    def _get_user_preferences(self, phone_number: str) -> Dict[str, Any]:
        """Get user notification preferences"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM user_preferences WHERE user_phone = ?
        ''', (phone_number,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'phone_number': row[0],
                'email': row[1],
                'sms_enabled': bool(row[2]),
                'email_enabled': bool(row[3]),
                'webhook_url': row[4],
                'slack_webhook': row[5],
                'preferred_channels': row[6].split(',') if row[6] else ['sms'],
                'quiet_hours_start': row[7],
                'quiet_hours_end': row[8],
                'timezone': row[9]
            }
        else:
            # Return defaults for new user
            return {
                'phone_number': phone_number,
                'sms_enabled': True,
                'email_enabled': False,
                'preferred_channels': ['sms'],
                'timezone': 'UTC'
            }
    
    def _determine_channels(self, user_prefs: Dict[str, Any], template_name: str) -> List[str]:
        """Determine which channels to use for notification"""
        channels = []
        
        # Check user preferences
        if user_prefs.get('sms_enabled', True):
            channels.append('sms')
        
        if user_prefs.get('email_enabled', False) and user_prefs.get('email'):
            channels.append('email')
        
        if user_prefs.get('webhook_url'):
            channels.append('webhook')
        
        # Add admin channels for system alerts
        if template_name.startswith('system_') or template_name.startswith('alert_'):
            if self.config['slack']['webhook_url']:
                channels.append('slack')
            if self.config['discord']['webhook_url']:
                channels.append('discord')
        
        return channels
    
    def _is_quiet_hours(self, user_prefs: Dict[str, Any]) -> bool:
        """Check if current time is within user's quiet hours"""
        start_hour = user_prefs.get('quiet_hours_start')
        end_hour = user_prefs.get('quiet_hours_end')
        
        if start_hour is None or end_hour is None:
            return False
        
        current_hour = datetime.now().hour
        
        if start_hour <= end_hour:
            return start_hour <= current_hour <= end_hour
        else:
            # Quiet hours span midnight
            return current_hour >= start_hour or current_hour <= end_hour
    
    def _log_notification(self, recipient: str, channel: str, template_name: str, 
                         variables: Dict[str, Any], result: Dict[str, Any]):
        """Log notification attempt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notification_history 
            (recipient, type, subject, body, status, delivery_status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            recipient,
            channel,
            template_name,
            json.dumps(variables),
            'sent' if result['success'] else 'failed',
            'delivered' if result['success'] else 'failed',
            result.get('error', '')
        ))
        
        conn.commit()
        conn.close()
    
    def setup_alert_rules(self):
        """Setup default alert rules"""
        default_rules = [
            {
                'name': 'High Error Rate',
                'condition_type': 'error_rate_threshold',
                'condition_value': '15',  # 15% error rate
                'alert_level': 'warning',
                'notification_channels': 'slack,email',
                'cooldown_minutes': 30
            },
            {
                'name': 'System Down',
                'condition_type': 'system_health',
                'condition_value': 'critical',
                'alert_level': 'critical',
                'notification_channels': 'slack,discord,email,sms',
                'cooldown_minutes': 5
            },
            {
                'name': 'High Response Time',
                'condition_type': 'response_time_threshold',
                'condition_value': '30',  # 30 seconds
                'alert_level': 'warning',
                'notification_channels': 'slack',
                'cooldown_minutes': 60
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for rule in default_rules:
            cursor.execute('''
                INSERT OR IGNORE INTO alert_rules 
                (name, condition_type, condition_value, alert_level, notification_channels, cooldown_minutes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (rule['name'], rule['condition_type'], rule['condition_value'],
                  rule['alert_level'], rule['notification_channels'], rule['cooldown_minutes']))
        
        conn.commit()
        conn.close()
    
    def check_alert_conditions(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if any alert conditions are triggered"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM alert_rules WHERE enabled = 1')
        rules = cursor.fetchall()
        
        triggered_alerts = []
        
        for rule in rules:
            rule_data = {
                'id': rule[0],
                'name': rule[1],
                'condition_type': rule[2],
                'condition_value': rule[3],
                'alert_level': rule[4],
                'notification_channels': rule[5].split(','),
                'cooldown_minutes': rule[6],
                'last_triggered': rule[7]
            }
            
            # Check cooldown
            if rule_data['last_triggered']:
                last_triggered = datetime.fromisoformat(rule_data['last_triggered'])
                if datetime.now() - last_triggered < timedelta(minutes=rule_data['cooldown_minutes']):
                    continue
            
            # Check condition
            if self._evaluate_condition(rule_data, metrics):
                triggered_alerts.append(rule_data)
                
                # Update last triggered time
                cursor.execute('''
                    UPDATE alert_rules 
                    SET last_triggered = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (rule_data['id'],))
        
        conn.commit()
        conn.close()
        
        return triggered_alerts
    
    def _evaluate_condition(self, rule: Dict[str, Any], metrics: Dict[str, Any]) -> bool:
        """Evaluate if alert condition is met"""
        condition_type = rule['condition_type']
        threshold = float(rule['condition_value']) if rule['condition_value'].replace('.', '').isdigit() else rule['condition_value']
        
        if condition_type == 'error_rate_threshold':
            return metrics.get('error_rate', 0) > threshold
        elif condition_type == 'response_time_threshold':
            return metrics.get('avg_response_time', 0) > threshold
        elif condition_type == 'system_health':
            return metrics.get('health_status') == threshold
        elif condition_type == 'active_users_low':
            return metrics.get('active_users', 0) < threshold
        
        return False

# Convenience functions for common notifications
async def notify_task_completion(phone_number: str, task_data: Dict[str, Any]):
    """Send task completion notification"""
    notifier = NotificationSystem()
    await notifier.send_notification(
        phone_number, 
        'task_completion', 
        {
            'category': task_data.get('category', 'general'),
            'processing_time': task_data.get('processing_time', 0)
        }
    )

async def notify_system_alert(alert_type: str, severity: str, message: str):
    """Send system alert to administrators"""
    notifier = NotificationSystem()
    await notifier.send_notification(
        'admin',
        'system_alert',
        {
            'alert_type': alert_type,
            'severity': severity,
            'message': message,
            'timestamp': datetime.now().isoformat()
        },
        channels=['slack', 'discord', 'email']
    )

async def notify_rate_limit_warning(phone_number: str, tier: str, remaining: int):
    """Send rate limit warning"""
    notifier = NotificationSystem()
    await notifier.send_notification(
        phone_number,
        'rate_limit_warning',
        {
            'tier': tier,
            'remaining': remaining
        }
    ) 