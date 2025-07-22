# 🛠️ Django SMS AI Agent - Troubleshooting Guide

## 🔍 Common Issues & Solutions

### 1. 🚨 **CSRF Token Missing Error**

#### **Problem**
```
WARNING Forbidden (CSRF token missing.): /dashboard/login/
```

#### **Cause**
Django requires CSRF tokens for all POST requests to prevent Cross-Site Request Forgery attacks.

#### **Solution**
✅ **FIXED** - The login template now includes `{% csrf_token %}` in the form.

```html
<form method="POST">
    {% csrf_token %}
    <!-- form fields -->
</form>
```

#### **Verification**
```bash
# Check if CSRF token is in the form
curl -c cookies.txt http://localhost:5001/dashboard/
grep csrftoken cookies.txt
```

---

### 2. 🔐 **Admin Dashboard Login Issues**

#### **Problem**
- Can't access dashboard
- Login form not working
- Redirected to wrong page

#### **Admin Dashboard Access**

**Correct URLs:**
- **Custom Dashboard Login**: `http://localhost:5001/dashboard/`
- **Custom Dashboard**: `http://localhost:5001/dashboard/dashboard/`
- **Django Admin**: `http://localhost:5001/admin/` (different system)

#### **Default Credentials**
```bash
# Check your .env file for:
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_admin_password
```

#### **Login Process**
1. Go to `http://localhost:5001/dashboard/`
2. Enter credentials from `.env` file
3. Should redirect to `http://localhost:5001/dashboard/dashboard/`

#### **Troubleshooting Steps**
```bash
# 1. Check if service is running
docker-compose ps

# 2. Check logs for authentication errors
docker-compose logs web | grep -i login

# 3. Test login endpoint directly
curl -X POST http://localhost:5001/dashboard/login/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=your_password"

# 4. Check session storage (Redis)
docker-compose logs redis
```

---

### 3. 📊 **Database Connection Issues**

#### **Problem**
```
django.db.utils.OperationalError: could not translate host name "database" to address
```

#### **Solution**
```bash
# 1. Check if database service is running
docker-compose ps database

# 2. Check database logs
docker-compose logs database

# 3. Restart database service
docker-compose restart database

# 4. Wait for database to be ready
docker-compose exec database pg_isready -U sms_agent -d sms_agent_db
```

#### **Database Health Check**
```bash
# Check database connectivity
curl http://localhost:5001/health

# Manual database connection test
docker-compose exec database psql -U sms_agent -d sms_agent_db -c "SELECT 1;"
```

---

### 4. 🔄 **Migration Issues**

#### **Problem**
```
django.db.migrations.exceptions.InconsistentMigrationHistory
```

#### **Solution**
```bash
# 1. Check migration status
docker-compose exec web python manage.py showmigrations

# 2. Apply migrations
docker-compose exec web python manage.py migrate

# 3. If migrations are corrupted, reset (WARNING: destroys data)
docker-compose down -v
docker-compose up -d
```

---

### 5. 🌐 **Static Files Not Loading**

#### **Problem**
- CSS/JS files return 404
- Admin interface looks broken

#### **Solution**
```bash
# 1. Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# 2. Check static files directory
docker-compose exec web ls -la /app/staticfiles/

# 3. Restart web service
docker-compose restart web
```

---

### 6. 📱 **SMS Webhook Issues**

#### **Problem**
- SMS not being processed
- Twilio webhook failing

#### **Troubleshooting Steps**
```bash
# 1. Check ngrok URL
curl http://localhost:4040/api/tunnels

# 2. Test webhook endpoint
curl -X POST http://localhost:5001/sms/receive \
  -d "From=+1234567890&Body=test message"

# 3. Check webhook logs
docker-compose logs web | grep -i sms

# 4. Verify Twilio webhook configuration
# Should be: https://your-domain.ngrok-free.app/sms/receive
```

#### **Webhook URL Update**
**Old Flask URL**: `/sms`  
**New Django URL**: `/sms/receive`

---

### 7. 🔧 **Environment Configuration Issues**

#### **Problem**
- Services not starting
- Missing environment variables

#### **Solution**
```bash
# 1. Copy environment template
cp env.example .env

# 2. Edit with your values
nano .env

# 3. Required variables:
DJANGO_SECRET_KEY=your-secret-key
DATABASE_PASSWORD=secure_password_123
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_admin_password
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
OPENAI_API_KEY=your_openai_key
```

---

### 8. 🐳 **Docker Issues**

#### **Problem**
- Containers not starting
- Build failures
- Port conflicts

#### **Solution**
```bash
# 1. Clean restart
docker-compose down
docker-compose up -d --build

# 2. Check logs
docker-compose logs

# 3. Check port conflicts
netstat -tulpn | grep :5001
netstat -tulpn | grep :5432

# 4. Clean Docker system
docker system prune -f
docker-compose down -v
docker-compose up -d
```

---

## 🔍 **Debug Commands**

### **Application Debugging**
```bash
# Check Django system
docker-compose exec web python manage.py check

# Django shell for debugging
docker-compose exec web python manage.py shell

# Check all services
docker-compose ps

# View real-time logs
docker-compose logs -f web
```

### **Database Debugging**
```bash
# Database status
docker-compose exec database pg_isready -U sms_agent

# Database shell
docker-compose exec database psql -U sms_agent -d sms_agent_db

# Check database size
docker-compose exec database psql -U sms_agent -d sms_agent_db -c "
SELECT pg_size_pretty(pg_database_size('sms_agent_db'));"

# Check active connections
docker-compose exec database psql -U sms_agent -d sms_agent_db -c "
SELECT count(*) FROM pg_stat_activity;"
```

### **Network Debugging**
```bash
# Test internal connectivity
docker-compose exec web ping database
docker-compose exec web ping redis

# Check port mappings
docker-compose port web 8000
docker-compose port database 5432
```

---

## 📊 **Monitoring & Logs**

### **Log Locations**
```bash
# Application logs
tail -f logs/django.log

# Container logs
docker-compose logs web
docker-compose logs database
docker-compose logs redis
docker-compose logs ngrok

# Django debug logs
docker-compose exec web python manage.py shell -c "
import logging
logging.getLogger('django').setLevel(logging.DEBUG)
"
```

### **Health Monitoring**
```bash
# Application health
curl http://localhost:5001/health

# Dashboard health
curl http://localhost:5001/dashboard/api/overview

# Database health
curl http://localhost:5001/dashboard/api/system/performance
```

---

## 🚨 **Emergency Recovery**

### **Complete Reset (WARNING: Destroys Data)**
```bash
# Stop all services
docker-compose down -v

# Remove all containers and volumes
docker-compose rm -f
docker volume prune -f

# Rebuild and start
./deploy.sh --rebuild
```

### **Backup Before Reset**
```bash
# Backup database
docker-compose exec database pg_dump -U sms_agent -d sms_agent_db > backup.sql

# Backup environment
cp .env .env.backup

# Backup logs
tar -czf logs_backup.tar.gz logs/
```

---

## 📞 **Getting Help**

### **Debug Information to Collect**
```bash
# System information
docker-compose ps
docker-compose logs --tail=50

# Environment check
echo "Django settings module: $DJANGO_SETTINGS_MODULE"
echo "Debug mode: $DEBUG"

# Network status
curl -I http://localhost:5001/health
curl -I http://localhost:5001/dashboard/
```

### **Common URLs for Testing**
- **Health Check**: `http://localhost:5001/health`
- **Dashboard Login**: `http://localhost:5001/dashboard/`
- **Django Admin**: `http://localhost:5001/admin/`
- **API Root**: `http://localhost:5001/api/`
- **SMS Test**: `http://localhost:5001/sms/receive` (POST)

---

## ✅ **Success Indicators**

When everything is working correctly:

```bash
# Health check returns 200
curl http://localhost:5001/health
# {"status": "healthy", ...}

# Dashboard login page loads
curl -I http://localhost:5001/dashboard/
# HTTP/1.1 200 OK

# Database is connected
docker-compose exec database pg_isready -U sms_agent
# accepting connections

# All services running
docker-compose ps
# All services should show "Up"
```

Your Django SMS AI Agent should now be fully operational! 🎉 