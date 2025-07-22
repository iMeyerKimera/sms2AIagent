# 🔌 API Reference

**Complete REST API documentation for SMS-to-AI Agent**

---

## 📋 **Overview**

The SMS-to-AI Agent provides a comprehensive REST API built with Django REST Framework. This API allows you to manage users, tasks, analytics, and system operations programmatically.

### **Base URL**
- **Development**: `http://localhost:5001/api/`
- **Production**: `https://yourdomain.com/api/`

### **Authentication**
- **Session Authentication**: For web dashboard
- **Token Authentication**: For API clients
- **Admin Authentication**: For administrative endpoints

---

## 🔐 **Authentication**

### **Obtain API Token**

```http
POST /api/auth/token/
Content-Type: application/json

{
  "username": "admin",
  "password": "your_password"
}
```

**Response:**
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user_id": 1,
  "username": "admin"
}
```

### **Using the Token**

Include the token in all API requests:
```http
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

---

## 👥 **User Management**

### **List Users**

```http
GET /api/users/
Authorization: Token your_token_here
```

**Response:**
```json
{
  "count": 25,
  "next": "http://localhost:5001/api/users/?page=2",
  "previous": null,
  "results": [
    {
      "phone_number": "+1234567890",
      "tier": "premium",
      "email": "user@example.com",
      "full_name": "John Doe",
      "created_at": "2024-01-15T10:30:00Z",
      "last_active": "2024-01-20T14:25:00Z",
      "total_requests": 45,
      "monthly_requests": 12,
      "timezone": "UTC",
      "preferences": {
        "notifications": true,
        "language": "en"
      }
    }
  ]
}
```

### **Get User Details**

```http
GET /api/users/{phone_number}/
Authorization: Token your_token_here
```

**Example:**
```http
GET /api/users/+1234567890/
```

**Response:**
```json
{
  "phone_number": "+1234567890",
  "tier": "premium",
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2024-01-15T10:30:00Z",
  "last_active": "2024-01-20T14:25:00Z",
  "total_requests": 45,
  "monthly_requests": 12,
  "rate_limit_reset": "2024-01-20T15:00:00Z",
  "timezone": "UTC",
  "preferences": {
    "notifications": true,
    "language": "en"
  },
  "stats": {
    "success_rate": 95.6,
    "avg_response_time": 2.3,
    "favorite_categories": ["coding", "debug"]
  }
}
```

### **Create User**

```http
POST /api/users/
Authorization: Token your_token_here
Content-Type: application/json

{
  "phone_number": "+1987654321",
  "tier": "free",
  "email": "newuser@example.com",
  "full_name": "Jane Smith",
  "timezone": "America/New_York",
  "preferences": {
    "notifications": true,
    "language": "en"
  }
}
```

**Response:**
```json
{
  "phone_number": "+1987654321",
  "tier": "free",
  "email": "newuser@example.com",
  "full_name": "Jane Smith",
  "created_at": "2024-01-20T16:30:00Z",
  "last_active": "2024-01-20T16:30:00Z",
  "total_requests": 0,
  "monthly_requests": 0,
  "timezone": "America/New_York"
}
```

### **Update User**

```http
PATCH /api/users/{phone_number}/
Authorization: Token your_token_here
Content-Type: application/json

{
  "tier": "premium",
  "email": "updated@example.com",
  "preferences": {
    "notifications": false,
    "language": "es"
  }
}
```

### **Update User Tier**

```http
POST /api/users/{phone_number}/update_tier/
Authorization: Token your_token_here
Content-Type: application/json

{
  "tier": "enterprise",
  "reason": "Upgrade for increased usage"
}
```

### **Send Message to User**

```http
POST /api/users/{phone_number}/send_message/
Authorization: Token your_token_here
Content-Type: application/json

{
  "message": "Welcome to premium tier! You now have access to enhanced features.",
  "message_type": "notification"
}
```

---

## 📋 **Task Management**

### **List Tasks**

```http
GET /api/tasks/
Authorization: Token your_token_here
```

**Query Parameters:**
- `user_phone`: Filter by user phone number
- `category`: Filter by task category
- `success`: Filter by success status (true/false)
- `created_after`: Filter tasks created after date (ISO format)
- `created_before`: Filter tasks created before date (ISO format)
- `page`: Page number for pagination
- `page_size`: Number of results per page (default: 20)

**Example:**
```http
GET /api/tasks/?user_phone=+1234567890&category=coding&page=1&page_size=10
```

**Response:**
```json
{
  "count": 150,
  "next": "http://localhost:5001/api/tasks/?page=2",
  "previous": null,
  "results": [
    {
      "id": 123,
      "user_phone": "+1234567890",
      "sms_content": "Help me debug this Python function",
      "ai_response": "I'd be happy to help you debug your Python function...",
      "category": "debug",
      "processing_time": 2.45,
      "tokens_used": 450,
      "complexity_score": 0.7,
      "success": true,
      "error_message": null,
      "created_at": "2024-01-20T14:25:00Z",
      "completed_at": "2024-01-20T14:25:02Z",
      "metadata": {
        "language": "python",
        "confidence": 0.95
      }
    }
  ]
}
```

### **Get Task Details**

```http
GET /api/tasks/{task_id}/
Authorization: Token your_token_here
```

**Response:**
```json
{
  "id": 123,
  "user_phone": "+1234567890",
  "sms_content": "Help me debug this Python function:\n\ndef calculate_sum(numbers):\n    total = 0\n    for i in numbers:\n        total += i\n    return total",
  "ai_response": "Your function looks correct! This function will calculate the sum of all numbers in the input list. Here's how it works:\n\n1. Initialize total to 0\n2. Iterate through each number in the list\n3. Add each number to the total\n4. Return the final sum\n\nThe function should work as expected. If you're experiencing issues, could you share the specific error or unexpected behavior?",
  "category": "debug",
  "processing_time": 2.45,
  "tokens_used": 450,
  "complexity_score": 0.7,
  "success": true,
  "error_message": null,
  "created_at": "2024-01-20T14:25:00Z",
  "completed_at": "2024-01-20T14:25:02Z",
  "metadata": {
    "language": "python",
    "confidence": 0.95,
    "prompt_template": "debug_code",
    "model_used": "gpt-4"
  }
}
```

### **Create Task (Manual)**

```http
POST /api/tasks/
Authorization: Token your_token_here
Content-Type: application/json

{
  "user_phone": "+1234567890",
  "sms_content": "Create a Python function to sort a list",
  "category": "coding"
}
```

### **Get Task Analytics**

```http
GET /api/tasks/analytics/
Authorization: Token your_token_here
```

**Query Parameters:**
- `start_date`: Start date for analytics (ISO format)
- `end_date`: End date for analytics (ISO format)
- `user_phone`: Filter by specific user
- `category`: Filter by task category

**Response:**
```json
{
  "total_tasks": 1250,
  "successful_tasks": 1187,
  "success_rate": 94.96,
  "avg_processing_time": 2.34,
  "avg_tokens_used": 523,
  "category_breakdown": {
    "coding": {
      "count": 450,
      "success_rate": 96.2,
      "avg_processing_time": 2.8
    },
    "debug": {
      "count": 380,
      "success_rate": 94.7,
      "avg_processing_time": 2.1
    },
    "general": {
      "count": 420,
      "success_rate": 93.8,
      "avg_processing_time": 1.9
    }
  },
  "daily_stats": [
    {
      "date": "2024-01-20",
      "total_tasks": 45,
      "successful_tasks": 43,
      "avg_processing_time": 2.2
    }
  ]
}
```

---

## 📊 **Analytics Endpoints**

### **System Overview**

```http
GET /api/analytics/overview/
Authorization: Token your_token_here
```

**Response:**
```json
{
  "total_users": 1250,
  "active_users_24h": 89,
  "active_users_7d": 456,
  "total_tasks": 15678,
  "tasks_24h": 234,
  "success_rate": 94.6,
  "avg_response_time": 2.3,
  "tier_distribution": {
    "free": 890,
    "premium": 320,
    "enterprise": 40
  },
  "top_categories": [
    {"category": "coding", "count": 5678},
    {"category": "debug", "count": 4567},
    {"category": "general", "count": 3456}
  ]
}
```

### **User Analytics**

```http
GET /api/analytics/users/
Authorization: Token your_token_here
```

**Query Parameters:**
- `tier`: Filter by user tier
- `start_date`: Start date for analysis
- `end_date`: End date for analysis

**Response:**
```json
{
  "total_users": 1250,
  "new_users_period": 45,
  "active_users_period": 678,
  "retention_rate": 87.3,
  "tier_upgrades": 12,
  "tier_downgrades": 3,
  "geographic_distribution": {
    "US": 789,
    "CA": 234,
    "UK": 123,
    "Other": 104
  },
  "usage_patterns": {
    "avg_requests_per_user": 12.4,
    "most_active_hours": [14, 15, 16, 20, 21],
    "peak_day": "Wednesday"
  }
}
```

### **Performance Analytics**

```http
GET /api/analytics/performance/
Authorization: Token your_token_here
```

**Response:**
```json
{
  "response_times": {
    "avg": 2.34,
    "p50": 1.89,
    "p95": 4.56,
    "p99": 8.23
  },
  "error_rates": {
    "total_errors": 156,
    "error_rate": 1.2,
    "common_errors": [
      {"type": "openai_timeout", "count": 45},
      {"type": "database_connection", "count": 23},
      {"type": "invalid_phone", "count": 18}
    ]
  },
  "resource_usage": {
    "cpu_avg": 23.4,
    "memory_avg": 67.8,
    "database_connections": 12
  }
}
```

---

## 🔔 **Messaging Endpoints**

### **Send Broadcast Message**

```http
POST /api/messaging/broadcast/
Authorization: Token your_token_here
Content-Type: application/json

{
  "message": "System maintenance scheduled for tonight at 2 AM EST.",
  "tier_filter": ["premium", "enterprise"],
  "message_type": "announcement"
}
```

**Response:**
```json
{
  "message_id": "broadcast_20240120_001",
  "recipients_count": 360,
  "estimated_delivery": "2024-01-20T16:45:00Z",
  "status": "queued"
}
```

### **Get Message Status**

```http
GET /api/messaging/status/{message_id}/
Authorization: Token your_token_here
```

**Response:**
```json
{
  "message_id": "broadcast_20240120_001",
  "status": "completed",
  "sent_count": 358,
  "failed_count": 2,
  "delivery_rate": 99.4,
  "created_at": "2024-01-20T16:35:00Z",
  "completed_at": "2024-01-20T16:47:00Z"
}
```

---

## 🚨 **Error Logs**

### **List Error Logs**

```http
GET /api/error-logs/
Authorization: Token your_token_here
```

**Query Parameters:**
- `error_type`: Filter by error type
- `resolved`: Filter by resolution status (true/false)
- `user_phone`: Filter by user
- `start_date`: Start date filter
- `end_date`: End date filter

**Response:**
```json
{
  "count": 156,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 789,
      "user_phone": "+1234567890",
      "task_id": 123,
      "error_type": "openai_timeout",
      "error_message": "OpenAI API request timed out after 60 seconds",
      "stack_trace": "Traceback (most recent call last):\n  File...",
      "timestamp": "2024-01-20T14:25:00Z",
      "resolved": false,
      "metadata": {
        "request_id": "req_abc123",
        "model": "gpt-4",
        "timeout": 60
      }
    }
  ]
}
```

### **Mark Error as Resolved**

```http
PATCH /api/error-logs/{error_id}/
Authorization: Token your_token_here
Content-Type: application/json

{
  "resolved": true,
  "resolution_notes": "Fixed by updating OpenAI timeout configuration"
}
```

---

## ⚙️ **System Management**

### **Health Check**

```http
GET /api/health/
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T16:30:00Z",
  "services": {
    "database": {
      "status": "healthy",
      "response_time": 0.023,
      "connections": 8
    },
    "redis": {
      "status": "healthy",
      "response_time": 0.001,
      "memory_usage": "45MB"
    },
    "openai": {
      "status": "healthy",
      "response_time": 1.234,
      "rate_limit_remaining": 4500
    },
    "twilio": {
      "status": "healthy",
      "response_time": 0.456,
      "account_balance": "$45.67"
    }
  },
  "version": "1.0.0",
  "uptime": 86400
}
```

### **System Statistics**

```http
GET /api/system/stats/
Authorization: Token your_token_here
```

**Response:**
```json
{
  "system": {
    "cpu_usage": 23.4,
    "memory_usage": 67.8,
    "disk_usage": 45.2,
    "uptime": 86400
  },
  "database": {
    "total_size": "2.3GB",
    "connections": 12,
    "slow_queries": 3,
    "cache_hit_ratio": 94.6
  },
  "queues": {
    "pending_tasks": 5,
    "failed_tasks": 2,
    "completed_today": 234
  }
}
```

---

## 📥 **Webhook Endpoints**

### **SMS Webhook (Twilio)**

```http
POST /api/sms/receive/
Content-Type: application/x-www-form-urlencoded

From=+1234567890&
To=+1987654321&
Body=Help me debug this Python code&
MessageSid=SM1234567890abcdef&
AccountSid=AC1234567890abcdef
```

**Response:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Thank you for your message! I'm processing your request and will respond shortly.</Message>
</Response>
```

---

## 🔧 **Rate Limiting**

### **Rate Limit Headers**

All API responses include rate limiting headers:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642694400
```

### **Rate Limit Exceeded Response**

```json
{
  "error": "Rate limit exceeded",
  "detail": "You have exceeded the rate limit of 1000 requests per hour",
  "retry_after": 3600
}
```

---

## ❌ **Error Responses**

### **Standard Error Format**

```json
{
  "error": "validation_error",
  "detail": "The provided data is invalid",
  "fields": {
    "phone_number": ["This field is required"],
    "tier": ["Must be one of: free, premium, enterprise"]
  },
  "timestamp": "2024-01-20T16:30:00Z",
  "request_id": "req_abc123"
}
```

### **HTTP Status Codes**

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error

---

## 📚 **Code Examples**

### **Python Client Example**

```python
import requests

class SMSAgentAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {'Authorization': f'Token {token}'}
    
    def get_users(self, page=1, tier=None):
        params = {'page': page}
        if tier:
            params['tier'] = tier
        
        response = requests.get(
            f'{self.base_url}/users/',
            headers=self.headers,
            params=params
        )
        return response.json()
    
    def send_message(self, phone_number, message):
        data = {'message': message}
        response = requests.post(
            f'{self.base_url}/users/{phone_number}/send_message/',
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def get_analytics(self, start_date=None, end_date=None):
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        response = requests.get(
            f'{self.base_url}/analytics/overview/',
            headers=self.headers,
            params=params
        )
        return response.json()

# Usage
api = SMSAgentAPI('http://localhost:5001/api', 'your_token_here')
users = api.get_users(tier='premium')
analytics = api.get_analytics()
```

### **JavaScript Client Example**

```javascript
class SMSAgentAPI {
    constructor(baseUrl, token) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json'
        };
    }
    
    async getUsers(page = 1, tier = null) {
        const params = new URLSearchParams({ page });
        if (tier) params.append('tier', tier);
        
        const response = await fetch(`${this.baseUrl}/users/?${params}`, {
            headers: this.headers
        });
        return response.json();
    }
    
    async sendMessage(phoneNumber, message) {
        const response = await fetch(`${this.baseUrl}/users/${phoneNumber}/send_message/`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({ message })
        });
        return response.json();
    }
    
    async getAnalytics(startDate = null, endDate = null) {
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        const response = await fetch(`${this.baseUrl}/analytics/overview/?${params}`, {
            headers: this.headers
        });
        return response.json();
    }
}

// Usage
const api = new SMSAgentAPI('http://localhost:5001/api', 'your_token_here');
const users = await api.getUsers(1, 'premium');
const analytics = await api.getAnalytics();
```

---

## 🔗 **Related Documentation**

- **[User Guide](USER_GUIDE.md)** - Learn how to use the system
- **[Admin Guide](ADMIN_GUIDE.md)** - Administrative functions
- **[Installation Guide](../getting-started/INSTALLATION.md)** - Set up the system
- **[Troubleshooting](../operations/TROUBLESHOOTING.md)** - Common issues

---

**🔌 Your API is ready for integration! Use these endpoints to build powerful applications on top of SMS-to-AI Agent.** 