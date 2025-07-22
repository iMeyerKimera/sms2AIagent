# 🚀 Enhanced SMS-to-Cursor AI Agent - Production Setup Guide

## Prerequisites

- Docker and Docker Compose installed
- Twilio account with phone number
- OpenAI API key
- Domain/server for deployment (optional)

## Quick Production Deployment

### 1. Clone and Setup

```bash
git clone <your-repo>
cd sms2AIagent
```

### 2. Create Production Environment

Copy the environment template:
```bash
cp env.example .env
```

Edit `.env` with your production credentials:

#### 🔐 Required Variables (MUST SET):
```bash
# Twilio Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890

# OpenAI Configuration  
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Flask Security
FLASK_SECRET_KEY=your-256-bit-secret-key-here
FLASK_ENV=production
FLASK_DEBUG=false

# Admin Dashboard
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_secure_admin_password
```

#### 📧 Optional Variables (Recommended):
```bash
# Email Notifications
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com

# Slack Alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SLACK_CHANNEL=#alerts

# Ngrok (for webhook testing)
NGROK_AUTHTOKEN=your_ngrok_auth_token
```

### 3. Deploy with Docker

#### Option A: Quick Deployment
```bash
./deploy.sh
```

#### Option B: Production Deployment
```bash
./deploy.sh --production
```

#### Option C: Manual Docker Compose
```bash
# Build and start
docker-compose up --build -d

# Check status
docker-compose ps
docker-compose logs -f web
```

### 4. Verify Deployment

```bash
# Health check
curl http://localhost:5001/health

# Admin dashboard
open http://localhost:5001/admin/

# Ngrok tunnel (if enabled)
open http://localhost:4040
```

## Production Configuration Details

### 🏗️ Docker Configuration

The enhanced Docker setup includes:

- **Python 3.11-slim** base image
- **Audio processing** libraries for voice features
- **SQLite** support for databases
- **Enhanced health checks** with 60s startup time
- **Production Gunicorn** with 3 workers, 180s timeout
- **Volume persistence** for databases and logs
- **Resource limits** and logging configuration

### 📊 Database Persistence

Databases are automatically created and persisted:
- `task_analytics.db` - User activity, tasks, system metrics
- `notifications.db` - Notification history, user preferences, alert rules

### 🔄 Auto-scaling Ready

Optional Redis service for future scaling:
```bash
# Enable Redis for session management
docker-compose --profile scaling up -d
```

### 🔒 Security Features

- Twilio signature validation
- Rate limiting per user tier
- Admin dashboard authentication
- Request size limits
- CORS protection

## Twilio Webhook Configuration

### 1. Get Webhook URL

If using ngrok:
```bash
# Get your public URL
curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url'
```

### 2. Configure Twilio Console

1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to **Phone Numbers** → **Manage** → **Active numbers**
3. Click your phone number
4. Set webhook URL: `https://your-domain.com/sms` (or ngrok URL + `/sms`)
5. Set HTTP method: **POST**
6. Save configuration

## Monitoring and Maintenance

### 📈 Admin Dashboard

Access at `http://localhost:5001/admin/`

Features:
- Real-time system metrics
- User management and analytics
- Task categorization reports
- Error monitoring
- Performance charts

### 📋 Health Monitoring

```bash
# Comprehensive health check
curl http://localhost:5001/health | jq

# Container health
docker-compose exec web /app/docker-healthcheck.sh

# View logs
docker-compose logs -f web
tail -f logs/sms_agent.log
```

### 🔄 Maintenance Commands

```bash
# Restart services
docker-compose restart

# Update and rebuild
git pull
docker-compose up --build -d

# Database backup
docker-compose exec web sqlite3 task_analytics.db ".backup backup_$(date +%Y%m%d).db"

# View real-time metrics
docker-compose exec web sqlite3 task_analytics.db "SELECT * FROM system_metrics ORDER BY timestamp DESC LIMIT 10;"
```

## Advanced Features Configuration

### 🎯 Task Routing

Configure intelligent task categorization:
```bash
ENABLE_ADVANCED_ROUTING=true
DEFAULT_USER_TIER=free
RATE_LIMIT_FREE=10      # SMS per hour
RATE_LIMIT_PREMIUM=50   # SMS per hour
RATE_LIMIT_ENTERPRISE=unlimited
```

### 🤖 AI Model Configuration

```bash
DEFAULT_AI_MODEL=gpt-4
FALLBACK_AI_MODEL=gpt-3.5-turbo
MAX_TOKENS_FREE=1000
MAX_TOKENS_PREMIUM=4000
MAX_TOKENS_ENTERPRISE=8000
```

### 📱 Notification Channels

Enable multi-channel notifications:
```bash
# Email
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_CHANNEL=#alerts

# Discord  
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

## Performance Tuning

### 🚀 Production Optimizations

```bash
# Gunicorn workers (adjust based on CPU cores)
GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=180
GUNICORN_MAX_REQUESTS=1000

# AI processing timeouts
AI_REQUEST_TIMEOUT=60
AI_RETRY_ATTEMPTS=3

# Rate limiting
GLOBAL_RATE_LIMIT=1000
PER_USER_RATE_LIMIT=100
```

### 📊 Resource Monitoring

Monitor resource usage:
```bash
# Container stats
docker stats enhanced_sms_agent

# Database size
du -h *.db

# Log size
du -h logs/
```

## Troubleshooting

### 🔍 Common Issues

#### SMS not working:
1. Check Twilio webhook URL is correct
2. Verify phone number is SMS-enabled
3. Check Twilio credentials in `.env`
4. Review logs: `docker-compose logs web`

#### AI responses failing:
1. Verify OpenAI API key is valid
2. Check rate limits and quotas
3. Review error logs for API issues

#### Admin dashboard not accessible:
1. Check Flask secret key is set
2. Verify admin credentials
3. Check if port 5001 is accessible

#### Health check failing:
1. Run manual health check: `curl http://localhost:5001/health`
2. Check database permissions
3. Verify all environment variables

### 📞 Support

Check logs for detailed error information:
```bash
# Application logs
docker-compose logs -f web

# Specific error grep
docker-compose logs web | grep ERROR

# Database access
docker-compose exec web sqlite3 task_analytics.db ".tables"
```

## 🔐 Security Checklist

- [ ] Changed default admin password
- [ ] Set strong Flask secret key
- [ ] Configured Twilio signature validation
- [ ] Set up HTTPS/SSL certificates
- [ ] Configured firewall rules
- [ ] Set up database backups
- [ ] Enabled monitoring and alerts
- [ ] Reviewed rate limiting settings
- [ ] Tested disaster recovery

---

**Your Enhanced SMS-to-Cursor AI Agent is now ready for production! 🎉** 