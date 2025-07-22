# 📱 SMS-to-AI Agent

**Turn your phone into a powerful AI development assistant!** Send SMS messages to get instant help with coding, debugging, design, and more - all powered by advanced AI and intelligent task routing.

---

## 🚀 **Quick Start**

### **Get Running in 5 Minutes**
```bash
# Clone and start
git clone https://github.com/iMeyerKimera/sms2AIagent.git
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

---

## 📄 **License**

This project is released under the **MIT License** to encourage community contribution and adoption.

### **MIT License Summary**
- **License**: MIT License
- **Usage**: Free for development, testing, and production
- **Commercial Use**: Allowed with attribution
- **Modification**: Allowed
- **Distribution**: Allowed

### **What You Can Do**
- Use the software for any purpose (commercial or non-commercial)
- Modify and adapt the code
- Distribute copies of the software
- Use the software privately
- Sublicense the software

### **What You Must Do**
- Include the original copyright notice
- Include the MIT license text
- Include a disclaimer of warranty

**📋 [Full License Details](LICENSE)**

---

## 🤝 **Contributing**

We welcome contributions to the project! Please read our **[Contributing Guide](CONTRIBUTING.md)** for detailed information on:

- How to set up your development environment
- Code style and standards
- Security guidelines and best practices
- Pull request process
- Issue reporting guidelines
- Community code of conduct

**📋 [Complete Contributing Guide](CONTRIBUTING.md)**

---

## 🙏 **Acknowledgments**

SMS-to-AI Agent is built on the shoulders of many amazing open source projects. We extend our deepest gratitude to:

### **👨‍💻 Original Developer**
- **[iMeyerKimera](https://github.com/iMeyerKimera)** - Initial creator and architect of SMS-to-AI Agent

### **🏗️ Core Technologies**
- **[Django](https://www.djangoproject.com/)** - The web framework for perfectionists with deadlines
- **[OpenAI](https://openai.com/)** - Advanced AI models and APIs
- **[Twilio](https://www.twilio.com/)** - Communication APIs for SMS and voice
- **[PostgreSQL](https://www.postgresql.org/)** - The world's most advanced open source database
- **[Redis](https://redis.io/)** - Lightning-fast in-memory data store
- **[Docker](https://www.docker.com/)** - Containerization platform

### **🛠️ Development Tools**
- **[Python](https://www.python.org/)** - Programming language that powers it all
- **[Git](https://git-scm.com/)** - Version control and collaboration
- **[Bootstrap](https://getbootstrap.com/)** - Responsive UI framework
- **[Chart.js](https://www.chartjs.org/)** - Beautiful data visualization

### **📚 Community & Documentation**
- **[GitHub](https://github.com/)** - Platform for open source collaboration
- **[Stack Overflow](https://stackoverflow.com/)** - Developer knowledge base
- **[Read the Docs](https://readthedocs.org/)** - Documentation hosting

**🎉 Special thanks to the entire open source community for making this project possible!**

For a complete list of acknowledgments, see our **[Contributing Guide](CONTRIBUTING.md)**.

---

## 📞 **Support**

- **Documentation**: [Complete Documentation](docs/README.md)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

**SMS-to-AI Agent: Where every text message becomes a development opportunity.**

