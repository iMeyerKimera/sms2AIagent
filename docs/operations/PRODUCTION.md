# 🚀 Production Deployment Guide

**Complete guide for deploying SMS-to-AI Agent in production environments**

---

## 📋 **Overview**

This guide covers production deployment with:
- **Docker & Docker Compose** orchestration
- **PostgreSQL** database with persistence
- **Redis** for caching and sessions
- **Nginx** reverse proxy
- **SSL/TLS** certificates
- **Monitoring & Logging**
- **Backup strategies**

---

## 🏗️ **Production Architecture**

```
[SMS Users] → [Twilio] → [Nginx/SSL] → [Django App] → [PostgreSQL]
                                    ↓
                               [Redis Cache]
                                    ↓
                            [Admin Dashboard]
```

---

## ⚙️ **Prerequisites**

### **Infrastructure Requirements**
- **Server**: 2+ CPU cores, 4GB+ RAM, 20GB+ storage
- **OS**: Ubuntu 20.04+ or CentOS 8+
- **Docker**: 20.10+ with Docker Compose 2.0+
- **Domain**: For SSL certificates and webhooks

### **External Services**
- **Twilio Account**: SMS service provider
- **OpenAI API Key**: AI processing (optional)
- **SSL Certificate**: Let's Encrypt or commercial

---

## 🐳 **Production Docker Setup**

### **1. Production Environment File**
Create `.env.prod`:
```bash
# Django Settings
DJANGO_SETTINGS_MODULE=sms_agent.settings
DJANGO_SECRET_KEY=your-super-secret-production-key-here-make-it-long
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,localhost

# Database Configuration
DATABASE_URL=postgresql://sms_agent:secure_password_here@database:5432/sms_agent_db
DB_NAME=sms_agent_db
DB_USER=sms_agent
DB_PASSWORD=secure_password_here
DB_HOST=database
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379

# Twilio Configuration
TWILIO_ACCOUNT_SID=your_production_account_sid
TWILIO_AUTH_TOKEN=your_production_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# OpenAI Configuration
OPENAI_API_KEY=your_production_openai_key

# Admin Credentials
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=secure_admin_password_here

# Security Settings
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Rate Limiting
RATE_LIMIT_FREE=10
RATE_LIMIT_PREMIUM=50
RATE_LIMIT_ENTERPRISE=1000

# External URLs
WEBHOOK_URL=https://yourdomain.com/sms/receive
ADMIN_URL=https://yourdomain.com/dashboard/
```

### **2. Production Docker Compose**
Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  database:
    image: postgres:15
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/backups:/backups
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - backend
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  web:
    build:
      context: .
      dockerfile: Dockerfile.prod
    restart: unless-stopped
    env_file:
      - .env.prod
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - ./logs:/app/logs
    networks:
      - backend
      - frontend
    depends_on:
      database:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - static_volume:/usr/share/nginx/html/static
      - media_volume:/usr/share/nginx/html/media
    networks:
      - frontend
    depends_on:
      - web

  backup:
    image: postgres:15
    restart: "no"
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - ./database/backups:/backups
      - ./scripts/backup.sh:/backup.sh
    networks:
      - backend
    command: /bin/bash /backup.sh
    profiles:
      - backup

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true
```

---

## 🔒 **SSL & Security Setup**

### **1. Nginx Configuration**
Create `nginx/nginx.conf`:
```nginx
events {
    worker_connections 1024;
}

http {
    upstream web {
        server web:8000;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
        ssl_prefer_server_ciphers off;
        
        add_header Strict-Transport-Security "max-age=63072000" always;
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;

        client_max_body_size 10M;

        location / {
            proxy_pass http://web;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_redirect off;
        }

        location /static/ {
            alias /usr/share/nginx/html/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        location /media/ {
            alias /usr/share/nginx/html/media/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

### **2. SSL Certificate Setup**
```bash
# Install Certbot
sudo apt update
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/

# Set permissions
sudo chmod 644 nginx/ssl/fullchain.pem
sudo chmod 600 nginx/ssl/privkey.pem
```

---

## 🚀 **Deployment Process**

### **1. Server Setup**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### **2. Application Deployment**
```bash
# Clone repository
git clone <your-repo-url>
cd sms2AIagent

# Set up environment
cp env.example .env.prod
# Edit .env.prod with production values

# Create required directories
mkdir -p logs database/backups nginx/ssl

# Deploy application
docker-compose -f docker-compose.prod.yml up -d

# Check deployment
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs
```

### **3. Database Initialization**
```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

---

## 📊 **Monitoring & Logging**

### **1. Application Logs**
```bash
# View application logs
docker-compose -f docker-compose.prod.yml logs web -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs database -f
docker-compose -f docker-compose.prod.yml logs redis -f
docker-compose -f docker-compose.prod.yml logs nginx -f

# Log rotation setup
sudo logrotate -d /etc/logrotate.d/docker-logs
```

### **2. Health Monitoring**
```bash
# Check service health
curl https://yourdomain.com/health

# Monitor system resources
docker stats

# Check database connection
docker-compose -f docker-compose.prod.yml exec database pg_isready -U sms_agent
```

---

## 💾 **Backup & Recovery**

### **1. Database Backup Script**
Create `scripts/backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/sms_agent_backup_$TIMESTAMP.sql"

# Create backup
pg_dump -h database -U sms_agent -d sms_agent_db > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

### **2. Automated Backups**
```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * cd /path/to/sms2AIagent && docker-compose -f docker-compose.prod.yml run --rm backup
```

### **3. Recovery Process**
```bash
# Stop application
docker-compose -f docker-compose.prod.yml down

# Restore database
gunzip -c backup_file.sql.gz | docker-compose -f docker-compose.prod.yml exec -T database psql -U sms_agent -d sms_agent_db

# Restart application
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔧 **Production Optimizations**

### **1. Performance Tuning**
```bash
# PostgreSQL optimization
# Edit postgresql.conf:
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# Redis optimization
# Edit redis.conf:
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### **2. Security Hardening**
```bash
# Firewall setup
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Fail2ban setup
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 🌐 **External Service Configuration**

### **1. Twilio Webhook Setup**
1. Log into Twilio Console
2. Go to Phone Numbers → Manage → Active Numbers
3. Click your SMS-enabled number
4. Set webhook URL: `https://yourdomain.com/sms/receive`
5. Set HTTP method: POST
6. Save configuration

### **2. Domain DNS Setup**
```
# DNS Records
A    yourdomain.com      your.server.ip.address
A    www.yourdomain.com  your.server.ip.address
```

---

## 🚨 **Troubleshooting**

### **Common Production Issues**
```bash
# SSL certificate issues
sudo certbot renew --dry-run

# Database connection issues
docker-compose -f docker-compose.prod.yml exec database psql -U sms_agent -d sms_agent_db

# Application not responding
docker-compose -f docker-compose.prod.yml restart web

# Disk space issues
docker system prune -a
```

---

## 📈 **Scaling Considerations**

### **Horizontal Scaling**
- **Load Balancer**: Multiple web instances behind nginx
- **Database Replication**: Read replicas for analytics
- **Redis Cluster**: For high availability
- **CDN**: For static files

### **Vertical Scaling**
- **CPU**: Increase for AI processing
- **Memory**: More RAM for database and Redis
- **Storage**: SSD for database performance

---

**🎉 Your SMS-to-AI Agent is now production-ready!**

**For ongoing maintenance, see [Monitoring Guide](MONITORING.md) and [Troubleshooting Guide](TROUBLESHOOTING.md)** 