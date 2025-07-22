# 🚀 Django SMS AI Agent - Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the Django-based SMS AI Agent with PostgreSQL and Redis.

## 📋 Prerequisites

### Required Accounts & Keys
- **Twilio Account**: For SMS functionality
- **OpenAI API Key**: For AI processing
- **ngrok Account**: For webhook tunneling (optional but recommended)

### System Requirements
- **Docker & Docker Compose**: Latest versions
- **Git**: For repository cloning
- **curl**: For health checks and testing

## 🔧 Quick Deployment

### 1. Clone and Setup
```bash
# Clone the repository
git clone <repository-url>
cd sms2AIagent

# Copy environment configuration
cp env.example .env
```

### 2. Configure Environment
Edit `.env` file with your credentials:

```bash
# Django Configuration
DJANGO_SECRET_KEY=your-super-secure-256-bit-secret-key
DEBUG=false

# Database
DATABASE_NAME=sms_agent_db
DATABASE_USER=sms_agent
DATABASE_PASSWORD=secure_password_123
DATABASE_HOST=database
DATABASE_PORT=5432

# API Keys
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
OPENAI_API_KEY=your_openai_api_key

# Admin Access
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_admin_password

# ngrok (optional)
NGROK_AUTHTOKEN=your_ngrok_token
NGROK_DOMAIN=your-domain.ngrok-free.app
```

### 3. Deploy Services
```bash
# Standard deployment
./deploy.sh

# Or with rebuild
./deploy.sh --rebuild

# Or with backup and rebuild
./deploy.sh --backup --rebuild
```

### 4. Verify Deployment
```bash
# Check service status
docker-compose ps

# Test health endpoint
curl http://localhost:5001/health

# View logs
docker-compose logs web
```

## 🌐 Service Endpoints

### Main Application
- **Web App**: http://localhost:5001
- **Django Admin**: http://localhost:5001/admin/
- **Custom Dashboard**: http://localhost:5001/dashboard/
- **API Root**: http://localhost:5001/api/
- **Health Check**: http://localhost:5001/health

### Development Tools
- **ngrok Dashboard**: http://localhost:4040 (if enabled)

### API Endpoints
```bash
# SMS Processing
POST /sms/receive          # Twilio webhook
POST /sms/send            # Send SMS

# User Management
POST /users/register      # Register user
GET  /users/{phone}/profile    # User profile
GET  /users/{phone}/tasks      # User tasks

# Analytics
GET /analytics/overview   # System overview
GET /analytics/user-stats # User statistics
GET /analytics/task-stats # Task statistics

# REST API (Django REST Framework)
GET    /api/users/        # List users
POST   /api/users/        # Create user
GET    /api/tasks/        # List tasks
POST   /api/tasks/        # Create task
GET    /api/errors/       # List errors
```

## 🔄 Database Management

### Initial Setup
Django automatically handles database setup through migrations:
```bash
# Migrations run automatically in Docker
# Manual migration (if needed):
docker-compose exec web python manage.py migrate
```

### Database Operations
```bash
# Connect to PostgreSQL
docker-compose exec database psql -U sms_agent -d sms_agent_db

# Create backup
docker-compose exec database pg_dump -U sms_agent -d sms_agent_db > backup.sql

# View database logs
docker-compose logs database

# Check database status
docker-compose exec database pg_isready -U sms_agent -d sms_agent_db
```

### Django Admin Setup
```bash
# Create Django superuser (optional)
docker-compose exec web python manage.py createsuperuser

# Collect static files (runs automatically)
docker-compose exec web python manage.py collectstatic --noinput
```

## 📱 Twilio Configuration

### 1. Get Public URL
If using ngrok:
```bash
# Check ngrok URL
curl http://localhost:4040/api/tunnels
```

### 2. Configure Webhook
In Twilio Console:
1. Go to Phone Numbers → Manage → Active numbers
2. Click your SMS-enabled number
3. Set webhook URL: `https://your-domain.ngrok-free.app/sms/receive`
4. HTTP method: POST
5. Save configuration

### 3. Test SMS Integration
```bash
# Send test SMS to your Twilio number
# Check logs for processing
docker-compose logs web -f
```

## 🔍 Health Monitoring

### Health Check Endpoints
```bash
# Application health
curl http://localhost:5001/health

# Database health
curl http://localhost:5001/dashboard/api/overview
```

### Container Health
```bash
# Check all services
docker-compose ps

# View specific service logs
docker-compose logs web
docker-compose logs database
docker-compose logs redis
```

### Performance Monitoring
```bash
# Resource usage
docker stats

# Database performance
docker-compose exec database psql -U sms_agent -d sms_agent_db -c "
SELECT * FROM pg_stat_activity WHERE state = 'active';
"
```

## 🛠️ Troubleshooting

### **Dashboard Login Issues**

#### **CSRF Token Missing Error**
```
WARNING Forbidden (CSRF token missing.): /dashboard/login/
```

**Solution**: ✅ **FIXED** - Login template now includes CSRF token.

**Access Dashboard**:
1. Go to: `http://localhost:5001/dashboard/`
2. Use credentials from `.env` file (`ADMIN_USERNAME`, `ADMIN_PASSWORD`)
3. Form now includes proper CSRF protection

#### **Wrong Login URL**
- ❌ Wrong: `http://localhost:5001/admin/login/` (Django admin)
- ✅ Correct: `http://localhost:5001/dashboard/` (Custom dashboard)

### Common Issues

#### 1. Service Won't Start
```bash
# Check container status
docker-compose ps

# View error logs
docker-compose logs web
docker-compose logs database

# Restart services
docker-compose restart
```

#### 2. Database Connection Failed
```bash
# Check database status
docker-compose exec database pg_isready -U sms_agent

# View database logs
docker-compose logs database

# Reset database (WARNING: destroys data)
docker-compose down -v
docker-compose up -d
```

#### 3. Migration Issues
```bash
# Check migration status
docker-compose exec web python manage.py showmigrations

# Apply migrations manually
docker-compose exec web python manage.py migrate

# Reset migrations (WARNING: destroys data)
docker-compose exec web python manage.py migrate --run-syncdb
```

#### 4. Static Files Not Loading
```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput --clear

# Check static files directory
docker-compose exec web ls -la /app/staticfiles/
```

#### 5. ngrok Issues
```bash
# Check ngrok status
curl http://localhost:4040/api/tunnels

# Restart ngrok
docker-compose restart ngrok

# View ngrok logs
docker-compose logs ngrok
```

## 🔐 Security Configuration

### Production Settings
```bash
# Security-focused environment variables
DEBUG=false
ALLOWED_HOSTS=your-domain.com,your-ip-address
SECRET_KEY=very-long-random-string
SECURE_COOKIES=true
FORCE_HTTPS=true
```

### Database Security
```bash
# Change default database password
DATABASE_PASSWORD=very-secure-random-password

# Restrict database access
DATABASE_HOST=database  # Keep internal
```

### API Security
```bash
# Rate limiting (configured per tier)
RATE_LIMIT_FREE=10        # per month
RATE_LIMIT_PREMIUM=100    # per month
RATE_LIMIT_ENTERPRISE=1000 # per month
```

## 📊 Monitoring & Analytics

### Built-in Monitoring
- **Django Admin**: http://localhost:5001/admin/
- **Custom Dashboard**: http://localhost:5001/dashboard/
- **Health Endpoint**: http://localhost:5001/health

### Log Files
```bash
# Application logs
tail -f logs/django.log

# Container logs
docker-compose logs -f web
```

### Database Monitoring
```bash
# Database size
docker-compose exec database psql -U sms_agent -d sms_agent_db -c "
SELECT pg_size_pretty(pg_database_size('sms_agent_db'));
"

# Active connections
docker-compose exec database psql -U sms_agent -d sms_agent_db -c "
SELECT count(*) FROM pg_stat_activity;
"
```

## 🚀 Scaling Considerations

### Horizontal Scaling
- **Web Tier**: Multiple Django instances behind load balancer
- **Database**: PostgreSQL read replicas
- **Cache**: Redis clustering
- **Queue**: Add Celery for background tasks

### Performance Optimization
- **Database**: Connection pooling, query optimization
- **Cache**: Redis for session/query caching
- **Static Files**: CDN for static assets
- **Monitoring**: Add APM tools

## 📝 Maintenance

### Regular Tasks
```bash
# Database backup (weekly)
docker-compose exec database pg_dump -U sms_agent -d sms_agent_db | gzip > backup_$(date +%Y%m%d).sql.gz

# Update containers (monthly)
docker-compose pull
docker-compose up -d

# Clean old images
docker image prune -f
```

### Updates
```bash
# Update application code
git pull
docker-compose build
docker-compose up -d

# Update dependencies
# Edit requirements.txt and rebuild:
docker-compose build --no-cache
```

---

## 📞 Support

### Common Commands Reference
```bash
# Deployment
./deploy.sh --rebuild

# Logs
docker-compose logs -f web

# Database access
docker-compose exec database psql -U sms_agent -d sms_agent_db

# Django shell
docker-compose exec web python manage.py shell

# Create admin user
docker-compose exec web python manage.py createsuperuser
```

### Useful URLs
- **Application**: http://localhost:5001
- **Django Admin**: http://localhost:5001/admin/
- **Custom Dashboard**: http://localhost:5001/dashboard/
- **API Documentation**: http://localhost:5001/api/
- **Health Check**: http://localhost:5001/health

Your Django SMS AI Agent is now ready for production! 🎉 