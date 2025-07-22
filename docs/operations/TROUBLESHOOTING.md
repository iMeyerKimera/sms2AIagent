# 🔍 Troubleshooting Guide

**Complete troubleshooting guide for SMS-to-AI Agent system issues**

---

## 🚨 **Emergency Quick Fixes**

### **Service Down**
```bash
# Restart all services
docker-compose restart

# Check service status
docker-compose ps

# View recent logs
docker-compose logs --tail=50
```

### **Database Issues**
```bash
# Check database health
docker-compose exec database pg_isready -U sms_agent

# Restart database
docker-compose restart database

# Connect to database
docker-compose exec database psql -U sms_agent -d sms_agent_db
```

### **SMS Not Working**
```bash
# Check Twilio configuration
curl -X POST https://api.twilio.com/2010-04-01/Accounts/{SID}/Messages.json \
  -u {SID}:{AUTH_TOKEN} \
  -d "From={TWILIO_NUMBER}" \
  -d "To=+1234567890" \
  -d "Body=Test message"

# Check webhook URL
curl -X POST http://localhost:5001/sms/receive \
  -d "From=+1234567890" \
  -d "Body=Test message"
```

---

## 🐳 **Docker & Container Issues**

### **Containers Won't Start**

#### **Symptom**: `docker-compose up` fails
```bash
# Check Docker daemon
sudo systemctl status docker

# Check container logs
docker-compose logs web
docker-compose logs database
docker-compose logs redis

# Rebuild containers
docker-compose build --no-cache
docker-compose up -d
```

#### **Symptom**: Port conflicts
```bash
# Check what's using the port
sudo netstat -tulpn | grep :5001
sudo lsof -i :5001

# Kill process using port
sudo kill -9 <PID>

# Use different ports in docker-compose.yml
ports:
  - "5002:8000"  # Change external port
```

### **Container Health Issues**

#### **Web Container Unhealthy**
```bash
# Check web container health
docker-compose exec web curl http://localhost:8000/health

# Check Django logs
docker-compose logs web --tail=100

# Restart web container
docker-compose restart web
```

#### **Database Container Issues**
```bash
# Check PostgreSQL logs
docker-compose logs database

# Verify database connectivity
docker-compose exec web python manage.py dbshell

# Reset database (CAUTION: Data loss)
docker-compose down
docker volume rm sms2aiagent_postgres_data
docker-compose up -d
```

---

## 🗄️ **Database Issues**

### **Migration Problems**

#### **Migration Conflicts**
```bash
# List migrations
docker-compose exec web python manage.py showmigrations

# Reset migrations (CAUTION)
docker-compose exec web python manage.py migrate core zero
docker-compose exec web python manage.py migrate

# Fake migrations if needed
docker-compose exec web python manage.py migrate --fake
```

#### **Database Connection Errors**
```bash
# Test database connection
docker-compose exec database pg_isready -U sms_agent -d sms_agent_db

# Check environment variables
docker-compose exec web env | grep DATABASE

# Verify credentials
docker-compose exec database psql -U sms_agent -d sms_agent_db -c "\l"
```

### **Performance Issues**

#### **Slow Queries**
```sql
-- Enable query logging in PostgreSQL
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();

-- Check slow queries
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC LIMIT 10;
```

#### **Database Locks**
```sql
-- Check for locks
SELECT 
    pg_stat_activity.pid,
    pg_stat_activity.query,
    pg_stat_activity.state,
    pg_locks.locktype,
    pg_locks.mode
FROM pg_stat_activity 
JOIN pg_locks ON pg_stat_activity.pid = pg_locks.pid
WHERE pg_stat_activity.query != '<IDLE>';

-- Kill problematic queries
SELECT pg_terminate_backend(<PID>);
```

---

## 📱 **SMS & Twilio Issues**

### **SMS Not Received**

#### **Webhook Configuration**
```bash
# Verify webhook URL is accessible
curl -X POST https://yourdomain.com/sms/receive \
  -d "From=+1234567890" \
  -d "Body=Test message" \
  -d "MessageSid=test123"

# Check Twilio webhook logs
# Go to Twilio Console → Monitor → Logs → Errors
```

#### **Twilio Credentials**
```bash
# Test Twilio credentials
curl -X GET "https://api.twilio.com/2010-04-01/Accounts/{SID}.json" \
  -u {SID}:{AUTH_TOKEN}

# Expected response: Account information JSON
```

#### **Phone Number Issues**
```bash
# Verify phone number format
# Correct: +1234567890
# Incorrect: 1234567890, (123) 456-7890

# Check phone number capabilities
curl -X GET "https://api.twilio.com/2010-04-01/Accounts/{SID}/IncomingPhoneNumbers.json" \
  -u {SID}:{AUTH_TOKEN}
```

### **SMS Not Sent**

#### **Delivery Failures**
```bash
# Check sent message status
curl -X GET "https://api.twilio.com/2010-04-01/Accounts/{SID}/Messages/{MESSAGE_SID}.json" \
  -u {SID}:{AUTH_TOKEN}

# Common status values:
# - queued: Message is queued
# - sending: Message is being sent
# - sent: Message sent successfully
# - failed: Message failed to send
# - delivered: Message delivered
# - undelivered: Message not delivered
```

#### **Rate Limiting**
```bash
# Check Twilio account limits
curl -X GET "https://api.twilio.com/2010-04-01/Accounts/{SID}/Usage/Records.json" \
  -u {SID}:{AUTH_TOKEN}

# Monitor application rate limits
docker-compose exec web python manage.py shell
>>> from core.models import User
>>> user = User.objects.get(phone_number='+1234567890')
>>> print(f"Requests: {user.total_requests}, Monthly: {user.monthly_requests}")
```

---

## 🤖 **AI Processing Issues**

### **OpenAI API Errors**

#### **Authentication Failures**
```bash
# Test OpenAI API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check environment variable
docker-compose exec web env | grep OPENAI_API_KEY
```

#### **Rate Limit Exceeded**
```bash
# Check OpenAI usage
curl https://api.openai.com/v1/usage \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Monitor API errors in logs
docker-compose logs web | grep "AI processing failed"
```

#### **Model Availability**
```bash
# Check available models
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" | jq '.data[].id'

# Test specific model
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'
```

### **Task Processing Failures**

#### **Task Router Issues**
```python
# Debug task routing
docker-compose exec web python manage.py shell

from task_router import TaskRouter
from core.models import User

router = TaskRouter()
user = User.objects.get(phone_number='+1234567890')
result = router.route_task("Debug this Python code", user.tier)
print(result)
```

#### **Cursor Agent Issues**
```python
# Debug Cursor Agent
docker-compose exec web python manage.py shell

from cursor_agent import CursorAgent

agent = CursorAgent()
result = agent.create_task("Create a Python function")
print(result)
```

---

## 🔐 **Authentication & Dashboard Issues**

### **Admin Dashboard Login Issues**

#### **CSRF Token Errors**
```bash
# Check CSRF settings
docker-compose exec web python manage.py shell
>>> from django.conf import settings
>>> print(f"CSRF_COOKIE_SECURE: {settings.CSRF_COOKIE_SECURE}")
>>> print(f"CSRF_TRUSTED_ORIGINS: {settings.CSRF_TRUSTED_ORIGINS}")

# Clear browser cookies and try again
# Ensure webhook URL matches allowed hosts
```

#### **Session Issues**
```bash
# Check Redis connection
docker-compose exec redis redis-cli ping

# Check session configuration
docker-compose exec web python manage.py shell
>>> from django.conf import settings
>>> print(f"SESSION_ENGINE: {settings.SESSION_ENGINE}")
>>> print(f"SESSION_REDIS_URL: {settings.SESSION_REDIS_URL}")

# Clear all sessions
docker-compose exec redis redis-cli FLUSHDB
```

#### **Permission Errors**
```bash
# Check admin credentials
docker-compose exec web python manage.py shell
>>> from django.conf import settings
>>> print(f"ADMIN_USERNAME: {settings.ADMIN_USERNAME}")
>>> print(f"ADMIN_PASSWORD: {settings.ADMIN_PASSWORD}")

# Reset admin password
docker-compose exec web python manage.py changepassword admin
```

### **Django Admin Issues**

#### **Superuser Access**
```bash
# Create superuser
docker-compose exec web python manage.py createsuperuser

# Reset superuser password
docker-compose exec web python manage.py changepassword <username>

# Check user permissions
docker-compose exec web python manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='admin')
>>> print(f"Is superuser: {user.is_superuser}")
>>> print(f"Is staff: {user.is_staff}")
```

---

## 📊 **Performance Issues**

### **Slow Response Times**

#### **Database Performance**
```sql
-- Check database performance
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public';

-- Analyze tables
ANALYZE;

-- Check for missing indexes
SELECT 
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch
FROM pg_stat_user_tables
ORDER BY seq_tup_read DESC;
```

#### **Redis Performance**
```bash
# Check Redis info
docker-compose exec redis redis-cli info memory

# Monitor Redis operations
docker-compose exec redis redis-cli monitor

# Check slow log
docker-compose exec redis redis-cli slowlog get 10
```

#### **Application Performance**
```bash
# Enable Django debug toolbar (development only)
pip install django-debug-toolbar

# Monitor memory usage
docker stats

# Check application logs for slow operations
docker-compose logs web | grep "processing time"
```

### **High Memory Usage**

#### **Container Memory**
```bash
# Check container memory usage
docker stats --no-stream

# Limit container memory
# Add to docker-compose.yml:
services:
  web:
    deploy:
      resources:
        limits:
          memory: 512M
```

#### **Database Memory**
```sql
-- Check PostgreSQL memory usage
SELECT 
    setting,
    unit,
    context
FROM pg_settings 
WHERE name IN ('shared_buffers', 'effective_cache_size', 'work_mem');

-- Optimize memory settings in postgresql.conf
shared_buffers = 128MB
effective_cache_size = 512MB
work_mem = 4MB
```

---

## 🌐 **Network & Connectivity Issues**

### **External Service Connectivity**

#### **Internet Access Issues**
```bash
# Test external connectivity from container
docker-compose exec web curl -I https://api.openai.com
docker-compose exec web curl -I https://api.twilio.com
docker-compose exec web nslookup api.openai.com

# Check DNS resolution
docker-compose exec web cat /etc/resolv.conf
```

#### **Firewall Issues**
```bash
# Check firewall status
sudo ufw status

# Allow required ports
sudo ufw allow 5001/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check iptables
sudo iptables -L -n
```

### **SSL/TLS Issues**

#### **Certificate Problems**
```bash
# Test SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Check certificate expiration
echo | openssl s_client -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates

# Renew Let's Encrypt certificate
sudo certbot renew
```

#### **Webhook SSL Issues**
```bash
# Test webhook with SSL
curl -X POST https://yourdomain.com/sms/receive \
  -d "From=+1234567890" \
  -d "Body=Test" \
  -v

# Check SSL configuration
curl -I https://yourdomain.com
```

---

## 📝 **Logging & Debugging**

### **Enable Debug Logging**
```python
# In settings.py (development only)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

### **Useful Log Commands**
```bash
# Real-time logs
docker-compose logs -f web

# Search logs
docker-compose logs web | grep ERROR
docker-compose logs web | grep "AI processing"

# Export logs
docker-compose logs web > web_logs.txt

# Log rotation
sudo logrotate /etc/logrotate.d/docker-logs
```

---

## 🔧 **Recovery Procedures**

### **Complete System Reset**
```bash
# CAUTION: This will delete all data
docker-compose down -v
docker system prune -a
docker volume prune
docker-compose up -d
```

### **Database Recovery**
```bash
# Restore from backup
docker-compose down
docker volume rm sms2aiagent_postgres_data
docker-compose up -d database
gunzip -c backup.sql.gz | docker-compose exec -T database psql -U sms_agent -d sms_agent_db
docker-compose up -d
```

### **Configuration Reset**
```bash
# Reset to default configuration
cp env.example .env
# Edit .env with your values
docker-compose restart
```

---

## 📞 **Getting Help**

### **Log Collection for Support**
```bash
# Collect all relevant logs
mkdir support_logs
docker-compose logs web > support_logs/web.log
docker-compose logs database > support_logs/database.log
docker-compose logs redis > support_logs/redis.log
docker-compose ps > support_logs/services.txt
docker version > support_logs/docker_version.txt
```

### **System Information**
```bash
# Collect system info
uname -a > system_info.txt
docker --version >> system_info.txt
docker-compose --version >> system_info.txt
free -h >> system_info.txt
df -h >> system_info.txt
```

---

**🎉 Most issues can be resolved with the steps above. For persistent problems, check the system logs and ensure all prerequisites are met.**

**See also: [Production Guide](PRODUCTION.md) and [Monitoring Guide](MONITORING.md)** 