# 🔐 Dashboard Login Guide

## ✅ **CSRF Token Issue - FIXED**

The CSRF token missing error has been resolved. The login form now includes proper Django CSRF protection.

---

## 🎯 **Accessing the Admin Dashboard**

### **Two Admin Interfaces Available**

#### 1. **Custom Admin Dashboard** (Main Interface)
- **URL**: `http://localhost:5001/dashboard/`
- **Purpose**: Custom SMS AI Agent management interface
- **Credentials**: Use `.env` file settings
- **Features**: SMS analytics, user management, system monitoring

#### 2. **Django Admin** (Built-in)
- **URL**: `http://localhost:5001/admin/`
- **Purpose**: Django's built-in admin interface
- **Credentials**: Requires Django superuser
- **Features**: Database record management, user administration

---

## 🔑 **Login Credentials**

### **Custom Dashboard Login**
```bash
# Check your .env file for these values:
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_admin_password
```

### **Django Admin Login**
```bash
# Create a Django superuser first:
docker-compose exec web python manage.py createsuperuser
```

---

## 📝 **Step-by-Step Login Process**

### **Custom Dashboard Access**

1. **Navigate to Login Page**
   ```
   http://localhost:5001/dashboard/
   ```

2. **Enter Credentials**
   - Username: Value from `ADMIN_USERNAME` in `.env`
   - Password: Value from `ADMIN_PASSWORD` in `.env`

3. **Submit Form**
   - Form now includes CSRF token automatically
   - Should redirect to: `http://localhost:5001/dashboard/dashboard/`

4. **Access Features**
   - User Management: `/dashboard/users/`
   - Analytics: `/dashboard/analytics/`
   - System Monitoring: `/dashboard/system/`

### **Django Admin Access**

1. **Create Superuser** (One-time setup)
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

2. **Navigate to Django Admin**
   ```
   http://localhost:5001/admin/
   ```

3. **Login with Superuser Credentials**

---

## 🛠️ **Troubleshooting Login Issues**

### **Problem 1: CSRF Token Missing**
```
WARNING Forbidden (CSRF token missing.): /dashboard/login/
```

**Status**: ✅ **FIXED**
- Login template now includes `{% csrf_token %}`
- Form submission works properly

### **Problem 2: Wrong URL**
```
Page not found (404)
```

**Common Mistakes**:
- ❌ `/admin/login/` (This is Django admin, different system)
- ❌ `/dashboard/login/` (Not the root URL)
- ✅ `/dashboard/` (Correct custom dashboard URL)

### **Problem 3: Invalid Credentials**
```
Error: Invalid credentials
```

**Check**:
```bash
# Verify credentials in .env file
grep "ADMIN_" .env

# Should show:
# ADMIN_USERNAME=admin
# ADMIN_PASSWORD=your_secure_admin_password
```

### **Problem 4: Service Not Running**
```
Connection refused
```

**Fix**:
```bash
# Check if services are running
docker-compose ps

# Start services if needed
docker-compose up -d

# Check logs
docker-compose logs web
```

---

## 🔍 **Debug Commands**

### **Check Login Logs**
```bash
# View authentication logs
docker-compose logs web | grep -i login

# View Django logs
tail -f logs/django.log | grep -i auth
```

### **Test Login Endpoint**
```bash
# Test with curl (replace with your credentials)
curl -c cookies.txt -b cookies.txt \
  -X POST http://localhost:5001/dashboard/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=your_password&csrfmiddlewaretoken=DUMMY"
```

### **Check Session Storage**
```bash
# Check Redis for session data
docker-compose exec redis redis-cli keys "*"
```

---

## 📊 **Dashboard Features Overview**

### **Custom Dashboard** (`/dashboard/`)
- **Real-time Metrics**: System overview, user stats, task performance
- **User Management**: View users, manage tiers, monitor activity
- **Analytics**: Detailed reporting, trends, performance metrics
- **System Health**: Database status, error tracking, configuration

### **Django Admin** (`/admin/`)
- **User Records**: Direct database user management
- **Task Records**: View all SMS tasks and responses
- **Error Logs**: System error tracking and resolution
- **System Management**: Django-level administration

---

## ✅ **Success Indicators**

When login is working correctly:

1. **Page Loads**
   ```bash
   curl -I http://localhost:5001/dashboard/
   # HTTP/1.1 200 OK
   ```

2. **Form Submission Works**
   - No CSRF errors in logs
   - Successful redirect to dashboard

3. **Session Created**
   ```bash
   # Check for session cookies
   curl -c cookies.txt http://localhost:5001/dashboard/
   grep sessionid cookies.txt
   ```

4. **Dashboard Accessible**
   - Can access `/dashboard/dashboard/`
   - Menu items load properly
   - Data displays correctly

---

## 🚀 **Quick Fix Summary**

The main login issue was the missing CSRF token. This has been fixed by:

1. ✅ **Added CSRF token to login form**
   ```html
   <form method="POST">
       {% csrf_token %}
       <!-- form fields -->
   </form>
   ```

2. ✅ **Updated view with CSRF protection**
   ```python
   @csrf_protect
   def admin_login(request):
       # login logic
   ```

3. ✅ **Fixed URL routing**
   - Dashboard login: `/dashboard/`
   - Dashboard home: `/dashboard/dashboard/`

4. ✅ **Added proper logging**
   - Login attempts logged
   - Failed attempts tracked
   - Debugging information available

Your admin dashboard should now work perfectly! 🎉

---

## 📞 **Need More Help?**

Check the comprehensive troubleshooting guide: `DJANGO_TROUBLESHOOTING.md`

**Quick Test URLs**:
- Health: `http://localhost:5001/health`
- Dashboard: `http://localhost:5001/dashboard/`
- Django Admin: `http://localhost:5001/admin/`
- API: `http://localhost:5001/api/` 