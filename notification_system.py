"""
Enhanced SMS-to-Cursor AI Agent - Notification System
Multi-channel notification system with PostgreSQL integration
"""

import os
import json
import logging
import smtplib
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from email.mime.text import MIMEText as MimeText
from email.mime.multipart import MIMEMultipart as MimeMultipart
from database_manager import get_database_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global database manager instance  
db = get_database_manager()

class NotificationSystem:
    """
    Comprehensive notification system supporting multiple channels with PostgreSQL integration
    """
    
    def __init__(self):
        """Initialize notification system with PostgreSQL database manager"""
        self.db = get_database_manager()
        
        # Email configuration
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME')
        self.smtp_password = os.environ.get('SMTP_PASSWORD')
        self.from_email = os.environ.get('FROM_EMAIL', self.smtp_username)
        
        # Webhook URLs
        self.slack_webhook = os.environ.get('SLACK_WEBHOOK_URL')
        self.discord_webhook = os.environ.get('DISCORD_WEBHOOK_URL')
        
        # Twilio configuration
        self.twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.environ.get('TWILIO_PHONE_NUMBER')
        
        logger.info("Notification System initialized with PostgreSQL")
    
    def get_user_preferences(self, phone_number: str) -> Dict[str, Any]:
        """Get user notification preferences from PostgreSQL"""
        try:
            preferences = self.db.execute_query("""
                SELECT * FROM user_preferences WHERE user_phone = %s
            """, (phone_number,), db_type='notifications', fetch='one')
            
            if preferences:
                return dict(preferences)
            
            # Return default preferences if none found
            return {
                'user_phone': phone_number,
                'email': None,
                'sms_enabled': True,
                'email_enabled': False,
                'webhook_url': None,
                'slack_webhook': None,
                'preferred_channels': ['sms'],
                'quiet_hours_start': None,
                'quiet_hours_end': None,
                'timezone': 'UTC'
            }
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return {
                'user_phone': phone_number,
                'sms_enabled': True,
                'email_enabled': False,
                'preferred_channels': ['sms']
            }
    
    def update_user_preferences(self, phone_number: str, preferences: Dict[str, Any]) -> bool:
        """Update user notification preferences"""
        try:
            self.db.execute_query("""
                INSERT INTO user_preferences (
                    user_phone, email, sms_enabled, email_enabled, webhook_url,
                    slack_webhook, preferred_channels, quiet_hours_start, 
                    quiet_hours_end, timezone, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (user_phone) 
                DO UPDATE SET
                    email = EXCLUDED.email,
                    sms_enabled = EXCLUDED.sms_enabled,
                    email_enabled = EXCLUDED.email_enabled,
                    webhook_url = EXCLUDED.webhook_url,
                    slack_webhook = EXCLUDED.slack_webhook,
                    preferred_channels = EXCLUDED.preferred_channels,
                    quiet_hours_start = EXCLUDED.quiet_hours_start,
                    quiet_hours_end = EXCLUDED.quiet_hours_end,
                    timezone = EXCLUDED.timezone,
                    updated_at = NOW()
            """, (
                phone_number,
                preferences.get('email'),
                preferences.get('sms_enabled', True),
                preferences.get('email_enabled', False),
                preferences.get('webhook_url'),
                preferences.get('slack_webhook'),
                json.dumps(preferences.get('preferred_channels', ['sms'])),
                preferences.get('quiet_hours_start'),
                preferences.get('quiet_hours_end'),
                preferences.get('timezone', 'UTC')
            ), db_type='notifications', fetch='none')
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False
    
    def is_quiet_hours(self, user_preferences: Dict[str, Any]) -> bool:
        """Check if current time is within user's quiet hours"""
        try:
            quiet_start = user_preferences.get('quiet_hours_start')
            quiet_end = user_preferences.get('quiet_hours_end')
            
            if quiet_start is None or quiet_end is None:
                return False
            
            now = datetime.now().hour
            
            if quiet_start <= quiet_end:
                return quiet_start <= now < quiet_end
            else:  # Spans midnight
                return now >= quiet_start or now < quiet_end
                
        except Exception as e:
            logger.error(f"Error checking quiet hours: {e}")
            return False
    
    def get_notification_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get notification template from PostgreSQL"""
        try:
            template = self.db.execute_query("""
                SELECT * FROM notification_templates 
                WHERE name = %s AND active = true
            """, (template_name,), db_type='notifications', fetch='one')
            
            return dict(template) if template else None
            
        except Exception as e:
            logger.error(f"Error getting notification template: {e}")
            return None
    
    def render_template(self, template: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, str]:
        """Render notification template with variables"""
        try:
            subject = template.get('subject_template', '')
            body = template.get('body_template', '')
            
            # Simple template variable replacement
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                subject = subject.replace(placeholder, str(value))
                body = body.replace(placeholder, str(value))
            
            return {
                'subject': subject,
                'body': body
            }
            
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            return {
                'subject': template.get('subject_template', ''),
                'body': template.get('body_template', '')
            }
    
    def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send SMS notification via Twilio"""
        try:
            if not all([self.twilio_account_sid, self.twilio_auth_token, self.twilio_phone_number]):
                return {'success': False, 'error': 'Twilio not configured'}
            
            from twilio.rest import Client
            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            
            message_obj = client.messages.create(
                body=message,
                from_=self.twilio_phone_number,
                to=phone_number
            )
            
            return {
                'success': True,
                'message_sid': message_obj.sid,
                'status': message_obj.status
            }
            
        except Exception as e:
            logger.error(f"Error sending SMS to {phone_number}: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_email(self, email: str, subject: str, body: str) -> Dict[str, Any]:
        """Send email notification via SMTP"""
        try:
            if not all([self.smtp_username, self.smtp_password]):
                return {'success': False, 'error': 'Email not configured'}
            
            msg = MimeMultipart()
            msg['From'] = self.from_email
            msg['To'] = email
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.from_email, email, text)
            server.quit()
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error sending email to {email}: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_slack(self, message: str, webhook_url: str = None) -> Dict[str, Any]:
        """Send Slack notification via webhook"""
        try:
            url = webhook_url or self.slack_webhook
            if not url:
                return {'success': False, 'error': 'Slack webhook not configured'}
            
            payload = {
                'text': message,
                'username': 'SMS AI Assistant',
                'icon_emoji': ':robot_face:'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            return {'success': True, 'status_code': response.status_code}
            
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_discord(self, message: str, webhook_url: str = None) -> Dict[str, Any]:
        """Send Discord notification via webhook"""
        try:
            url = webhook_url or self.discord_webhook
            if not url:
                return {'success': False, 'error': 'Discord webhook not configured'}
            
            payload = {
                'content': message,
                'username': 'SMS AI Assistant'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            return {'success': True, 'status_code': response.status_code}
            
        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_webhook(self, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send custom webhook notification"""
        try:
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            return {'success': True, 'status_code': response.status_code}
            
        except Exception as e:
            logger.error(f"Error sending webhook to {url}: {e}")
            return {'success': False, 'error': str(e)}
    
    def log_notification(self, recipient: str, notification_type: str, subject: str, 
                        body: str, status: str, error_message: str = None,
                        template_id: int = None) -> Optional[int]:
        """Log notification to PostgreSQL database"""
        try:
            result = self.db.execute_query("""
                INSERT INTO notification_history (
                    recipient, type, subject, body, status, sent_at,
                    error_message, template_id, metadata
                ) VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s, %s)
                RETURNING id
            """, (
                recipient, notification_type, subject, body, status,
                error_message, template_id, json.dumps({})
            ), db_type='notifications', fetch='one')
            
            return result['id'] if result else None
            
        except Exception as e:
            logger.error(f"Error logging notification: {e}")
            return None
    
    def send_notification(self, phone_number: str, template_name: str, 
                         variables: Dict[str, Any] = None, 
                         force_channels: List[str] = None) -> Dict[str, Any]:
        """Send multi-channel notification using template"""
        try:
            variables = variables or {}
            
            # Get user preferences
            user_prefs = self.get_user_preferences(phone_number)
            
            # Check quiet hours
            if self.is_quiet_hours(user_prefs):
                logger.info(f"Skipping notification to {phone_number} - quiet hours")
                return {'success': False, 'reason': 'quiet_hours'}
            
            # Get notification template
            template = self.get_notification_template(template_name)
            if not template:
                logger.error(f"Template not found: {template_name}")
                return {'success': False, 'error': 'Template not found'}
            
            # Render template
            rendered = self.render_template(template, variables)
            subject = rendered['subject']
            body = rendered['body']
            
            # Determine channels to use
            if force_channels:
                channels = force_channels
            else:
                preferred = user_prefs.get('preferred_channels', ['sms'])
                if isinstance(preferred, str):
                    preferred = json.loads(preferred)
                channels = preferred
            
            results = {}
            
            # Send SMS
            if 'sms' in channels and user_prefs.get('sms_enabled', True):
                sms_result = self.send_sms(phone_number, body)
                results['sms'] = sms_result
                
                # Log SMS notification
                self.log_notification(
                    phone_number, 'sms', subject, body,
                    'sent' if sms_result['success'] else 'failed',
                    sms_result.get('error'), template.get('id')
                )
            
            # Send Email
            if 'email' in channels and user_prefs.get('email_enabled', False):
                email = user_prefs.get('email')
                if email:
                    email_result = self.send_email(email, subject, body)
                    results['email'] = email_result
                    
                    # Log email notification
                    self.log_notification(
                        email, 'email', subject, body,
                        'sent' if email_result['success'] else 'failed',
                        email_result.get('error'), template.get('id')
                    )
            
            # Send Slack
            if 'slack' in channels:
                slack_webhook = user_prefs.get('slack_webhook') or self.slack_webhook
                if slack_webhook:
                    slack_message = f"*{subject}*\n{body}"
                    slack_result = self.send_slack(slack_message, slack_webhook)
                    results['slack'] = slack_result
                    
                    # Log Slack notification
                    self.log_notification(
                        phone_number, 'slack', subject, body,
                        'sent' if slack_result['success'] else 'failed',
                        slack_result.get('error'), template.get('id')
                    )
            
            # Send Discord
            if 'discord' in channels:
                discord_message = f"**{subject}**\n{body}"
                discord_result = self.send_discord(discord_message)
                results['discord'] = discord_result
                
                # Log Discord notification
                self.log_notification(
                    phone_number, 'discord', subject, body,
                    'sent' if discord_result['success'] else 'failed',
                    discord_result.get('error'), template.get('id')
                )
            
            # Send Custom Webhook
            if 'webhook' in channels:
                webhook_url = user_prefs.get('webhook_url')
                if webhook_url:
                    webhook_data = {
                        'phone_number': phone_number,
                        'subject': subject,
                        'body': body,
                        'template': template_name,
                        'variables': variables,
                        'timestamp': datetime.now().isoformat()
                    }
                    webhook_result = self.send_webhook(webhook_url, webhook_data)
                    results['webhook'] = webhook_result
                    
                    # Log webhook notification
                    self.log_notification(
                        webhook_url, 'webhook', subject, body,
                        'sent' if webhook_result['success'] else 'failed',
                        webhook_result.get('error'), template.get('id')
                    )
            
            # Determine overall success
            success = any(result.get('success', False) for result in results.values())
            
            return {
                'success': success,
                'channels_attempted': list(results.keys()),
                'results': results,
                'template_used': template_name
            }
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_system_alert(self, alert_type: str, message: str, level: str = 'info') -> Dict[str, Any]:
        """Send system alert to administrators"""
        try:
            # Get admin notification channels
            admin_channels = ['slack', 'discord']
            if level in ['error', 'critical']:
                admin_channels.append('email')
            
            alert_message = f"[{level.upper()}] {alert_type}: {message}"
            
            results = {}
            
            # Send to Slack
            if self.slack_webhook:
                emoji_map = {'info': ':information_source:', 'warning': ':warning:', 'error': ':x:', 'critical': ':rotating_light:'}
                slack_msg = f"{emoji_map.get(level, ':robot_face:')} {alert_message}"
                results['slack'] = self.send_slack(slack_msg)
            
            # Send to Discord
            if self.discord_webhook:
                results['discord'] = self.send_discord(alert_message)
            
            # Log system alert
            self.log_notification(
                'system', 'alert', f"{alert_type} Alert", alert_message,
                'sent' if any(r.get('success') for r in results.values()) else 'failed'
            )
            
            return {
                'success': any(result.get('success', False) for result in results.values()),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error sending system alert: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_notification_history(self, phone_number: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get notification history from PostgreSQL"""
        try:
            if phone_number:
                notifications = self.db.execute_query("""
                    SELECT * FROM notification_history 
                    WHERE recipient = %s 
                    ORDER BY sent_at DESC 
                    LIMIT %s
                """, (phone_number, limit), db_type='notifications')
            else:
                notifications = self.db.execute_query("""
                    SELECT * FROM notification_history 
                    ORDER BY sent_at DESC 
                    LIMIT %s
                """, (limit,), db_type='notifications')
            
            return [dict(notif) for notif in notifications] if notifications else []
            
        except Exception as e:
            logger.error(f"Error getting notification history: {e}")
            return []
    
    def create_notification_template(self, name: str, template_type: str, 
                                   subject_template: str, body_template: str,
                                   variables: Dict[str, str] = None) -> bool:
        """Create a new notification template"""
        try:
            self.db.execute_query("""
                INSERT INTO notification_templates (
                    name, type, subject_template, body_template, variables, created_at, active
                ) VALUES (%s, %s, %s, %s, %s, NOW(), true)
                ON CONFLICT (name) 
                DO UPDATE SET
                    type = EXCLUDED.type,
                    subject_template = EXCLUDED.subject_template,
                    body_template = EXCLUDED.body_template,
                    variables = EXCLUDED.variables,
                    updated_at = NOW()
            """, (
                name, template_type, subject_template, body_template,
                json.dumps(variables or {})
            ), db_type='notifications', fetch='none')
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating notification template: {e}")
            return False

# Global notification system instance
notification_system = NotificationSystem() 