# 📱 SMS-to-Cursor AI Agent - User Guide

**Turn your phone into a powerful AI development assistant!** Send SMS messages to get instant help with coding, debugging, design, and more - all powered by advanced AI and intelligent task routing.

---

## 🚀 **Quick Start**

### How to Use:
1. **Send an SMS** to your configured phone number
2. **Describe your task** in natural language
3. **Receive an intelligent response** optimized for your request type
4. **Get SMS-friendly summaries** of complex solutions

### Example Messages:
```
"Create a Python function to calculate fibonacci numbers"
"Debug this JavaScript error: Cannot read property of undefined"
"Design a login page layout for my web app"
"Explain how OAuth 2.0 works"
```

---

## 🧠 **Intelligent Task Routing & Categorization**

Your SMS-to-AI Agent automatically analyzes every message and routes it to the most appropriate AI model and configuration. This ensures you get the best possible response for your specific type of request.

### **How Task Routing Works**

#### 🔍 **1. Automatic Analysis**
When you send a message, the system:
- **Analyzes your text** using advanced NLP techniques
- **Identifies keywords and patterns** that indicate task type
- **Calculates complexity score** based on technical depth
- **Determines optimal AI configuration** for your request

#### 🎯 **2. Smart Categorization**
Your tasks are automatically classified into these categories:

| **Category** | **Description** | **Example Messages** | **AI Optimization** |
|--------------|-----------------|---------------------|---------------------|
| 🖥️ **Coding** | Programming tasks, code generation, algorithms | "Write a Python API", "Create a React component" | Code-focused prompts, syntax highlighting |
| 🐛 **Debug** | Error analysis, troubleshooting, bug fixes | "Fix this error", "Why isn't my code working?" | Debug-specific context, error pattern analysis |
| 🎨 **Design** | UI/UX design, architecture, system planning | "Design a dashboard", "Plan database schema" | Design thinking prompts, visual descriptions |
| 📝 **Documentation** | Writing docs, README files, API documentation | "Write API docs", "Create README file" | Documentation best practices, clear structure |
| 📊 **Analysis** | Data analysis, research, investigation | "Analyze this data", "Research best practices" | Analytical thinking, comprehensive research |
| 💬 **General** | Questions, conversations, explanations | "Explain blockchain", "How does AI work?" | Conversational tone, educational focus |

#### ⚙️ **3. Dynamic Configuration**
Based on the detected category, the system automatically adjusts:

- **AI Model Selection**: GPT-4 for complex tasks, GPT-3.5 for simple ones
- **Token Limits**: More tokens for coding/analysis, fewer for general questions  
- **Response Style**: Technical detail for debugging, conversational for explanations
- **Processing Timeout**: Extended time for complex analysis tasks
- **Rate Limiting**: Adjusted based on your user tier and task complexity

### **Real-World Examples**

#### 🖥️ **Coding Task Example**
```
SMS: "Create a REST API endpoint in Python Flask for user registration"

System Analysis:
✅ Category: coding
✅ Complexity: medium (0.65)
✅ Priority: medium
✅ Model: gpt-4
✅ Max Tokens: 4000
✅ Specialized Prompt: "You are an expert Python developer..."

Response: Detailed Flask code with validation, error handling, and best practices
```

#### 🐛 **Debug Task Example**
```
SMS: "My React app crashes with 'Cannot read property map of undefined'"

System Analysis:
✅ Category: debug  
✅ Complexity: low (0.32)
✅ Priority: high (debugging is urgent)
✅ Model: gpt-4
✅ Specialized Prompt: "You are a debugging expert..."

Response: Step-by-step debugging guide with specific solution
```

#### 🎨 **Design Task Example**
```
SMS: "Design a mobile app interface for a food delivery service"

System Analysis:
✅ Category: design
✅ Complexity: high (0.78)
✅ Priority: medium
✅ Model: gpt-4
✅ Extended Processing: UI/UX focus

Response: Detailed design recommendations with layout, colors, user flow
```

---

## 👥 **User Tiers & Rate Limiting**

The system supports different user tiers with varying capabilities:

### **🆓 Free Tier**
- **10 SMS per hour**
- **1,000 AI tokens per request**
- **Standard response time**
- **All task categories supported**
- **Basic priority**

### **⭐ Premium Tier**
- **50 SMS per hour**
- **4,000 AI tokens per request**
- **Priority processing**
- **Longer responses for complex tasks**
- **Enhanced task routing**

### **🏢 Enterprise Tier**
- **Unlimited SMS**
- **8,000 AI tokens per request**
- **Highest priority processing**
- **Custom AI model configuration**
- **Advanced analytics access**
- **White-label options**

---

## 📊 **Task Complexity Scoring**

The system calculates a complexity score (0.0 to 1.0) for each task:

| **Score Range** | **Complexity** | **Examples** | **Processing** |
|-----------------|----------------|--------------|----------------|
| 0.0 - 0.3 | **Simple** | "What is Python?", "Hello world code" | Fast, standard tokens |
| 0.3 - 0.6 | **Medium** | "Create a login form", "Debug this function" | Standard processing |
| 0.6 - 0.8 | **Complex** | "Build a web scraper", "Design database schema" | Extended processing, more tokens |
| 0.8 - 1.0 | **Advanced** | "Create machine learning model", "Design microservices architecture" | Maximum resources, GPT-4 required |

---

## 📱 **SMS Response Optimization**

### **Smart Summarization**
Long AI responses are intelligently summarized for SMS:

1. **Preserve Key Information**: Essential code, steps, or solutions
2. **Maintain Context**: Keep enough detail to be useful
3. **Optimize for Mobile**: Format for easy reading on phones
4. **Include Follow-up Options**: "Reply 'MORE' for full details"

### **Response Examples**

#### Original AI Response (2000+ characters):
```
Here's a comprehensive Python function to calculate Fibonacci numbers with multiple implementation approaches:

1. Recursive Implementation:
def fibonacci_recursive(n):
    if n <= 1:
        return n
    return fibonacci_recursive(n-1) + fibonacci_recursive(n-2)

2. Iterative Implementation (More Efficient):
def fibonacci_iterative(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

3. Memoization Implementation (Best Performance):
def fibonacci_memo(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci_memo(n-1, memo) + fibonacci_memo(n-2, memo)
    return memo[n]

The iterative approach is recommended for most use cases as it has O(n) time complexity and O(1) space complexity, while the recursive approach has O(2^n) time complexity...
```

#### SMS-Optimized Response (160 characters):
```
Python Fibonacci function:

def fib(n):
    if n <= 1: return n
    a, b = 0, 1
    for _ in range(2, n+1):
        a, b = b, a+b
    return b

Reply 'MORE' for alternatives & explanation.
```

---

## 🔧 **Advanced Features**

### **🎯 Task Priority System**
Tasks are automatically prioritized:

1. **URGENT**: Debug tasks, error resolution
2. **HIGH**: Coding tasks, time-sensitive requests  
3. **MEDIUM**: Design, documentation tasks
4. **LOW**: General questions, research

### **📈 Analytics & Tracking**
Monitor your usage through the admin dashboard:

- **Task categorization breakdown**
- **Response time analytics**
- **Usage patterns and trends**
- **Popular request types**
- **Success rate metrics**

### **🔄 Follow-up Conversations**
The system maintains context for follow-up questions:

```
SMS 1: "Create a Python web scraper"
Response 1: [Code for basic web scraper]

SMS 2: "Add error handling to that"
Response 2: [Enhanced code with try/catch blocks]

SMS 3: "How do I handle rate limiting?"
Response 3: [Rate limiting implementation advice]
```

---

## 💡 **Best Practices for Optimal Results**

### **📝 Writing Effective SMS Requests**

#### ✅ **Good Examples:**
```
✅ "Create a Python function to validate email addresses"
✅ "Debug this React error: useState is not defined"  
✅ "Design a responsive navbar for my website"
✅ "Explain how to deploy Flask app to AWS"
```

#### ❌ **Less Effective Examples:**
```
❌ "Help" (too vague)
❌ "Code" (no specific request)
❌ "Fix my app" (missing context)
❌ "What should I do?" (unclear intent)
```

### **🎯 Tips for Better Responses**

1. **Be Specific**: Include technology, programming language, or specific problem
2. **Provide Context**: Mention what you're building or working on
3. **Include Error Messages**: Copy exact error text for debugging
4. **Specify Requirements**: Mention constraints, preferences, or requirements
5. **Ask Follow-ups**: Use "MORE" or ask specific follow-up questions

### **🚀 Power User Tips**

#### **Use Keywords for Better Categorization:**
- Start with action words: "Create", "Debug", "Design", "Explain"
- Include technology: "Python", "React", "CSS", "Database"
- Mention task type: "API", "Function", "Component", "Schema"

#### **Request Specific Formats:**
```
"Create a Python class for user authentication"
"Write CSS for a responsive grid layout" 
"Design a REST API schema for e-commerce"
"Debug this SQL query performance issue"
```

#### **Leverage Complexity Detection:**
The system automatically detects complexity, but you can help:

- **Simple**: "Basic Python loop"
- **Medium**: "Python web scraper with error handling"
- **Complex**: "Scalable Python microservice with authentication"
- **Advanced**: "Machine learning model for sentiment analysis"

---

## 🛠️ **Troubleshooting**

### **Common Issues & Solutions**

#### **❓ Getting Generic Responses**
**Problem**: Responses seem too general or don't match your request
**Solution**: Be more specific about technology, context, and requirements

#### **⏱️ Slow Response Times**
**Problem**: Taking too long to get responses
**Solution**: Check your user tier limits, try simpler requests during peak hours

#### **📱 Truncated Responses**
**Problem**: Response seems cut off
**Solution**: Reply with "MORE" to get the full response or additional details

#### **🔄 Rate Limiting**
**Problem**: Getting rate limit messages
**Solution**: Wait for your rate limit window to reset, or upgrade to Premium tier

### **Getting Help**
- **SMS "HELP"** for quick assistance
- **SMS "STATUS"** for your current usage stats
- **Visit Admin Dashboard** for detailed analytics
- **Check System Health** at `/health` endpoint

---

## 📊 **Real-Time Monitoring**

### **Admin Dashboard Features**
Access the admin dashboard at `/admin/` to monitor:

#### **📈 Usage Analytics**
- Tasks by category breakdown
- Response time trends  
- User activity patterns
- Popular request types

#### **🎯 Task Routing Insights**
- Categorization accuracy
- Complexity score distribution
- Model selection statistics
- Processing time by category

#### **👥 User Management**
- User tier distribution
- Rate limiting status
- Active user metrics
- Usage quota tracking

---

## 🔐 **Privacy & Security**

### **Data Protection**
- **Message Encryption**: All SMS messages are processed securely
- **No Long-term Storage**: Conversations are not permanently stored
- **Rate Limiting**: Prevents abuse and ensures fair usage
- **User Isolation**: Each user's data is kept separate and private

### **Best Security Practices**
- Don't send sensitive credentials or passwords via SMS
- Use the system for development help, not production secrets
- Monitor your usage through the admin dashboard
- Report any suspicious activity immediately

---

## 🚀 **Getting Started Checklist**

### **For Users:**
- [ ] Save the SMS phone number in your contacts
- [ ] Send a test message: "Create a simple Python hello world function"
- [ ] Try different task types (coding, debugging, design)
- [ ] Bookmark the admin dashboard for monitoring
- [ ] Experiment with follow-up questions

### **For Administrators:**
- [ ] Configure permanent ngrok domain
- [ ] Set up Twilio webhook URL
- [ ] Configure user tiers and rate limits
- [ ] Enable advanced task routing
- [ ] Set up monitoring and alerts
- [ ] Review security settings

---

**🎉 Your SMS-to-Cursor AI Agent is ready to boost your productivity! Start sending messages and experience the power of intelligent task routing and AI-powered development assistance.**

**Need help? SMS "HELP" or visit the admin dashboard for detailed analytics and system status.** 