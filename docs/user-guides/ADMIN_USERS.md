# 👥 Admin User Management Guide

**Complete guide for creating and managing admin dashboard users for SMS-to-AI Agent**

---

## 📋 **Overview**

The SMS-to-AI Agent provides multiple ways to create admin users for the dashboard. This guide covers all methods from the simplest to the most secure and flexible approaches.

---

## 🎯 **Quick Start**

### **Easiest Method: Use the Helper Script**

```bash
# Run the interactive admin creation script
./scripts/create_admin_user.sh
```

This script will guide you through creating an admin user with a simple menu interface.

---

## 🔧 **Method 1: Django Management Commands (Recommended)**

### **Interactive Creation**
```bash
# Create admin user interactively (recommended)
docker-compose exec web python manage.py create_admin
```

This will prompt you for:
- Username
- Email (optional)
- Password (with confirmation)
- User type (staff or superuser)

### **Non-Interactive Creation**
```bash
# Create superuser non-interactively
docker-compose exec web python manage.py create_admin \
    --username admin \
    --email admin@yourdomain.com \
    --password your_secure_password \
    --superuser \
    --no-input
```

### **Create Staff User**
```bash
# Create staff user (dashboard access only)
docker-compose exec web python manage.py create_admin \
    --username dashboard_admin \
    --email dashboard@yourdomain.com \
    --password your_secure_password \
    --no-input
```

---

## 📋 **Method 2: Django's Built-in Superuser Command**

### **Create Superuser**
```bash
# Django's native superuser creation
docker-compose exec web python manage.py createsuperuser
```

This creates a superuser that can:
- Access the admin dashboard
- Access Django's admin interface
- Manage all users and data

---

## 🔑 **Method 3: Environment Variables (Legacy)**

### **Set in .env File**
```bash
# Add to your .env file
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
```

### **Restart Application**
```bash
docker-compose down
docker-compose up -d
```

> **Note**: This method is kept for backward compatibility but Django authentication is recommended.

---

## 📊 **Managing Admin Users**

### **List Existing Admin Users**
```bash
# List all admin users
docker-compose exec web python manage.py list_admins

# List only active admin users
docker-compose exec web python manage.py list_admins --active-only
```

### **Using Django Admin Interface**
1. Access Django admin at: `http://localhost:5001/admin/`
2. Login with superuser credentials
3. Navigate to Users section
4. Create/edit users and set permissions

### **Reset Password**
```bash
# Reset password for existing user
docker-compose exec web python manage.py changepassword username
```

### **Deactivate User**
```python
# In Django shell
docker-compose exec web python manage.py shell

from django.contrib.auth.models import User
user = User.objects.get(username='username')
user.is_active = False
user.save()
```

---

## 🔐 **User Types and Permissions**

### **Superuser**
- Full access to everything
- Can access Django admin interface
- Can manage all users and data
- Can access admin dashboard

### **Staff User**
- Can access admin dashboard
- Can access Django admin interface
- Limited permissions based on groups

### **Environment-based Admin**
- Can access admin dashboard only
- Limited to basic authentication
- No Django admin access

---

## 🛡️ **Security Best Practices**

### **Password Requirements**
- Minimum 8 characters
- Include uppercase, lowercase, numbers
- Include special characters
- Avoid common passwords

### **Secure User Creation**
```bash
# Generate secure random password
SECURE_PASSWORD=$(openssl rand -base64 16)

# Create user with secure password
docker-compose exec web python manage.py create_admin \
    --username secure_admin \
    --email admin@yourdomain.com \
    --password "$SECURE_PASSWORD" \
    --superuser \
    --no-input

echo "Password: $SECURE_PASSWORD"
```

### **Multi-Factor Authentication (Future)**
```python
# Add to requirements.txt for future MFA support
django-otp==1.1.3

# Configure in settings.py
INSTALLED_APPS += [
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
]
```

---

## 🏢 **Production Deployment**

### **Create Production Admin User**
```bash
# Production-ready admin creation
docker-compose exec web python manage.py create_admin \
    --username prod_admin \
    --email admin@yourcompany.com \
    --superuser \
    --no-input

# Set strong password interactively
docker-compose exec web python manage.py changepassword prod_admin
```

### **Remove Default Credentials**
```bash
# Remove or change default environment credentials
# In .env file, change:
ADMIN_USERNAME=disabled
ADMIN_PASSWORD=disabled

# Restart application
docker-compose restart web
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **"User already exists" Error**
```bash
# Check existing users
docker-compose exec web python manage.py list_admins

# Change username or delete existing user
docker-compose exec web python manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.get(username='existing_user').delete()
```

#### **"Permission denied" Error**
```bash
# Ensure user has staff/superuser status
docker-compose exec web python manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='username')
>>> user.is_staff = True
>>> user.is_superuser = True
>>> user.save()
```

#### **Login Not Working**
```bash
# Verify user is active
docker-compose exec web python manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='username')
>>> print(f"Active: {user.is_active}, Staff: {user.is_staff}")
>>> user.is_active = True
>>> user.save()
```

### **Debug Authentication**
```bash
# Check authentication logs
docker-compose logs web | grep -i "login\|auth"

# Test authentication in Django shell
docker-compose exec web python manage.py shell
>>> from django.contrib.auth import authenticate
>>> user = authenticate(username='admin', password='password')
>>> print(f"Authentication result: {user}")
```

---

## 📋 **Quick Reference Commands**

```bash
# Create admin user (interactive)
./scripts/create_admin_user.sh

# Create admin user (command line)
docker-compose exec web python manage.py create_admin

# List admin users
docker-compose exec web python manage.py list_admins

# Create Django superuser
docker-compose exec web python manage.py createsuperuser

# Change password
docker-compose exec web python manage.py changepassword username

# Access Django admin
# http://localhost:5001/admin/

# Access custom dashboard
# http://localhost:5001/dashboard/
```

---

## 🔗 **Related Documentation**

- **[Admin Guide](ADMIN_GUIDE.md)** - Complete admin dashboard guide
- **[User Guide](USER_GUIDE.md)** - User management documentation  
- **[Configuration Guide](../getting-started/CONFIGURATION.md)** - System configuration
- **[Production Guide](../operations/PRODUCTION.md)** - Production deployment

---

## 🎯 **Summary**

### **For Development**
Use the interactive script: `./scripts/create_admin_user.sh`

### **For Production**
Use Django management commands with secure passwords:
```bash
docker-compose exec web python manage.py create_admin --superuser
```

### **For Quick Testing**
Use environment variables in `.env` file.

---

**👥 Your admin users are now ready! You can access the dashboard at `http://localhost:5001/dashboard/`** 