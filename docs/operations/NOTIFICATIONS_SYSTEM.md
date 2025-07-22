# 📢 Notifications System Documentation

## 🔧 **System Overview**

The Enhanced SMS-to-Cursor AI Agent includes a sophisticated multi-channel notification system that provides real-time alerts, user communications, and system monitoring capabilities.

### **Key Features**
- **Multi-Channel Support**: SMS, Email, Slack, Discord, Webhooks
- **Smart Routing**: Intelligent notification delivery based on user preferences
- **Template System**: Customizable notification templates with variables
- **Alert Rules**: Configurable system alert conditions and thresholds
- **User Preferences**: Per-user notification settings and quiet hours
- **Delivery Tracking**: Complete notification history and delivery status
- **Rate Limiting**: Built-in rate limiting to prevent spam
- **Retry Logic**: Automatic retry for failed deliveries

---

## 🏗️ **System Architecture**

### **Core Components**

1. **NotificationSystem Class** (`notification_system.py`)
   - Main orchestrator for all notification activities
   - Handles channel routing and delivery
   - Manages templates and user preferences

2. **Database Schema** (`notifications.db`)
   - **notification_templates**: Reusable message templates
   - **notification_history**: Complete delivery logs
   - **user_preferences**: Per-user notification settings
   - **alert_rules**: System monitoring and alerting rules

3. **Channel Handlers**
   - **SMS**: Twilio API integration
   - **Email**: SMTP with Gmail/custom server support
   - **Slack**: Webhook integration
   - **Discord**: Webhook integration
   - **Custom Webhooks**: Generic HTTP POST notifications

---

## 📋 **Database Schema**

### **notification_templates** Table
```sql
CREATE TABLE notification_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,                    -- Template identifier
    type TEXT,                          -- sms, email, slack, discord
    subject_template TEXT,              -- Subject/title template
    body_template TEXT,                 -- Message body template
    variables TEXT,                     -- JSON array of variables
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Example Templates:**
- `task_completion`: Notify when user task is completed
- `system_alert`: Critical system alerts
- `user_welcome`: Welcome message for new users
- `rate_limit_warning`: Rate limit approaching notification

### **notification_history** Table
```sql
CREATE TABLE notification_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient TEXT,                     -- Phone number, email, or channel
    type TEXT,                         -- sms, email, slack, discord
    subject TEXT,                      -- Message subject/title
    body TEXT,                         -- Message content
    status TEXT,                       -- sent, failed, pending
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivery_status TEXT,              -- delivered, bounced, opened
    error_message TEXT                 -- Error details if failed
);
```

### **user_preferences** Table
```sql
CREATE TABLE user_preferences (
    user_phone TEXT PRIMARY KEY,
    email TEXT,                        -- User's email address
    sms_enabled BOOLEAN DEFAULT 1,     -- SMS notifications enabled
    email_enabled BOOLEAN DEFAULT 0,   -- Email notifications enabled
    webhook_url TEXT,                  -- Custom webhook URL
    slack_webhook TEXT,                -- Personal Slack webhook
    preferred_channels TEXT,           -- JSON array of preferred channels
    quiet_hours_start INTEGER,         -- Quiet hours start (24h format)
    quiet_hours_end INTEGER,           -- Quiet hours end (24h format)
    timezone TEXT DEFAULT 'UTC'       -- User's timezone
);
```

### **alert_rules** Table
```sql
CREATE TABLE alert_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,                         -- Rule name/description
    condition_type TEXT,               -- error_rate, response_time, usage
    condition_value TEXT,              -- Threshold value
    alert_level TEXT,                  -- info, warning, critical
    notification_channels TEXT,        -- JSON array of channels
    enabled BOOLEAN DEFAULT 1,         -- Rule enabled/disabled
    cooldown_minutes INTEGER DEFAULT 60, -- Minimum time between alerts
    last_triggered TIMESTAMP          -- Last time rule was triggered
);
```

---

## ⚙️ **Configuration Guide**

### **Environment Variables**

```bash
# === Email Configuration ===
SMTP_SERVER=smtp.gmail.com           # SMTP server address
SMTP_PORT=587                        # SMTP port (587 for TLS)
SMTP_USERNAME=your_email@gmail.com   # SMTP username
SMTP_PASSWORD=your_app_password      # SMTP password/app password
FROM_EMAIL=your_email@gmail.com      # From email address

# === Slack Integration ===
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SLACK_CHANNEL=#alerts                # Default Slack channel

# === Discord Integration ===
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK

# === Twilio SMS ===
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxx   # Twilio Account SID
TWILIO_AUTH_TOKEN=your_auth_token    # Twilio Auth Token
TWILIO_PHONE_NUMBER=+1234567890      # Twilio phone number
```

### **Gmail Setup for Email Notifications**

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. **Use App Password** in `SMTP_PASSWORD` environment variable

### **Slack Webhook Setup**

1. Go to [Slack API](https://api.slack.com/apps)
2. Create new app → From scratch
3. Choose workspace and app name
4. Go to **Incoming Webhooks**
5. Activate incoming webhooks
6. Add new webhook to workspace
7. Copy webhook URL to `SLACK_WEBHOOK_URL`

### **Discord Webhook Setup**

1. Go to Discord server settings
2. Integrations → Webhooks
3. Create webhook
4. Copy webhook URL to `DISCORD_WEBHOOK_URL`

---

## 🚀 **Usage Examples**

### **Basic Notification Sending**

```python
from notification_system import NotificationSystem

# Initialize system
notifier = NotificationSystem()

# Send simple SMS
notifier.send_sms(
    phone_number="+1234567890",
    message="Your task has been completed!"
)

# Send email with template
notifier.send_email(
    email="user@example.com",
    subject="Task Completion Alert",
    body="Your coding task has been successfully processed.",
    template_name="task_completion"
)

# Send Slack notification
notifier.send_slack_notification(
    message="🚨 System Alert: High error rate detected",
    channel="#alerts",
    level="warning"
)
```

### **Template-Based Notifications**

```python
# Send notification using template
notifier.send_templated_notification(
    template_name="task_completion",
    recipient="+1234567890",
    variables={
        "user_name": "John",
        "task_category": "coding",
        "processing_time": "12.5s",
        "success": True
    }
)
```

### **Multi-Channel Broadcasting**

```python
# Send to multiple channels
notifier.send_multi_channel_notification(
    message="System maintenance scheduled for tonight",
    channels=["sms", "email", "slack"],
    recipients={
        "sms": ["+1234567890", "+0987654321"],
        "email": ["admin@company.com"],
        "slack": ["#general"]
    }
)
```

### **User Preference Management**

```python
# Set user preferences
notifier.update_user_preferences(
    phone_number="+1234567890",
    preferences={
        "email": "user@example.com",
        "sms_enabled": True,
        "email_enabled": True,
        "quiet_hours_start": 22,  # 10 PM
        "quiet_hours_end": 8,     # 8 AM
        "timezone": "America/New_York"
    }
)

# Get user preferences
prefs = notifier.get_user_preferences("+1234567890")
```

---

## 🔔 **Alert System**

### **Built-in Alert Rules**

The system includes several pre-configured alert rules:

1. **High Error Rate**
   - Triggers when error rate > 10% over 15 minutes
   - Sends warning to admin channels

2. **Slow Response Times**
   - Triggers when average response time > 30 seconds
   - Sends performance alert

3. **High Memory Usage**
   - Triggers when memory usage > 80%
   - Sends system resource alert

4. **Database Connection Issues**
   - Triggers on database connection failures
   - Sends critical system alert

### **Custom Alert Rules**

```python
# Create custom alert rule
notifier.create_alert_rule(
    name="High User Activity",
    condition_type="user_activity",
    condition_value="100",  # 100 requests per hour
    alert_level="info",
    notification_channels=["slack", "email"],
    cooldown_minutes=30
)

# Enable/disable alert rules
notifier.toggle_alert_rule("High User Activity", enabled=True)
```

### **Manual Alert Triggering**

```python
# Trigger system alert
notifier.trigger_system_alert(
    level="critical",
    title="Database Connection Lost",
    message="Primary database connection failed. Switching to backup.",
    affected_services=["task_router", "admin_dashboard"]
)
```

---

## 📊 **Admin Dashboard Integration**

### **Notification Management**

The admin dashboard provides comprehensive notification management:

1. **Notification History**
   - View all sent notifications
   - Filter by date, type, status
   - Export notification logs

2. **User Preference Management**
   - View and edit user notification preferences
   - Bulk update settings
   - Manage user communication channels

3. **Template Management**
   - Create and edit notification templates
   - Preview templates with sample data
   - Template usage analytics

4. **Alert Rule Configuration**
   - Create and manage alert rules
   - View alert history and performance
   - Configure alert channels and recipients

### **API Endpoints**

```bash
# Notification history
GET /admin/api/notifications/history?limit=50&type=sms

# User preferences
GET /admin/api/users/{phone}/preferences
PUT /admin/api/users/{phone}/preferences

# Send notification
POST /admin/api/notifications/send
{
    "type": "sms",
    "recipient": "+1234567890",
    "message": "Test notification"
}

# Alert rules
GET /admin/api/alerts/rules
POST /admin/api/alerts/rules
PUT /admin/api/alerts/rules/{id}
DELETE /admin/api/alerts/rules/{id}
```

---

## 🔄 **Advanced Features**

### **Delivery Retry Logic**

Failed notifications are automatically retried with exponential backoff:

```python
retry_config = {
    "max_retries": 3,
    "initial_delay": 60,    # 1 minute
    "max_delay": 3600,      # 1 hour
    "backoff_factor": 2     # Double delay each retry
}
```

### **Rate Limiting**

Built-in rate limiting prevents notification spam:

- **SMS**: 10 per hour per user
- **Email**: 50 per hour per user
- **Slack**: 100 per hour global
- **Discord**: 100 per hour global

### **Quiet Hours Support**

Notifications respect user-defined quiet hours:

```python
# Check if user is in quiet hours
is_quiet = notifier.is_user_in_quiet_hours("+1234567890")

# Send only urgent notifications during quiet hours
if not is_quiet or notification_level == "urgent":
    notifier.send_notification(...)
```

### **Template Variables**

Templates support dynamic variables:

```python
template = {
    "subject": "Task {task_id} - {status}",
    "body": "Hello {user_name}, your {task_category} task has {status}. Processing time: {processing_time}."
}

variables = {
    "task_id": "12345",
    "status": "completed",
    "user_name": "John",
    "task_category": "coding",
    "processing_time": "15.2s"
}
```

---

## 🛠️ **API Reference**

### **NotificationSystem Class Methods**

#### **send_sms(phone_number, message, template_name=None)**
Send SMS notification via Twilio.

**Parameters:**
- `phone_number`: Recipient phone number
- `message`: Message content
- `template_name`: Optional template name

**Returns:** `dict` with success status and message ID

#### **send_email(email, subject, body, template_name=None)**
Send email notification via SMTP.

**Parameters:**
- `email`: Recipient email address
- `subject`: Email subject
- `body`: Email body content
- `template_name`: Optional template name

**Returns:** `dict` with success status and tracking info

#### **send_slack_notification(message, channel=None, level="info")**
Send Slack notification via webhook.

**Parameters:**
- `message`: Message content
- `channel`: Slack channel (optional)
- `level`: Alert level (info, warning, critical)

**Returns:** `dict` with success status

#### **send_multi_channel_notification(message, channels, recipients)**
Send notification to multiple channels.

**Parameters:**
- `message`: Message content
- `channels`: List of channel types
- `recipients`: Dict mapping channels to recipient lists

**Returns:** `dict` with per-channel results

#### **create_notification_template(name, type, subject_template, body_template, variables)**
Create new notification template.

**Parameters:**
- `name`: Template name
- `type`: Notification type (sms, email, slack, discord)
- `subject_template`: Subject template with variables
- `body_template`: Body template with variables
- `variables`: List of variable names

**Returns:** Template ID

#### **get_notification_history(limit=50, filters=None)**
Retrieve notification history.

**Parameters:**
- `limit`: Maximum number of records
- `filters`: Dict with filter criteria

**Returns:** List of notification records

---

## 🧪 **Testing**

### **Unit Tests**

```python
# Test SMS sending
def test_sms_sending():
    notifier = NotificationSystem()
    result = notifier.send_sms("+1234567890", "Test message")
    assert result["success"] == True

# Test template rendering
def test_template_rendering():
    notifier = NotificationSystem()
    rendered = notifier.render_template(
        "task_completion",
        {"user_name": "John", "task_category": "coding"}
    )
    assert "John" in rendered["body"]
```

### **Integration Tests**

```bash
# Test all notification channels
python test_notifications.py --channels all

# Test specific channel
python test_notifications.py --channel email

# Test alert system
python test_notifications.py --alerts
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Email notifications not sending**
1. Check SMTP credentials
2. Verify app password for Gmail
3. Check firewall/port 587 access
4. Review error logs in notification history

#### **Slack notifications failing**
1. Verify webhook URL is correct
2. Check webhook permissions
3. Ensure channel exists
4. Review Slack app configuration

#### **SMS delivery issues**
1. Check Twilio credentials
2. Verify phone number format (+1234567890)
3. Check Twilio account balance
4. Review delivery status in Twilio console

#### **Database connection errors**
1. Check database file permissions
2. Verify SQLite installation
3. Check disk space for database growth
4. Review database initialization logs

### **Debug Mode**

Enable debug logging for notifications:

```python
import logging
logging.getLogger('notification_system').setLevel(logging.DEBUG)
```

### **Health Checks**

```bash
# Check notification system health
curl http://localhost:5001/admin/api/notifications/health

# Test notification delivery
curl -X POST http://localhost:5001/admin/api/notifications/test \
  -H "Content-Type: application/json" \
  -d '{"type": "sms", "recipient": "+1234567890"}'
```

---

## 📈 **Performance Considerations**

### **Optimization Tips**

1. **Batch Processing**: Group notifications for bulk delivery
2. **Template Caching**: Cache rendered templates for performance
3. **Connection Pooling**: Reuse SMTP connections
4. **Queue System**: Use message queues for high-volume scenarios
5. **Database Indexing**: Index notification history for fast queries

### **Monitoring**

Track key metrics:
- Notification delivery rate
- Average delivery time
- Failed notification percentage
- Template rendering performance
- Channel-specific success rates

---

## 🔮 **Future Enhancements**

### **Planned Features**

1. **Push Notifications**: Mobile app push notification support
2. **SMS Templates**: Rich SMS templates with media
3. **A/B Testing**: Template performance testing
4. **Analytics Dashboard**: Comprehensive notification analytics
5. **Machine Learning**: Smart delivery time optimization
6. **Integration APIs**: Third-party notification service integration

### **Scalability Roadmap**

1. **Message Queues**: Redis/RabbitMQ for async processing
2. **Microservices**: Separate notification service
3. **Load Balancing**: Multi-instance notification handling
4. **Monitoring**: Prometheus/Grafana integration
5. **Cloud Services**: AWS SNS/SES integration

---

This documentation provides a complete guide to the Enhanced SMS-to-Cursor AI Agent's notification system. For additional support, check the troubleshooting section or review the source code in `notification_system.py`. 