# 🔧 Admin User Management Guide

**Complete guide for adding, managing, and communicating with users through the SMS Agent Admin Dashboard**

---

## 📋 **Table of Contents**

1. [Accessing the Admin Dashboard](#-accessing-the-admin-dashboard)
2. [User Management Overview](#-user-management-overview)
3. [Adding New Users](#-adding-new-users)
4. [Communicating with Users](#-communicating-with-users)
5. [Managing User Tiers](#-managing-user-tiers)
6. [Monitoring User Activity](#-monitoring-user-activity)
7. [User Analytics](#-user-analytics)
8. [Troubleshooting](#-troubleshooting)

---

## 🔐 **Accessing the Admin Dashboard**

### **1. Login to Dashboard**
```
URL: http://localhost:5001/dashboard/
Default Credentials:
- Username: admin
- Password: admin123
```

### **2. Navigate to User Management**
- Click **"Users"** in the main navigation
- URL: `http://localhost:5001/dashboard/users/`

---

## 👥 **User Management Overview**

### **Dashboard Features**
The User Management section provides:

- **📊 User Statistics**: Total, active, premium, and enterprise users
- **🔍 Search & Filtering**: Find users by phone number, tier, or activity
- **📱 Individual Messaging**: Send SMS to specific users
- **📢 Broadcast Messaging**: Send SMS to all users or by tier
- **⭐ Tier Management**: Upgrade/downgrade user tiers
- **📈 Activity Monitoring**: Track user engagement and usage

### **User Information Display**
For each user, you can see:
- **Phone Number**: Primary identifier
- **User Tier**: Free, Premium, or Enterprise
- **Activity Status**: Active, Recent, or Inactive
- **Usage Statistics**: Total requests, monthly requests
- **Performance Metrics**: Success rate, average response time
- **Last Activity**: When they last used the system

---

## ➕ **Adding New Users**

### **Method 1: Automatic Registration (Recommended)**
Users are automatically added when they send their first SMS:

1. **User sends SMS** to your Twilio number
2. **System automatically creates** user record
3. **Default tier assigned**: Free tier
4. **User appears** in admin dashboard immediately

### **Method 2: Manual Registration via API**
```bash
# Create user via API
curl -X POST http://localhost:5001/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "tier": "free",
    "email": "user@example.com",
    "full_name": "John Doe"
  }'
```

### **Method 3: Django Admin Interface**
```
1. Go to: http://localhost:5001/admin/
2. Login with Django superuser credentials
3. Navigate to: Core > Users
4. Click "Add User"
5. Fill in required fields:
   - Phone Number: +1234567890
   - Tier: free/premium/enterprise
   - Email (optional)
   - Full Name (optional)
```

### **User Creation Checklist**
- [ ] Valid phone number format (+1234567890)
- [ ] Appropriate tier assigned (free, premium, enterprise)
- [ ] Rate limits configured automatically
- [ ] User appears in dashboard within 1 minute

---

## 📱 **Communicating with Users**

### **🎯 Individual User Messaging**

#### **Send Message to Specific User**
1. **Navigate** to User Management (`/dashboard/users/`)
2. **Find the user** using search or scroll
3. **Click the envelope icon** (📧) in the Actions column
4. **Enter your message** (max 320 characters)
5. **Click "Send Message"**

#### **Message Examples**
```
✅ Welcome to SMS Agent! Send "HELP" for commands.

✅ Your tier has been upgraded to Premium. Enjoy 50 SMS/hour!

✅ System maintenance scheduled for 2 AM EST tonight.

✅ New features available! Try asking for "React components".
```

### **📢 Broadcast Messaging**

#### **Send Message to All Users**
1. **Click "Broadcast Message"** button (top right)
2. **Enter your message** (max 320 characters)
3. **Check "Send to all users"** if desired
4. **Click "Send Message"**

#### **Send Message by Tier**
1. **Use tier filter** to select specific tier (Free/Premium/Enterprise)
2. **Click "Broadcast Message"**
3. **Message will be sent** to all users in that tier

#### **Broadcast Examples**
```
🎉 New AI models available! Better coding assistance now live.

🔧 Scheduled maintenance tonight 1-3 AM EST. Service may be interrupted.

⭐ Upgrade to Premium for 5x more requests per hour! Reply UPGRADE.

📊 Check out your usage stats in our new analytics dashboard!
```

### **📧 Message Features**
- **Character Counter**: Shows remaining characters (320 max)
- **Delivery Confirmation**: Success/failure notifications
- **Rate Limiting**: Respects system rate limits
- **Logging**: All messages logged for audit trail

---

## ⭐ **Managing User Tiers**

### **Available Tiers**

| **Tier** | **SMS/Hour** | **AI Tokens** | **Priority** | **Features** |
|----------|--------------|---------------|--------------|--------------|
| 🆓 **Free** | 10 | 1,000 | Standard | Basic task routing |
| ⭐ **Premium** | 50 | 4,000 | High | Enhanced routing, priority support |
| 🏢 **Enterprise** | Unlimited | 8,000 | Highest | Custom configs, white-label |

### **Upgrade/Downgrade User Tier**

#### **Via Admin Dashboard**
1. **Find the user** in User Management
2. **Click the crown icon** (👑) in Actions column
3. **Select new tier** from dropdown
4. **Click "Update Tier"**
5. **User receives SMS notification** about tier change

#### **Via API**
```bash
curl -X POST http://localhost:5001/dashboard/api/users/tier \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "tier": "premium"
  }'
```

### **Tier Change Notifications**
Users automatically receive SMS when tier changes:
```
🆓→⭐ "Congratulations! Upgraded to Premium. Now 50 SMS/hour!"
⭐→🏢 "Welcome to Enterprise! Unlimited SMS + priority support."
🏢→⭐ "Tier changed to Premium. 50 SMS/hour limit now active."
```

---

## 📊 **Monitoring User Activity**

### **Activity Indicators**
- **🟢 Active**: Used within last hour
- **🟡 Recent**: Used within last 24 hours  
- **🔴 Inactive**: No activity for 24+ hours

### **User Statistics Tracking**
- **Total Requests**: Lifetime SMS count
- **Monthly Requests**: Current month usage
- **Success Rate**: Percentage of successful task completions
- **Average Response Time**: Mean processing time for their tasks
- **Recent Tasks**: Last 7 days activity count

### **Filtering Users**
```
🔍 Search: Filter by phone number
🎯 Tier Filter: Free, Premium, Enterprise
📅 Activity Filter: Active (24h), Recent (7d), Inactive (30d+)
```

### **User Details View**
Click the eye icon (👁️) to see:
- **Complete user profile**
- **Task statistics by category**
- **Recent task history** (last 10 tasks)
- **Performance metrics**
- **Usage patterns**

---

## 📈 **User Analytics**

### **Accessing Analytics**
1. **Navigate to Analytics** (`/dashboard/analytics/`)
2. **View comprehensive user metrics**
3. **Export data** as CSV or JSON

### **Key Metrics Available**

#### **👥 User Growth**
- New user registrations over time
- User retention rates
- Tier distribution changes
- Geographic user distribution

#### **📱 Usage Patterns**
- Peak usage hours
- Popular task categories by user tier
- Average session lengths
- Response time trends

#### **💰 Tier Analysis**
- Revenue potential by tier
- Upgrade/downgrade patterns
- Feature usage by tier
- Customer lifetime value

### **Export User Data**
```bash
# Export user analytics
curl "http://localhost:5001/dashboard/api/analytics/export?start_date=2024-01-01&end_date=2024-12-31" \
  -o user_analytics.csv
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **❌ User Not Appearing in Dashboard**
**Problem**: User sent SMS but not visible in admin
**Solutions**:
1. Check if SMS was received in Twilio logs
2. Verify webhook URL is correct
3. Check application logs for errors
4. Refresh browser (Ctrl+F5)

#### **📱 Message Delivery Failures**
**Problem**: Broadcast or individual messages not delivering
**Solutions**:
1. Verify Twilio credentials are correct
2. Check recipient phone number format (+1234567890)
3. Ensure Twilio account has sufficient credits
4. Check rate limiting hasn't blocked messages

#### **⭐ Tier Updates Not Applied**
**Problem**: User tier change doesn't take effect
**Solutions**:
1. Refresh user management page
2. Check application logs for database errors
3. Verify user phone number is correct
4. Try updating via Django admin interface

#### **📊 Missing User Statistics**
**Problem**: User stats showing as 0 or missing
**Solutions**:
1. Check if user has actually sent messages
2. Verify database connections
3. Run analytics refresh
4. Check for data migration issues

### **Debug Commands**
```bash
# Check application logs
docker-compose logs web --tail=50

# Check database connection
docker-compose exec web python manage.py dbshell

# Verify user exists in database
docker-compose exec database psql -U sms_agent -d sms_agent_db -c "SELECT * FROM users WHERE phone_number='+1234567890';"

# Check Twilio webhook logs
curl https://api.twilio.com/2010-04-01/Accounts/{SID}/Messages.json \
  -u {SID}:{AUTH_TOKEN}
```

### **Emergency Procedures**

#### **🚨 Block Problem User**
```bash
# Temporarily block user via API
curl -X POST http://localhost:5001/dashboard/api/users/tier \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+1234567890",
    "tier": "blocked"
  }'
```

#### **📢 Emergency Broadcast**
```bash
# Send emergency notification
curl -X POST http://localhost:5001/dashboard/api/users/broadcast \
  -H "Content-Type: application/json" \
  -d '{
    "message": "URGENT: Service maintenance in progress. Responses may be delayed."
  }'
```

---

## 🎯 **Best Practices**

### **👥 User Management**
- ✅ **Monitor daily**: Check new user registrations
- ✅ **Review tiers weekly**: Identify upgrade candidates
- ✅ **Respond quickly**: Address user issues promptly
- ✅ **Track patterns**: Monitor usage trends
- ✅ **Backup data**: Regular user data exports

### **📱 Communication**
- ✅ **Be concise**: SMS has 160-320 character limits
- ✅ **Be helpful**: Provide actionable information
- ✅ **Be timely**: Send notifications promptly
- ✅ **Respect privacy**: Don't over-communicate
- ✅ **Test messages**: Verify before broadcasting

### **📊 Analytics**
- ✅ **Daily monitoring**: Check key metrics daily
- ✅ **Weekly reports**: Generate usage summaries
- ✅ **Monthly analysis**: Deep dive into trends
- ✅ **Quarterly reviews**: Strategic user growth planning
- ✅ **Data retention**: Keep historical data for analysis

---

## 🚀 **Quick Reference**

### **Common Admin Tasks**
```
View all users:           /dashboard/users/
Send individual message:  Click 📧 icon → Enter message → Send
Send broadcast:           Click "Broadcast Message" → Enter message → Send
Upgrade user tier:        Click 👑 icon → Select tier → Update
View user details:        Click 👁️ icon → Review profile → Close
Export analytics:         /dashboard/analytics/ → Export CSV
Check system health:      /dashboard/system/
```

### **Emergency Contacts**
- **System Admin**: Check system logs first
- **Twilio Support**: For SMS delivery issues
- **Database Admin**: For data integrity issues

---

**🎉 You're now ready to effectively manage users and communications through the SMS Agent Admin Dashboard!**

**Need help? Check the system logs, review this guide, or contact your technical team.** 