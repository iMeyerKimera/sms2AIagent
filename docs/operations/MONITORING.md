# 📊 Monitoring & Logging Guide

**Comprehensive monitoring and logging setup for SMS-to-AI Agent**

---

## 📋 **Overview**

This guide covers setting up monitoring, logging, alerting, and performance tracking for your SMS-to-AI Agent deployment. Proper monitoring ensures system reliability, helps with troubleshooting, and provides insights for optimization.

---

## 🔍 **Health Monitoring**

### **Built-in Health Checks**

```bash
# Application health endpoint
curl http://localhost:5001/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2024-01-20T16:30:00Z",
  "services": {
    "database": {"status": "healthy", "response_time": 0.023},
    "redis": {"status": "healthy", "response_time": 0.001},
    "openai": {"status": "healthy", "rate_limit_remaining": 4500},
    "twilio": {"status": "healthy", "account_balance": "$45.67"}
  },
  "version": "1.0.0",
  "uptime": 86400
}
```

### **System Resource Monitoring**

```bash
# Monitor Docker containers
docker stats --no-stream

# Check service status
docker-compose ps

# Monitor logs in real-time
docker-compose logs -f web
```

---

## 📝 **Logging Configuration**

### **Application Logging**

```python
# Django logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/errors.log',
            'maxBytes': 1024*1024*15,
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'sms_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/sms.log',
            'maxBytes': 1024*1024*10,
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
        },
        'sms_agent': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
        },
        'sms_agent.sms': {
            'handlers': ['sms_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### **Log Analysis Commands**

```bash
# View recent errors
tail -f logs/errors.log

# Search for specific patterns
grep "ERROR" logs/app.log | tail -20
grep "SMS" logs/sms.log | jq '.'

# Monitor SMS processing
tail -f logs/sms.log | jq '.message'

# Count error types
grep "ERROR" logs/errors.log | awk '{print $3}' | sort | uniq -c

# Performance analysis
grep "processing_time" logs/app.log | awk '{print $NF}' | sort -n
```

---

## 📈 **Performance Metrics**

### **Key Metrics to Monitor**

#### **Application Metrics**
- Request/response times
- SMS processing success rate
- AI API response times
- User activity patterns
- Error rates and types

#### **System Metrics**
- CPU and memory usage
- Database connection pool usage
- Redis memory usage
- Disk space utilization
- Network I/O

#### **Business Metrics**
- Daily active users
- Tasks processed per hour
- User tier distribution
- Popular task categories
- Revenue metrics (if applicable)

### **Metrics Collection Script**

```python
# monitoring/collect_metrics.py
import psutil
import redis
import psycopg2
from django.db.models import Count, Avg
from core.models import User, Task, ErrorLog

class MetricsCollector:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
    
    def collect_system_metrics(self):
        """Collect system resource metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
        }
    
    def collect_application_metrics(self):
        """Collect application-specific metrics"""
        from datetime import timedelta
        from django.utils import timezone
        
        now = timezone.now()
        last_hour = now - timedelta(hours=1)
        
        return {
            'active_users_last_hour': User.objects.filter(last_active__gte=last_hour).count(),
            'tasks_last_hour': Task.objects.filter(created_at__gte=last_hour).count(),
            'successful_tasks_last_hour': Task.objects.filter(
                created_at__gte=last_hour, success=True
            ).count(),
            'errors_last_hour': ErrorLog.objects.filter(timestamp__gte=last_hour).count(),
            'avg_processing_time': Task.objects.filter(
                created_at__gte=last_hour, success=True
            ).aggregate(avg=Avg('processing_time'))['avg'] or 0
        }
    
    def store_metrics(self, metrics):
        """Store metrics in Redis with timestamp"""
        timestamp = int(timezone.now().timestamp())
        for key, value in metrics.items():
            self.redis_client.zadd(f"metrics:{key}", {timestamp: value})
            # Keep only last 24 hours of data
            cutoff = timestamp - (24 * 3600)
            self.redis_client.zremrangebyscore(f"metrics:{key}", 0, cutoff)
```

---

## 🚨 **Alerting System**

### **Alert Configuration**

```python
# monitoring/alerts.py
import smtplib
import requests
from email.mime.text import MIMEText
from django.conf import settings

class AlertManager:
    def __init__(self):
        self.alert_thresholds = {
            'cpu_usage': 80,
            'memory_usage': 85,
            'error_rate': 5,  # percentage
            'response_time': 5.0,  # seconds
            'failed_tasks': 10  # per hour
        }
    
    def check_thresholds(self, metrics):
        """Check if any metrics exceed thresholds"""
        alerts = []
        
        for metric, threshold in self.alert_thresholds.items():
            if metric in metrics and metrics[metric] > threshold:
                alerts.append({
                    'metric': metric,
                    'value': metrics[metric],
                    'threshold': threshold,
                    'severity': self._get_severity(metric, metrics[metric])
                })
        
        return alerts
    
    def send_alert(self, alerts):
        """Send alerts via email and Slack"""
        if not alerts:
            return
        
        message = self._format_alert_message(alerts)
        
        # Send email alert
        self._send_email_alert(message)
        
        # Send Slack notification
        self._send_slack_alert(message)
    
    def _send_email_alert(self, message):
        """Send email alert"""
        if not hasattr(settings, 'ALERT_EMAIL'):
            return
        
        msg = MIMEText(message)
        msg['Subject'] = 'SMS-to-AI Agent Alert'
        msg['From'] = settings.EMAIL_HOST_USER
        msg['To'] = settings.ALERT_EMAIL
        
        try:
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                server.starttls()
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                server.send_message(msg)
        except Exception as e:
            print(f"Failed to send email alert: {e}")
    
    def _send_slack_alert(self, message):
        """Send Slack alert"""
        if not hasattr(settings, 'SLACK_WEBHOOK_URL'):
            return
        
        payload = {
            'text': f"🚨 SMS-to-AI Agent Alert\n\n{message}",
            'username': 'SMS-AI Monitor',
            'icon_emoji': ':warning:'
        }
        
        try:
            requests.post(settings.SLACK_WEBHOOK_URL, json=payload)
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")
```

---

## 📊 **Dashboard Monitoring**

### **Real-time Dashboard Metrics**

```javascript
// static/js/monitoring.js
class MonitoringDashboard {
    constructor() {
        this.charts = {};
        this.updateInterval = 30000; // 30 seconds
        this.initialize();
    }
    
    initialize() {
        this.createCharts();
        this.startUpdating();
    }
    
    async fetchMetrics() {
        try {
            const response = await fetch('/dashboard/api/metrics/');
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch metrics:', error);
            return null;
        }
    }
    
    createCharts() {
        // System resource chart
        this.charts.system = new Chart(document.getElementById('systemChart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU Usage (%)',
                    data: [],
                    borderColor: 'rgb(255, 99, 132)',
                    tension: 0.1
                }, {
                    label: 'Memory Usage (%)',
                    data: [],
                    borderColor: 'rgb(54, 162, 235)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
        
        // Task processing chart
        this.charts.tasks = new Chart(document.getElementById('tasksChart'), {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Tasks Processed',
                    data: [],
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    updateCharts(metrics) {
        const now = new Date().toLocaleTimeString();
        
        // Update system chart
        this.addDataPoint(this.charts.system, now, [
            metrics.cpu_percent,
            metrics.memory_percent
        ]);
        
        // Update tasks chart
        this.addDataPoint(this.charts.tasks, now, [
            metrics.tasks_last_hour
        ]);
        
        // Update metric cards
        document.getElementById('activeUsers').textContent = metrics.active_users_last_hour;
        document.getElementById('tasksProcessed').textContent = metrics.tasks_last_hour;
        document.getElementById('successRate').textContent = 
            `${((metrics.successful_tasks_last_hour / metrics.tasks_last_hour) * 100 || 0).toFixed(1)}%`;
        document.getElementById('avgResponseTime').textContent = 
            `${metrics.avg_processing_time.toFixed(2)}s`;
    }
    
    addDataPoint(chart, label, data) {
        chart.data.labels.push(label);
        chart.data.datasets.forEach((dataset, index) => {
            dataset.data.push(data[index]);
        });
        
        // Keep only last 20 data points
        if (chart.data.labels.length > 20) {
            chart.data.labels.shift();
            chart.data.datasets.forEach(dataset => {
                dataset.data.shift();
            });
        }
        
        chart.update();
    }
    
    startUpdating() {
        setInterval(async () => {
            const metrics = await this.fetchMetrics();
            if (metrics) {
                this.updateCharts(metrics);
            }
        }, this.updateInterval);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MonitoringDashboard();
});
```

---

## 🔧 **Monitoring Tools Setup**

### **Prometheus Configuration**

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'sms-agent'
    static_configs:
      - targets: ['localhost:5001']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### **Grafana Dashboard**

```json
{
  "dashboard": {
    "title": "SMS-to-AI Agent Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(sms_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Success Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rate(sms_requests_successful[5m]) / rate(sms_requests_total[5m]) * 100",
            "legendFormat": "Success %"
          }
        ]
      }
    ]
  }
}
```

---

## 📱 **Production Monitoring Checklist**

### **Pre-Deployment**
- [ ] Configure log rotation
- [ ] Set up health check endpoints
- [ ] Configure alerting thresholds
- [ ] Test notification channels
- [ ] Set up monitoring dashboard

### **Post-Deployment**
- [ ] Verify all services are healthy
- [ ] Monitor initial load patterns
- [ ] Validate alert thresholds
- [ ] Check log collection
- [ ] Test backup procedures

### **Ongoing Monitoring**
- [ ] Daily health check review
- [ ] Weekly performance analysis
- [ ] Monthly capacity planning
- [ ] Quarterly security audit
- [ ] Regular backup verification

---

## 🔗 **Related Documentation**

- **[Production Guide](PRODUCTION.md)** - Production deployment
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Issue resolution
- **[Configuration Guide](../getting-started/CONFIGURATION.md)** - System configuration

---

**📊 Your monitoring system is now configured for comprehensive observability and proactive issue detection!** 