# 📱 SMS-to-AI Agent

**Turn your phone into a powerful AI development assistant!** Send SMS messages to get instant help with coding, debugging, design, and more - all powered by advanced AI and intelligent task routing.

---

## 🚀 **Quick Start**

### **Get Running in 5 Minutes**
```bash
# Clone and start
git clone <your-repo>
cd sms2AIagent
cp env.example .env
# Edit .env with your Twilio & OpenAI credentials
docker-compose up -d

# Check health
curl http://localhost:5001/health
```

**📚 [Complete Quick Start Guide](docs/getting-started/QUICK_START.md)**

---

## 🎯 **Key Features**

- **📱 SMS Processing**: Intelligent SMS-to-AI task routing
- **🧠 AI Integration**: OpenAI and Cursor AI integration  
- **👥 User Management**: Multi-tier user system (Free/Premium/Enterprise)
- **📊 Analytics Dashboard**: Real-time system monitoring and user analytics
- **🔧 Admin Tools**: Complete administrative interface
- **🐳 Docker Ready**: Containerized deployment with PostgreSQL and Redis
- **📈 Scalable**: Production-ready with monitoring and logging

---

## 📖 **Documentation**

### **🎯 New Users - Start Here**
- **[🚀 Quick Start](docs/getting-started/QUICK_START.md)** - Get running in 5 minutes
- **[📱 User Guide](docs/user-guides/USER_GUIDE.md)** - Complete SMS usage guide
- **[🔧 Admin Guide](docs/user-guides/ADMIN_GUIDE.md)** - Dashboard and user management

### **⚙️ Setup & Deployment**
- **[📦 Installation Guide](docs/getting-started/INSTALLATION.md)** - Complete setup instructions
- **[🚀 Production Deployment](docs/operations/PRODUCTION.md)** - Production-ready deployment
- **[🔍 Troubleshooting](docs/operations/TROUBLESHOOTING.md)** - Common issues and solutions

### **💻 Development**
- **[🏗️ Architecture](docs/development/ARCHITECTURE.md)** - System design and architecture
- **[🗄️ Database Guide](docs/development/DATABASE.md)** - Database schema and management
- **[🔌 API Reference](docs/user-guides/API_REFERENCE.md)** - REST API documentation

### **📚 [Complete Documentation Index](docs/README.md)**

---

## 🎮 **How It Works**

### **For SMS Users**
1. **Send SMS** to your Twilio number
2. **AI analyzes** your message and determines the best approach
3. **Intelligent routing** directs coding questions to specialized AI models
4. **Get responses** optimized for your request type and user tier

### **For Administrators**
1. **Monitor everything** via the web dashboard
2. **Manage users** and upgrade/downgrade tiers
3. **Send messages** to individual users or broadcast to all
4. **View analytics** and system performance metrics

---

## 🏗️ **System Architecture**

```
[SMS Users] → [Twilio] → [SMS-to-AI Agent] → [OpenAI/Cursor AI]
                              ↓
                      [PostgreSQL Database]
                              ↓
                      [Admin Dashboard] ← [Administrators]
```

### **Technology Stack**
- **Backend**: Django + Django REST Framework
- **Database**: PostgreSQL with Redis caching
- **AI Integration**: OpenAI GPT-4, Cursor AI
- **SMS**: Twilio API
- **Frontend**: Bootstrap + JavaScript
- **Deployment**: Docker + Docker Compose

---

## 🔗 **Quick Access**

### **System URLs**
- **Admin Dashboard**: http://localhost:5001/dashboard/
- **Django Admin**: http://localhost:5001/admin/
- **API Documentation**: http://localhost:5001/api/
- **Health Check**: http://localhost:5001/health

### **Default Credentials**
- **Admin Dashboard**: admin / admin123
- **Django Admin**: Create superuser with `python manage.py createsuperuser`

---

## 👥 **User Tiers**

| Tier | SMS/Hour | AI Tokens | Features |
|------|----------|-----------|----------|
| 🆓 **Free** | 10 | 1,000 | Basic task routing |
| ⭐ **Premium** | 50 | 4,000 | Enhanced routing, priority |
| 🏢 **Enterprise** | Unlimited | 8,000 | Custom configs, white-label |

---

## 🧠 **Intelligent Task Routing**

The system automatically categorizes and routes SMS messages:

- **🖥️ Coding**: Programming tasks, code generation
- **🐛 Debug**: Error analysis, troubleshooting  
- **🎨 Design**: UI/UX design, architecture planning
- **📝 Documentation**: Writing docs, README files
- **📊 Analysis**: Data analysis, research
- **💬 General**: Questions, conversations, explanations

Each category gets optimized AI prompts and processing parameters.

---

## 🚀 **Getting Started Paths**

### **🆕 First Time User?**
1. **[Quick Start](docs/getting-started/QUICK_START.md)** - Get running in 5 minutes
2. **[User Guide](docs/user-guides/USER_GUIDE.md)** - Learn to use SMS features
3. **[Admin Guide](docs/user-guides/ADMIN_GUIDE.md)** - Manage users and system

### **🔧 Production Deployment?**
1. **[Installation Guide](docs/getting-started/INSTALLATION.md)** - Complete setup
2. **[Production Deployment](docs/operations/PRODUCTION.md)** - Production best practices
3. **[Monitoring Guide](docs/operations/MONITORING.md)** - Set up monitoring

### **💻 Developer/Customization?**
1. **[Architecture Guide](docs/development/ARCHITECTURE.md)** - Understand the system
2. **[Database Guide](docs/development/DATABASE.md)** - Database schema and operations
3. **[API Reference](docs/user-guides/API_REFERENCE.md)** - API endpoints and usage

---

## 🆘 **Need Help?**

### **Common Issues**
- **[Troubleshooting Guide](docs/operations/TROUBLESHOOTING.md)** - Comprehensive issue resolution
- **[Production Issues](docs/operations/PRODUCTION.md#troubleshooting)** - Production-specific problems

### **Feature Questions**
- **[User Guide](docs/user-guides/USER_GUIDE.md)** - Complete feature documentation
- **[Admin Guide](docs/user-guides/ADMIN_GUIDE.md)** - Administrative functions
- **[API Reference](docs/user-guides/API_REFERENCE.md)** - REST API details

---

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📞 **Support**

- **Documentation**: [Complete Documentation](docs/README.md)
- **Issues**: Use the issue tracker for bug reports
- **Production Support**: See [Production Guide](docs/operations/PRODUCTION.md)

---

**🎉 Ready to transform SMS into intelligent AI assistance? Start with the [Quick Start Guide](docs/getting-started/QUICK_START.md)!**

