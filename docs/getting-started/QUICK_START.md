# 🚀 Quick Start Guide

**Get your SMS-to-AI Agent running in 5 minutes!**

---

## ⚡ **Prerequisites**

- **Docker & Docker Compose** installed
- **Twilio Account** (free trial available)
- **OpenAI API Key** (optional but recommended)

---

## 🛠️ **5-Minute Setup**

### **1. Clone & Configure**
```bash
# Clone the repository
git clone <your-repo-url>
cd sms2AIagent

# Copy environment template
cp env.example .env
```

### **2. Set Essential Environment Variables**
Edit `.env` file with your credentials:
```bash
# Required - Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token  
TWILIO_PHONE_NUMBER=+1234567890

# Required - Database
DATABASE_URL=postgresql://sms_agent:your_password@database:5432/sms_agent_db

# Optional but Recommended - AI
OPENAI_API_KEY=your_openai_api_key

# Admin Access
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### **3. Start the System**
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### **4. Verify Everything Works**
```bash
# Check health
curl http://localhost:5001/health

# Expected response: {"status": "healthy"}
```

---

## 📱 **Test Your Setup**

### **1. Configure Twilio Webhook**
In your Twilio Console:
- Go to Phone Numbers → Manage → Active Numbers
- Click your SMS-enabled number
- Set webhook URL: `https://your-ngrok-url.com/sms/receive`

### **2. Send Test SMS**
Send an SMS to your Twilio number:
```
"Hello! Can you help me with Python code?"
```

### **3. Access Admin Dashboard**
- URL: http://localhost:5001/dashboard/
- Login: admin / admin123
- Check the Users section to see your SMS

---

## ✅ **You're Ready!**

Your SMS-to-AI Agent is now running! Here's what you can do:

### **📱 For SMS Users**
- Send coding questions, debug help, or general queries
- Users are automatically registered on first SMS
- Different user tiers available (Free/Premium/Enterprise)

### **🔧 For Administrators**
- **Dashboard**: http://localhost:5001/dashboard/
- **User Management**: View, message, and manage user tiers
- **Analytics**: Monitor usage and system performance
- **System Health**: Real-time system monitoring

---

## 📚 **Next Steps**

- **[Complete User Guide](../user-guides/USER_GUIDE.md)** - Learn all SMS features
- **[Admin Guide](../user-guides/ADMIN_GUIDE.md)** - Master the admin dashboard
- **[Production Setup](../operations/PRODUCTION.md)** - Deploy for production use
- **[Configuration Guide](CONFIGURATION.md)** - Advanced configuration options

---

## 🆘 **Quick Troubleshooting**

### **Service Won't Start**
```bash
# Check logs
docker-compose logs web
docker-compose logs database
```

### **SMS Not Working**
1. Verify Twilio credentials in `.env`
2. Check webhook URL is accessible
3. Review Twilio console logs

### **Health Check Fails**
```bash
# Restart services
docker-compose restart

# Check individual services
docker-compose logs web --tail=20
```

---

**🎉 Congratulations! Your SMS-to-AI Agent is live and ready to help users!**

**Having issues? Check the [Troubleshooting Guide](../operations/TROUBLESHOOTING.md) or [Configuration Guide](CONFIGURATION.md) for more details.** 