# 🌐 Ngrok Permanent Domain Setup Guide

## Why Use a Permanent Domain?

By default, ngrok generates a new random URL each time you restart your application (e.g., `https://abc123.ngrok-free.app`). A permanent domain gives you:

- ✅ **Consistent webhook URL** - no need to update Twilio every restart
- ✅ **Reliable SMS service** - users can always reach your bot
- ✅ **Professional appearance** - custom branded domains
- ✅ **Easier testing** - bookmark and reuse the same URL

---

## 📋 **Step-by-Step Setup**

### **1. Get Your Free Permanent Domain**

1. **Visit ngrok Dashboard**: Go to [https://dashboard.ngrok.com/domains](https://dashboard.ngrok.com/domains)
2. **Login/Register**: Sign up for a free ngrok account if you don't have one
3. **Create Domain**: Click "Create Domain" or "New Domain"
4. **Choose Name**: Select a memorable name (e.g., `mybot-ai-assistant`)
5. **Get Full Domain**: You'll receive something like `mybot-ai-assistant.ngrok-free.app`

### **2. Configure Your Environment**

Edit your `.env` file and set the permanent domain:

```bash
# Replace with your actual reserved domain
NGROK_DOMAIN=mybot-ai-assistant.ngrok-free.app
```

### **3. Restart Your Application**

```bash
# Stop current containers
docker-compose down

# Start with permanent domain
docker-compose up -d

# Verify the domain is working
curl https://mybot-ai-assistant.ngrok-free.app/health
```

### **4. Update Twilio Webhook URL**

1. **Go to Twilio Console**: [https://console.twilio.com/](https://console.twilio.com/)
2. **Navigate to Phone Numbers**: Phone Numbers → Manage → Active numbers
3. **Select Your Number**: Click on your SMS-enabled phone number
4. **Update Webhook URL**: Set to `https://mybot-ai-assistant.ngrok-free.app/sms`
5. **Set Method**: Ensure HTTP method is set to **POST**
6. **Save Configuration**: Click Save

---

## 🔧 **Configuration Examples**

### **Free Tier Domain Examples:**
```bash
# Your reserved domains might look like:
NGROK_DOMAIN=sms-ai-bot-123.ngrok-free.app
NGROK_DOMAIN=my-cursor-agent.ngrok-free.app  
NGROK_DOMAIN=dev-sms-assistant.ngrok-free.app
```

### **Paid Tier Custom Domains (Optional):**
```bash
# With paid ngrok plans, you can use custom domains:
NGROK_DOMAIN=sms.mycompany.com
NGROK_DOMAIN=ai-assistant.mydomain.io
```

---

## ✅ **Verification Checklist**

After setup, verify everything is working:

- [ ] **Domain resolves**: `curl https://your-domain.ngrok-free.app/health`
- [ ] **Ngrok shows permanent URL**: Check container logs for your custom domain
- [ ] **Twilio webhook updated**: SMS messages should reach your bot
- [ ] **Admin dashboard accessible**: `https://your-domain.ngrok-free.app/admin/`
- [ ] **SMS test successful**: Send a test SMS to verify end-to-end functionality

---

## 🚨 **Troubleshooting**

### **Domain Not Working**
```bash
# Check if domain is correctly set in environment
docker-compose exec web printenv | grep NGROK

# Verify ngrok container logs
docker-compose logs ngrok

# Test domain resolution
nslookup your-domain.ngrok-free.app
```

### **Ngrok Container Failing**
```bash
# Check for auth token issues
docker-compose logs ngrok | grep -i error

# Verify auth token is set
docker-compose exec ngrok printenv | grep NGROK_AUTHTOKEN

# Restart ngrok container specifically
docker-compose restart ngrok
```

### **Twilio Not Reaching Your Bot**
1. **Check webhook URL**: Ensure it ends with `/sms`
2. **Verify HTTP method**: Must be POST, not GET
3. **Test manually**: `curl -X POST https://your-domain.ngrok-free.app/sms`
4. **Check ngrok inspector**: Visit `http://localhost:4040` to see incoming requests

---

## 🎯 **Pro Tips**

### **Domain Naming Best Practices:**
- Use descriptive names: `sms-ai-assistant` vs `app123`
- Include purpose: `debug-bot`, `code-helper`, `ai-agent`
- Keep it short: Easier to remember and type
- Avoid special characters: Stick to letters, numbers, and hyphens

### **Multiple Environments:**
```bash
# Development
NGROK_DOMAIN=dev-sms-bot.ngrok-free.app

# Staging  
NGROK_DOMAIN=staging-sms-bot.ngrok-free.app

# Production
NGROK_DOMAIN=prod-sms-bot.ngrok-free.app
```

### **Team Collaboration:**
- Share the permanent domain with your team
- Document the domain in your project README
- Use the same domain across deployments for consistency

---

## 📞 **Need Help?**

- **Ngrok Documentation**: [https://ngrok.com/docs](https://ngrok.com/docs)
- **Ngrok Dashboard**: [https://dashboard.ngrok.com/](https://dashboard.ngrok.com/)
- **Test Your Setup**: SMS "HELP" to your bot after configuration

**Your permanent domain is now configured! Your SMS-to-AI Agent will always be accessible at the same URL. 🎉** 