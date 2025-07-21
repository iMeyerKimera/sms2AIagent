# 📦 Complete Installation Guide

**Comprehensive setup instructions for SMS-to-AI Agent in all environments**

---

## 📋 **Prerequisites**

### **System Requirements**
- **Operating System**: macOS, Linux, or Windows with WSL2
- **Docker**: Version 20.10+ 
- **Docker Compose**: Version 2.0+
- **Memory**: Minimum 4GB RAM recommended
- **Storage**: 10GB+ free space

### **External Services**
- **Twilio Account**: For SMS processing ([Sign up](https://www.twilio.com/try-twilio))
- **OpenAI API Key**: For AI processing ([Get API key](https://openai.com/api/))
- **Domain/ngrok**: For webhook access (production or [ngrok](https://ngrok.com/))

---

## 🛠️ **Installation Methods**

### **Method 1: Quick Docker Setup (Recommended)**

#### **Step 1: Install Docker**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose-plugin

# macOS (using Homebrew)
brew install docker docker-compose

# Windows - Download Docker Desktop from docker.com
```

#### **Step 2: Clone and Configure**
```bash
# Clone repository
git clone <your-repository-url>
cd sms2AIagent

# Copy environment template
cp env.example .env

# Edit configuration
nano .env  # or use your preferred editor
```

#### **Step 3: Configure Environment Variables**
Edit `.env` file with your credentials:
```bash
# Required - Twilio Configuration
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890

# Required - Database
DATABASE_URL=postgresql://sms_agent:your_password@database:5432/sms_agent_db
DB_PASSWORD=choose_secure_password

# Optional but Recommended - AI
OPENAI_API_KEY=your_openai_api_key_here

# Admin Access
ADMIN_USERNAME=admin
ADMIN_PASSWORD=choose_secure_admin_password

# Development Settings
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
```

#### **Step 4: Deploy**
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

#### **Step 5: Initialize Database**
```bash
# Run database migrations
docker-compose exec web python manage.py migrate

# Create admin user
docker-compose exec web python manage.py createsuperuser

# Load initial data (optional)
docker-compose exec web python manage.py loaddata initial_data.json
```

#### **Step 6: Verify Installation**
```bash
# Health check
curl http://localhost:5001/health

# Expected response: {"status": "healthy", "database": "connected", "redis": "connected"}
```

---

### **Method 2: Development Setup**

#### **Step 1: Python Environment**
```bash
# Create virtual environment
python3 -m venv sms_agent_env
source sms_agent_env/bin/activate  # Linux/macOS
# or
sms_agent_env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

#### **Step 2: Database Setup**
```bash
# Install PostgreSQL
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql

# Start PostgreSQL service
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS

# Create database and user
sudo -u postgres psql
CREATE DATABASE sms_agent_db;
CREATE USER sms_agent WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE sms_agent_db TO sms_agent;
\q
```

#### **Step 3: Redis Setup**
```bash
# Install Redis
# Ubuntu/Debian
sudo apt install redis-server

# macOS
brew install redis

# Start Redis
sudo systemctl start redis        # Linux
brew services start redis         # macOS
```

#### **Step 4: Application Configuration**
```bash
# Copy environment file
cp env.example .env.dev

# Edit for development
DATABASE_URL=postgresql://sms_agent:your_password@localhost:5432/sms_agent_db
REDIS_URL=redis://localhost:6379/0
DEBUG=True
```

#### **Step 5: Run Application**
```bash
# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver 0.0.0.0:5001
```

---

## 🌐 **External Service Configuration**

### **Twilio Setup**

#### **1. Get Twilio Credentials**
1. Sign up at [twilio.com](https://www.twilio.com/try-twilio)
2. Get a phone number with SMS capabilities
3. Find your Account SID and Auth Token in console

#### **2. Configure Webhook**
1. Go to Phone Numbers → Manage → Active Numbers
2. Click your SMS-enabled number
3. Set webhook URL:
   - **Development**: `https://your-ngrok-url.ngrok-free.app/sms/receive`
   - **Production**: `https://yourdomain.com/sms/receive`
4. Set HTTP method to POST
5. Save configuration

### **OpenAI Setup**

#### **1. Get API Key**
1. Sign up at [openai.com](https://openai.com/api/)
2. Go to API Keys section
3. Create new API key
4. Add to your `.env` file

#### **2. Set Usage Limits**
1. Go to Billing → Usage limits
2. Set monthly spending limit
3. Monitor usage in dashboard

### **ngrok Setup (Development)**

#### **1. Install ngrok**
```bash
# Download from ngrok.com or use package manager
# macOS
brew install ngrok

# Ubuntu/Debian
sudo snap install ngrok
```

#### **2. Configure ngrok**
```bash
# Sign up and get auth token from ngrok.com
ngrok config add-authtoken YOUR_AUTHTOKEN

# Start tunnel
ngrok http 5001

# Note the HTTPS URL (e.g., https://abcd1234.ngrok-free.app)
```

---

## 🔧 **Advanced Configuration**

### **Environment Variables Reference**

#### **Django Settings**
```bash
# Core Django configuration
DJANGO_SETTINGS_MODULE=sms_agent.settings
DJANGO_SECRET_KEY=your-super-secure-secret-key-here
DEBUG=False                                    # True for development
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,localhost

# Security settings (production)
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

#### **Database Configuration**
```bash
# PostgreSQL connection
DATABASE_URL=postgresql://user:password@host:port/database
DB_NAME=sms_agent_db
DB_USER=sms_agent
DB_PASSWORD=secure_password_here
DB_HOST=database                               # or localhost for development
DB_PORT=5432

# Connection pooling
DB_CONN_MAX_AGE=600
DB_CONN_HEALTH_CHECKS=True
```

#### **Redis Configuration**
```bash
# Redis connection
REDIS_URL=redis://redis:6379/0                # or redis://localhost:6379/0
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Session configuration
SESSION_ENGINE=django.contrib.sessions.backends.cache
SESSION_CACHE_ALIAS=default
```

#### **API Keys and Integrations**
```bash
# Twilio configuration
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# OpenAI configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4                            # or gpt-3.5-turbo
OPENAI_MAX_TOKENS=2000

# Webhook configuration
WEBHOOK_URL=https://yourdomain.com/sms/receive
WEBHOOK_SECRET=optional_webhook_secret
```

#### **Rate Limiting**
```bash
# Per-tier rate limits (requests per hour)
RATE_LIMIT_FREE=10
RATE_LIMIT_PREMIUM=50
RATE_LIMIT_ENTERPRISE=1000

# Rate limiting window
RATE_LIMIT_WINDOW=3600                        # 1 hour in seconds
```

### **Docker Compose Customization**

#### **Custom docker-compose.override.yml**
```yaml
version: '3.8'

services:
  web:
    ports:
      - "8000:8000"  # Change port mapping
    environment:
      - DEBUG=True
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads

  database:
    ports:
      - "5432:5432"  # Expose database port
    volumes:
      - ./database/custom.conf:/etc/postgresql/postgresql.conf

  redis:
    ports:
      - "6379:6379"  # Expose Redis port
```

---

## 🧪 **Testing Installation**

### **Health Checks**
```bash
# Application health
curl http://localhost:5001/health

# Database connectivity
docker-compose exec web python manage.py dbshell

# Redis connectivity
docker-compose exec redis redis-cli ping

# All services status
docker-compose ps
```

### **Functional Testing**
```bash
# Test SMS webhook (replace with your ngrok URL)
curl -X POST http://localhost:5001/sms/receive \
  -d "From=+1234567890" \
  -d "Body=Hello, test message!" \
  -d "MessageSid=test123"

# Test admin dashboard
curl -I http://localhost:5001/dashboard/

# Test Django admin
curl -I http://localhost:5001/admin/

# Test API endpoints
curl http://localhost:5001/api/
```

### **Load Testing**
```bash
# Install testing tools
pip install locust

# Run load test
locust -f tests/load_test.py --host=http://localhost:5001
```

---

## 🚨 **Troubleshooting Installation**

### **Common Issues**

#### **Docker Issues**
```bash
# Permission denied
sudo usermod -aG docker $USER
# Then logout and login again

# Port already in use
sudo netstat -tulpn | grep :5001
sudo kill -9 <PID>

# Docker daemon not running
sudo systemctl start docker
```

#### **Database Issues**
```bash
# Connection refused
docker-compose logs database

# Migration errors
docker-compose exec web python manage.py migrate --fake-initial

# Database doesn't exist
docker-compose exec database createdb -U sms_agent sms_agent_db
```

#### **Environment Issues**
```bash
# Missing environment variables
docker-compose exec web env | grep -E "(TWILIO|OPENAI|DATABASE)"

# Invalid configuration
docker-compose config
```

#### **Network Issues**
```bash
# ngrok not accessible
ngrok http 5001 --log=stdout

# Webhook not receiving
curl -X POST <your-webhook-url>/sms/receive -d "From=test&Body=test"

# DNS issues
dig yourdomain.com
nslookup yourdomain.com
```

---

## 🔄 **Post-Installation Steps**

### **1. Configure Twilio Webhook**
- Update webhook URL in Twilio console
- Test webhook with a test SMS

### **2. Set Up Monitoring**
- Configure log rotation
- Set up health check monitoring
- Configure alerting

### **3. Security Hardening**
- Change default passwords
- Configure SSL certificates
- Set up firewall rules
- Enable audit logging

### **4. Performance Optimization**
- Configure database connection pooling
- Set up Redis caching
- Optimize Docker resource limits

---

## 📚 **Next Steps**

After successful installation:

1. **[Configuration Guide](CONFIGURATION.md)** - Fine-tune your setup
2. **[User Guide](../user-guides/USER_GUIDE.md)** - Learn how to use the system
3. **[Admin Guide](../user-guides/ADMIN_GUIDE.md)** - Manage users and system
4. **[Production Deployment](../operations/PRODUCTION.md)** - Deploy to production

---

## 🆘 **Getting Help**

- **Issues**: Check [Troubleshooting Guide](../operations/TROUBLESHOOTING.md)
- **Configuration**: See [Configuration Guide](CONFIGURATION.md)
- **Production**: Review [Production Guide](../operations/PRODUCTION.md)

---

**🎉 Installation complete! Your SMS-to-AI Agent is ready to use.** 