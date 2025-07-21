# ⚙️ Configuration Guide

**Complete configuration reference for SMS-to-AI Agent**

---

## 📋 **Overview**

This guide covers all configuration options for SMS-to-AI Agent, from basic setup to advanced customization. Configuration is managed through environment variables and Django settings.

---

## 🔧 **Environment Configuration**

### **Basic Configuration (.env)**

```bash
# ===== CORE APPLICATION SETTINGS =====
DJANGO_SETTINGS_MODULE=sms_agent.settings
DJANGO_SECRET_KEY=your-super-secure-secret-key-minimum-50-characters-long
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,localhost,127.0.0.1

# ===== DATABASE CONFIGURATION =====
DATABASE_URL=postgresql://sms_agent:secure_password@database:5432/sms_agent_db
DB_NAME=sms_agent_db
DB_USER=sms_agent
DB_PASSWORD=secure_database_password
DB_HOST=database
DB_PORT=5432

# ===== REDIS CONFIGURATION =====
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# ===== TWILIO INTEGRATION =====
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WEBHOOK_SECRET=optional_webhook_secret

# ===== OPENAI INTEGRATION =====
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7

# ===== ADMIN CREDENTIALS =====
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_admin_password
ADMIN_EMAIL=admin@yourdomain.com

# ===== RATE LIMITING =====
RATE_LIMIT_FREE=10
RATE_LIMIT_PREMIUM=50
RATE_LIMIT_ENTERPRISE=1000
RATE_LIMIT_WINDOW=3600

# ===== EXTERNAL URLS =====
WEBHOOK_URL=https://yourdomain.com/sms/receive
ADMIN_URL=https://yourdomain.com/dashboard/
API_BASE_URL=https://yourdomain.com/api/
```

---

## 🏗️ **Django Settings Configuration**

### **Development Settings (settings/development.py)**

```python
from .base import *

# Debug settings
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*.ngrok-free.app']

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'sms_agent_db'),
        'USER': os.getenv('DB_USER', 'sms_agent'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 0,  # Close connections immediately
    }
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/development.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'sms_agent': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    },
}

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### **Production Settings (settings/production.py)**

```python
from .base import *

# Security settings
DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Security middleware
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Database configuration with connection pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': {
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,
        }
    }
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/production.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/errors.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
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
    },
}
```

---

## 🔐 **Security Configuration**

### **Secret Key Generation**

```python
# Generate a secure secret key
import secrets
secret_key = secrets.token_urlsafe(50)
print(f"DJANGO_SECRET_KEY={secret_key}")
```

### **CORS Configuration**

```python
# settings/base.py
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
```

### **CSRF Configuration**

```python
# Trusted origins for CSRF
CSRF_TRUSTED_ORIGINS = [
    'https://yourdomain.com',
    'https://www.yourdomain.com',
]

# CSRF cookie settings
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
```

---

## 📡 **API Configuration**

### **Twilio Settings**

```python
# Twilio configuration
TWILIO_SETTINGS = {
    'ACCOUNT_SID': os.getenv('TWILIO_ACCOUNT_SID'),
    'AUTH_TOKEN': os.getenv('TWILIO_AUTH_TOKEN'),
    'PHONE_NUMBER': os.getenv('TWILIO_PHONE_NUMBER'),
    'WEBHOOK_SECRET': os.getenv('TWILIO_WEBHOOK_SECRET'),
    'VERIFY_WEBHOOKS': True,
    'TIMEOUT': 30,
    'RETRY_ATTEMPTS': 3,
}
```

### **OpenAI Settings**

```python
# OpenAI configuration
OPENAI_SETTINGS = {
    'API_KEY': os.getenv('OPENAI_API_KEY'),
    'MODEL': os.getenv('OPENAI_MODEL', 'gpt-4'),
    'MAX_TOKENS': int(os.getenv('OPENAI_MAX_TOKENS', '2000')),
    'TEMPERATURE': float(os.getenv('OPENAI_TEMPERATURE', '0.7')),
    'TIMEOUT': 60,
    'MAX_RETRIES': 3,
}
```

### **Rate Limiting Configuration**

```python
# Rate limiting settings
RATE_LIMITING = {
    'FREE_TIER': {
        'REQUESTS_PER_HOUR': int(os.getenv('RATE_LIMIT_FREE', '10')),
        'TOKENS_PER_REQUEST': 1000,
        'DAILY_LIMIT': 50,
    },
    'PREMIUM_TIER': {
        'REQUESTS_PER_HOUR': int(os.getenv('RATE_LIMIT_PREMIUM', '50')),
        'TOKENS_PER_REQUEST': 4000,
        'DAILY_LIMIT': 500,
    },
    'ENTERPRISE_TIER': {
        'REQUESTS_PER_HOUR': int(os.getenv('RATE_LIMIT_ENTERPRISE', '1000')),
        'TOKENS_PER_REQUEST': 8000,
        'DAILY_LIMIT': -1,  # Unlimited
    },
}
```

---

## 🗄️ **Database Configuration**

### **PostgreSQL Optimization**

```python
# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c default_transaction_isolation=read_committed'
        },
    }
}

# Connection pooling
DATABASE_POOL_SETTINGS = {
    'MAX_OVERFLOW': 10,
    'POOL_SIZE': 20,
    'POOL_RECYCLE': 300,
    'POOL_TIMEOUT': 30,
}
```

### **Redis Configuration**

```python
# Redis settings
REDIS_SETTINGS = {
    'HOST': os.getenv('REDIS_HOST', 'localhost'),
    'PORT': int(os.getenv('REDIS_PORT', '6379')),
    'DB': int(os.getenv('REDIS_DB', '0')),
    'PASSWORD': os.getenv('REDIS_PASSWORD'),
    'CONNECTION_POOL_KWARGS': {
        'max_connections': 20,
        'retry_on_timeout': True,
    },
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours
```

---

## 📧 **Email Configuration**

### **SMTP Settings**

```python
# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@yourdomain.com')

# Email templates
EMAIL_TEMPLATES = {
    'USER_WELCOME': 'emails/welcome.html',
    'TASK_COMPLETED': 'emails/task_completed.html',
    'ERROR_ALERT': 'emails/error_alert.html',
    'TIER_UPGRADE': 'emails/tier_upgrade.html',
}
```

---

## 📊 **Logging Configuration**

### **Comprehensive Logging Setup**

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 1024*1024*15,
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
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'sms_agent': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
        },
        'sms_agent.sms': {
            'handlers': ['sms_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'sms_agent.ai': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
        },
    },
}
```

---

## 🔄 **Cache Configuration**

### **Redis Caching Setup**

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 20,
                'retry_on_timeout': True,
            },
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'sms_agent',
        'TIMEOUT': 3600,  # 1 hour default
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'sessions',
        'TIMEOUT': 86400,  # 24 hours
    },
}
```

---

## 🚀 **Performance Configuration**

### **Database Optimization**

```python
# Database optimization settings
DATABASE_OPTIMIZATION = {
    'CONN_MAX_AGE': 600,
    'ATOMIC_REQUESTS': False,
    'AUTOCOMMIT': True,
    'OPTIONS': {
        'MAX_CONNS': 20,
        'MIN_CONNS': 5,
        'POOL_RECYCLE': 300,
    },
}
```

### **Static Files Configuration**

```python
# Static files settings
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Media files settings
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

---

## 🔧 **Custom Configuration Classes**

### **Configuration Manager**

```python
# config/manager.py
class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self):
        self.twilio = self._load_twilio_config()
        self.openai = self._load_openai_config()
        self.rate_limits = self._load_rate_limits()
        
    def _load_twilio_config(self):
        return {
            'account_sid': os.getenv('TWILIO_ACCOUNT_SID'),
            'auth_token': os.getenv('TWILIO_AUTH_TOKEN'),
            'phone_number': os.getenv('TWILIO_PHONE_NUMBER'),
            'webhook_secret': os.getenv('TWILIO_WEBHOOK_SECRET'),
            'verify_webhooks': os.getenv('TWILIO_VERIFY_WEBHOOKS', 'True').lower() == 'true',
        }
    
    def _load_openai_config(self):
        return {
            'api_key': os.getenv('OPENAI_API_KEY'),
            'model': os.getenv('OPENAI_MODEL', 'gpt-4'),
            'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', '2000')),
            'temperature': float(os.getenv('OPENAI_TEMPERATURE', '0.7')),
        }
    
    def _load_rate_limits(self):
        return {
            'free': int(os.getenv('RATE_LIMIT_FREE', '10')),
            'premium': int(os.getenv('RATE_LIMIT_PREMIUM', '50')),
            'enterprise': int(os.getenv('RATE_LIMIT_ENTERPRISE', '1000')),
        }

# Usage in settings
config = ConfigManager()
```

---

## 🧪 **Environment-Specific Configurations**

### **Development Environment**

```bash
# .env.development
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,*.ngrok-free.app
DATABASE_URL=postgresql://sms_agent:password@localhost:5432/sms_agent_dev
REDIS_URL=redis://localhost:6379/0
OPENAI_MODEL=gpt-3.5-turbo
RATE_LIMIT_FREE=100
LOG_LEVEL=DEBUG
```

### **Staging Environment**

```bash
# .env.staging
DEBUG=False
ALLOWED_HOSTS=staging.yourdomain.com
DATABASE_URL=postgresql://sms_agent:secure_password@staging-db:5432/sms_agent_staging
REDIS_URL=redis://staging-redis:6379/0
OPENAI_MODEL=gpt-4
SECURE_SSL_REDIRECT=True
LOG_LEVEL=INFO
```

### **Production Environment**

```bash
# .env.production
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://sms_agent:ultra_secure_password@prod-db:5432/sms_agent_prod
REDIS_URL=redis://prod-redis:6379/0
OPENAI_MODEL=gpt-4
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
LOG_LEVEL=WARNING
```

---

## 📋 **Configuration Checklist**

### **Before Deployment**

- [ ] **Environment Variables**: All required variables set
- [ ] **Secret Key**: Strong, unique secret key generated
- [ ] **Database**: Connection tested and migrations applied
- [ ] **Redis**: Connection tested and caching working
- [ ] **Twilio**: Webhook URL configured and tested
- [ ] **OpenAI**: API key valid and quotas set
- [ ] **SSL**: Certificates installed and HTTPS working
- [ ] **Logging**: Log files writable and rotation configured
- [ ] **Rate Limits**: Appropriate limits for each tier
- [ ] **Security**: All security headers and settings enabled

### **Post-Deployment Validation**

```bash
# Health checks
curl https://yourdomain.com/health
curl https://yourdomain.com/admin/
curl https://yourdomain.com/dashboard/

# Test SMS functionality
# Send test SMS to your Twilio number

# Check logs
tail -f logs/app.log
tail -f logs/errors.log
```

---

## 🆘 **Configuration Troubleshooting**

### **Common Issues**

#### **Environment Variables Not Loading**
```bash
# Check if variables are set
docker-compose exec web env | grep TWILIO
docker-compose exec web env | grep OPENAI

# Verify .env file syntax
cat .env | grep -E "^[A-Z_]+=.*$"
```

#### **Database Connection Issues**
```bash
# Test database connection
docker-compose exec web python manage.py dbshell

# Check database URL format
echo $DATABASE_URL
```

#### **Redis Connection Issues**
```bash
# Test Redis connection
docker-compose exec web python -c "import redis; r=redis.from_url('redis://redis:6379/0'); print(r.ping())"
```

---

## 📚 **Next Steps**

After configuration:

1. **[User Guide](../user-guides/USER_GUIDE.md)** - Learn system features
2. **[Admin Guide](../user-guides/ADMIN_GUIDE.md)** - Administrative tasks
3. **[Production Guide](../operations/PRODUCTION.md)** - Production deployment
4. **[Monitoring Guide](../operations/MONITORING.md)** - Set up monitoring

---

**⚙️ Your SMS-to-AI Agent is now properly configured and ready for use!** 