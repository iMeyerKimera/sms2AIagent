# 🔧 Extending the System

**Complete guide for adding new features and customizing SMS-to-AI Agent**

---

## 📋 **Overview**

The SMS-to-AI Agent is designed with extensibility in mind. This guide covers how to add new features, integrate additional AI models, create custom task categories, and extend the system's capabilities while maintaining code quality and performance.

---

## 🎯 **Adding New Task Categories**

### **1. Define New Category**

```python
# core/models.py - Update Task model
class Task(TimestampedModel):
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('coding', 'Coding'),
        ('debug', 'Debug'),
        ('design', 'Design'),
        ('documentation', 'Documentation'),
        ('analysis', 'Analysis'),
        # Add new categories here
        ('translation', 'Translation'),
        ('research', 'Research'),
        ('math', 'Mathematics'),
        ('creative', 'Creative Writing'),
    ]
    
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='general'
    )
```

### **2. Create Category Processor**

```python
# processors/translation_processor.py
from .base_processor import BaseProcessor
import openai

class TranslationProcessor(BaseProcessor):
    """Processor for translation tasks"""
    
    def __init__(self):
        super().__init__()
        self.category = 'translation'
        self.description = 'Language translation and interpretation'
        
    def can_handle(self, message_content, metadata=None):
        """Check if this processor can handle the message"""
        translation_keywords = [
            'translate', 'translation', 'в переводе', 'traduire',
            'from english', 'to spanish', 'language'
        ]
        content_lower = message_content.lower()
        return any(keyword in content_lower for keyword in translation_keywords)
    
    def process(self, message_content, user_tier='free', metadata=None):
        """Process translation request"""
        
        # Enhanced prompt for translation
        prompt = f"""
        You are a professional translator. Please help with this translation request:
        
        {message_content}
        
        Please:
        1. Identify the source and target languages if not specified
        2. Provide an accurate translation
        3. Include cultural context if relevant
        4. Explain any nuances or alternative translations
        
        Keep the response conversational and helpful for SMS.
        """
        
        # Use appropriate model based on tier
        model = self.get_model_for_tier(user_tier)
        
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.get_token_limit(user_tier),
                temperature=0.3  # Lower temperature for accuracy
            )
            
            return {
                'response': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens,
                'model_used': model,
                'category': self.category,
                'confidence': 0.9  # High confidence for translations
            }
            
        except Exception as e:
            return self.handle_error(e, message_content)
    
    def get_model_for_tier(self, tier):
        """Get appropriate model based on user tier"""
        if tier == 'enterprise':
            return 'gpt-4'
        elif tier == 'premium':
            return 'gpt-3.5-turbo'
        else:
            return 'gpt-3.5-turbo'
    
    def get_token_limit(self, tier):
        """Get token limit based on user tier"""
        limits = {
            'free': 1000,
            'premium': 2000,
            'enterprise': 4000
        }
        return limits.get(tier, 1000)
```

### **3. Register Category in Router**

```python
# task_router.py - Update TaskRouter
from processors.translation_processor import TranslationProcessor

class TaskRouter:
    def __init__(self):
        self.processors = [
            TranslationProcessor(),
            CodingProcessor(),
            DebugProcessor(),
            # ... other processors
        ]
    
    def route_task(self, message_content, user_tier='free', metadata=None):
        """Route task to appropriate processor"""
        
        # Try each processor in order
        for processor in self.processors:
            if processor.can_handle(message_content, metadata):
                return processor.process(message_content, user_tier, metadata)
        
        # Fallback to general processor
        return self.general_processor.process(message_content, user_tier, metadata)
```

---

## 🤖 **Adding New AI Models**

### **1. Create AI Service Interface**

```python
# services/ai_service_interface.py
from abc import ABC, abstractmethod

class AIServiceInterface(ABC):
    """Abstract base class for AI services"""
    
    @abstractmethod
    def generate_response(self, prompt, **kwargs):
        """Generate AI response"""
        pass
    
    @abstractmethod
    def get_usage_stats(self):
        """Get usage statistics"""
        pass
    
    @abstractmethod
    def is_available(self):
        """Check if service is available"""
        pass

class AIServiceRegistry:
    """Registry for AI services"""
    
    def __init__(self):
        self.services = {}
    
    def register(self, name, service):
        """Register an AI service"""
        if not isinstance(service, AIServiceInterface):
            raise ValueError("Service must implement AIServiceInterface")
        self.services[name] = service
    
    def get_service(self, name):
        """Get an AI service by name"""
        return self.services.get(name)
    
    def list_services(self):
        """List all registered services"""
        return list(self.services.keys())
```

### **2. Implement New AI Service**

```python
# services/claude_service.py
import anthropic
from .ai_service_interface import AIServiceInterface
from django.conf import settings

class ClaudeService(AIServiceInterface):
    """Anthropic Claude AI service"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.CLAUDE_API_KEY
        )
        self.model = "claude-3-sonnet-20240229"
    
    def generate_response(self, prompt, max_tokens=1000, **kwargs):
        """Generate response using Claude"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return {
                'response': response.content[0].text,
                'tokens_used': response.usage.input_tokens + response.usage.output_tokens,
                'model_used': self.model,
                'service': 'claude'
            }
            
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")
    
    def get_usage_stats(self):
        """Get usage statistics"""
        # Implement usage tracking
        return {
            'requests_today': 0,
            'tokens_used_today': 0,
            'available_quota': 10000
        }
    
    def is_available(self):
        """Check if Claude service is available"""
        try:
            # Make a minimal test request
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )
            return True
        except:
            return False

# services/cohere_service.py
import cohere
from .ai_service_interface import AIServiceInterface

class CohereService(AIServiceInterface):
    """Cohere AI service"""
    
    def __init__(self):
        self.client = cohere.Client(settings.COHERE_API_KEY)
    
    def generate_response(self, prompt, max_tokens=1000, **kwargs):
        """Generate response using Cohere"""
        try:
            response = self.client.generate(
                model='command',
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=kwargs.get('temperature', 0.7)
            )
            
            return {
                'response': response.generations[0].text,
                'tokens_used': len(prompt.split()) + len(response.generations[0].text.split()),
                'model_used': 'command',
                'service': 'cohere'
            }
            
        except Exception as e:
            raise Exception(f"Cohere API error: {str(e)}")
    
    def get_usage_stats(self):
        """Get usage statistics"""
        return {
            'requests_today': 0,
            'tokens_used_today': 0,
            'available_quota': 10000
        }
    
    def is_available(self):
        """Check if Cohere service is available"""
        try:
            self.client.check_api_key()
            return True
        except:
            return False
```

### **3. Create AI Model Selector**

```python
# services/ai_model_selector.py
from .ai_service_interface import AIServiceRegistry
from .openai_service import OpenAIService
from .claude_service import ClaudeService
from .cohere_service import CohereService

class AIModelSelector:
    """Intelligent AI model selection"""
    
    def __init__(self):
        self.registry = AIServiceRegistry()
        self._register_services()
        
    def _register_services(self):
        """Register all available AI services"""
        self.registry.register('openai', OpenAIService())
        self.registry.register('claude', ClaudeService())
        self.registry.register('cohere', CohereService())
    
    def select_best_model(self, task_category, user_tier, content_length=0):
        """Select the best AI model for the task"""
        
        # Model selection rules
        model_preferences = {
            'coding': ['openai', 'claude'],
            'debug': ['openai', 'claude'],
            'creative': ['claude', 'cohere'],
            'translation': ['openai', 'claude'],
            'analysis': ['claude', 'openai'],
            'general': ['openai', 'cohere']
        }
        
        # Tier-based model access
        tier_access = {
            'free': ['openai'],
            'premium': ['openai', 'cohere'],
            'enterprise': ['openai', 'claude', 'cohere']
        }
        
        # Get preferred models for category
        preferred_models = model_preferences.get(task_category, ['openai'])
        available_models = tier_access.get(user_tier, ['openai'])
        
        # Find best available model
        for model in preferred_models:
            if model in available_models:
                service = self.registry.get_service(model)
                if service and service.is_available():
                    return service
        
        # Fallback to OpenAI
        return self.registry.get_service('openai')
    
    def process_with_best_model(self, prompt, task_category, user_tier, **kwargs):
        """Process request with the best available model"""
        
        service = self.select_best_model(task_category, user_tier)
        
        if not service:
            raise Exception("No AI service available")
        
        return service.generate_response(prompt, **kwargs)
```

---

## 🔌 **Adding New Integrations**

### **1. Social Media Integration**

```python
# integrations/social_media.py
import tweepy
import requests
from django.conf import settings

class TwitterIntegration:
    """Twitter integration for sharing responses"""
    
    def __init__(self):
        auth = tweepy.OAuthHandler(
            settings.TWITTER_CONSUMER_KEY,
            settings.TWITTER_CONSUMER_SECRET
        )
        auth.set_access_token(
            settings.TWITTER_ACCESS_TOKEN,
            settings.TWITTER_ACCESS_TOKEN_SECRET
        )
        self.api = tweepy.API(auth)
    
    def share_response(self, task_content, ai_response, user_consent=True):
        """Share AI response on Twitter with user consent"""
        
        if not user_consent:
            return None
        
        # Create shareable content
        tweet_content = f"""
        🤖 AI helped me with: {task_content[:50]}...
        
        💡 Solution: {ai_response[:100]}...
        
        #AI #SMS #TechHelp
        """
        
        try:
            tweet = self.api.update_status(tweet_content[:280])
            return {
                'tweet_id': tweet.id,
                'url': f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}"
            }
        except Exception as e:
            return {'error': str(e)}

class SlackIntegration:
    """Slack integration for team notifications"""
    
    def __init__(self):
        self.webhook_url = settings.SLACK_WEBHOOK_URL
    
    def send_notification(self, message, channel='#general'):
        """Send notification to Slack channel"""
        
        payload = {
            'channel': channel,
            'text': message,
            'username': 'SMS-AI Agent',
            'icon_emoji': ':robot_face:'
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload)
            return response.status_code == 200
        except Exception as e:
            return False
    
    def notify_high_value_task(self, task):
        """Notify team of high-value tasks"""
        
        if task.user_phone.tier == 'enterprise' or task.complexity_score > 0.8:
            message = f"""
            🚀 High-value task completed!
            
            User: {task.user_phone.phone_number} ({task.user_phone.tier})
            Category: {task.category}
            Processing time: {task.processing_time:.2f}s
            Tokens used: {task.tokens_used}
            """
            
            return self.send_notification(message, '#alerts')
```

### **2. Database Integration**

```python
# integrations/external_databases.py
import requests
import psycopg2
from django.conf import settings

class ExternalDatabaseIntegration:
    """Integration with external databases for enhanced responses"""
    
    def __init__(self):
        self.connections = {
            'knowledge_base': self._connect_knowledge_base(),
            'user_analytics': self._connect_analytics_db()
        }
    
    def _connect_knowledge_base(self):
        """Connect to external knowledge base"""
        if hasattr(settings, 'EXTERNAL_KB_URL'):
            return {
                'type': 'api',
                'url': settings.EXTERNAL_KB_URL,
                'auth': settings.EXTERNAL_KB_AUTH
            }
        return None
    
    def _connect_analytics_db(self):
        """Connect to external analytics database"""
        if hasattr(settings, 'ANALYTICS_DB_URL'):
            return psycopg2.connect(settings.ANALYTICS_DB_URL)
        return None
    
    def enhance_response(self, task_content, base_response, category):
        """Enhance AI response with external data"""
        
        enhancements = []
        
        # Add relevant knowledge base articles
        if category in ['coding', 'debug']:
            kb_data = self._search_knowledge_base(task_content)
            if kb_data:
                enhancements.append(f"\n📚 Related resources: {kb_data}")
        
        # Add user history insights
        if category == 'general':
            insights = self._get_user_insights(task_content)
            if insights:
                enhancements.append(f"\n💡 Based on your history: {insights}")
        
        if enhancements:
            return base_response + "\n" + "\n".join(enhancements)
        
        return base_response
    
    def _search_knowledge_base(self, query):
        """Search external knowledge base"""
        kb_conn = self.connections.get('knowledge_base')
        
        if not kb_conn or kb_conn['type'] != 'api':
            return None
        
        try:
            response = requests.get(
                f"{kb_conn['url']}/search",
                params={'q': query, 'limit': 3},
                headers={'Authorization': kb_conn['auth']}
            )
            
            if response.status_code == 200:
                results = response.json()
                return [item['title'] for item in results.get('items', [])]
            
        except Exception as e:
            pass  # Fail silently
        
        return None
    
    def _get_user_insights(self, query):
        """Get user behavior insights"""
        # Implementation depends on your analytics structure
        return None
```

---

## 📊 **Custom Analytics & Metrics**

### **1. Advanced Analytics Models**

```python
# analytics/models.py
from django.db import models
from core.models import User, Task
from django.utils import timezone

class UserBehaviorAnalytics(models.Model):
    """Advanced user behavior tracking"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Usage patterns
    most_active_hour = models.IntegerField(default=12)
    most_active_day = models.CharField(max_length=10, default='monday')
    avg_session_length = models.FloatField(default=0.0)
    
    # Preferences
    preferred_categories = models.JSONField(default=list)
    response_satisfaction = models.FloatField(default=0.0)
    
    # Performance metrics
    avg_response_time = models.FloatField(default=0.0)
    success_rate = models.FloatField(default=0.0)
    complexity_preference = models.FloatField(default=0.5)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    def update_metrics(self):
        """Update user metrics based on task history"""
        tasks = self.user.tasks.filter(success=True)
        
        if tasks.exists():
            # Calculate averages
            self.avg_response_time = tasks.aggregate(
                avg=models.Avg('processing_time')
            )['avg']
            
            self.success_rate = tasks.filter(success=True).count() / tasks.count()
            
            # Update preferred categories
            category_counts = tasks.values('category').annotate(
                count=models.Count('category')
            ).order_by('-count')
            
            self.preferred_categories = [
                item['category'] for item in category_counts[:3]
            ]
            
            self.save()

class SystemMetrics(models.Model):
    """System-wide performance metrics"""
    
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Performance metrics
    avg_response_time = models.FloatField()
    total_requests = models.IntegerField()
    successful_requests = models.IntegerField()
    error_rate = models.FloatField()
    
    # Resource usage
    cpu_usage = models.FloatField()
    memory_usage = models.FloatField()
    database_connections = models.IntegerField()
    
    # AI metrics
    total_tokens_used = models.IntegerField()
    openai_requests = models.IntegerField()
    ai_error_rate = models.FloatField()
    
    class Meta:
        ordering = ['-timestamp']

class PredictiveAnalytics(models.Model):
    """Predictive analytics for user behavior"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    prediction_date = models.DateField()
    
    # Predictions
    predicted_requests = models.IntegerField()
    churn_probability = models.FloatField()
    upgrade_probability = models.FloatField()
    preferred_time_slot = models.CharField(max_length=20)
    
    # Confidence scores
    prediction_confidence = models.FloatField()
    model_version = models.CharField(max_length=20)
    
    created_at = models.DateTimeField(auto_now_add=True)
```

### **2. Real-time Analytics Service**

```python
# analytics/services.py
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
import psutil
import redis

class RealTimeAnalytics:
    """Real-time analytics service"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=1)
    
    def track_request(self, user_phone, category, processing_time, success):
        """Track request in real-time"""
        timestamp = timezone.now()
        hour_key = timestamp.strftime('%Y-%m-%d-%H')
        
        # Update hourly metrics
        pipe = self.redis_client.pipeline()
        pipe.hincrby(f"hourly_metrics:{hour_key}", "total_requests", 1)
        pipe.hincrby(f"hourly_metrics:{hour_key}", f"category_{category}", 1)
        
        if success:
            pipe.hincrby(f"hourly_metrics:{hour_key}", "successful_requests", 1)
            pipe.hincrbyfloat(f"hourly_metrics:{hour_key}", "total_processing_time", processing_time)
        
        # User-specific tracking
        pipe.hincrby(f"user_metrics:{user_phone}", "requests_today", 1)
        pipe.hset(f"user_metrics:{user_phone}", "last_active", timestamp.isoformat())
        
        # Execute pipeline
        pipe.execute()
        
        # Set expiration for cleanup
        self.redis_client.expire(f"hourly_metrics:{hour_key}", 86400 * 7)  # 7 days
        self.redis_client.expire(f"user_metrics:{user_phone}", 86400)  # 1 day
    
    def get_real_time_metrics(self):
        """Get current real-time metrics"""
        current_hour = timezone.now().strftime('%Y-%m-%d-%H')
        metrics = self.redis_client.hgetall(f"hourly_metrics:{current_hour}")
        
        if not metrics:
            return {
                'requests_this_hour': 0,
                'success_rate': 0,
                'avg_processing_time': 0,
                'top_categories': []
            }
        
        total_requests = int(metrics.get(b'total_requests', 0))
        successful_requests = int(metrics.get(b'successful_requests', 0))
        total_processing_time = float(metrics.get(b'total_processing_time', 0))
        
        # Calculate success rate
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate average processing time
        avg_processing_time = (total_processing_time / successful_requests) if successful_requests > 0 else 0
        
        # Get top categories
        category_metrics = {
            key.decode().replace('category_', ''): int(value)
            for key, value in metrics.items()
            if key.decode().startswith('category_')
        }
        
        top_categories = sorted(
            category_metrics.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'requests_this_hour': total_requests,
            'success_rate': round(success_rate, 2),
            'avg_processing_time': round(avg_processing_time, 2),
            'top_categories': top_categories,
            'system_metrics': self._get_system_metrics()
        }
    
    def _get_system_metrics(self):
        """Get current system resource metrics"""
        return {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        }
```

---

## 🎨 **Custom UI Components**

### **1. Dashboard Widgets**

```python
# admin_dashboard/widgets.py
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

class MetricWidget:
    """Base widget for dashboard metrics"""
    
    def __init__(self, title, value, icon='fas fa-chart-line', color='primary'):
        self.title = title
        self.value = value
        self.icon = icon
        self.color = color
    
    def render(self):
        """Render widget HTML"""
        return render_to_string('widgets/metric_widget.html', {
            'title': self.title,
            'value': self.value,
            'icon': self.icon,
            'color': self.color
        })

class ChartWidget:
    """Chart widget for data visualization"""
    
    def __init__(self, title, data, chart_type='line'):
        self.title = title
        self.data = data
        self.chart_type = chart_type
    
    def render(self):
        """Render chart widget"""
        return render_to_string('widgets/chart_widget.html', {
            'title': self.title,
            'data': self.data,
            'chart_type': self.chart_type,
            'widget_id': f"chart_{id(self)}"
        })

class UserActivityWidget:
    """User activity widget"""
    
    def __init__(self, user_data):
        self.user_data = user_data
    
    def render(self):
        """Render user activity widget"""
        return render_to_string('widgets/user_activity_widget.html', {
            'users': self.user_data
        })
```

### **2. Custom Template Tags**

```python
# admin_dashboard/templatetags/dashboard_tags.py
from django import template
from django.utils.safestring import mark_safe
from analytics.services import RealTimeAnalytics

register = template.Library()

@register.simple_tag
def real_time_metrics():
    """Get real-time metrics for dashboard"""
    analytics = RealTimeAnalytics()
    return analytics.get_real_time_metrics()

@register.filter
def format_number(value):
    """Format numbers with thousands separators"""
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return value

@register.inclusion_tag('widgets/metric_card.html')
def metric_card(title, value, icon, color='primary', trend=None):
    """Render a metric card"""
    return {
        'title': title,
        'value': value,
        'icon': icon,
        'color': color,
        'trend': trend
    }

@register.inclusion_tag('widgets/progress_bar.html')
def progress_bar(value, max_value, label='', color='primary'):
    """Render a progress bar"""
    percentage = (value / max_value * 100) if max_value > 0 else 0
    return {
        'percentage': min(percentage, 100),
        'label': label,
        'color': color,
        'value': value,
        'max_value': max_value
    }
```

---

## 🔧 **Configuration Extensions**

### **1. Dynamic Configuration**

```python
# core/dynamic_config.py
from django.core.cache import cache
from django.db import models

class DynamicConfiguration(models.Model):
    """Dynamic system configuration"""
    
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    config_type = models.CharField(
        max_length=20,
        choices=[
            ('string', 'String'),
            ('integer', 'Integer'),
            ('float', 'Float'),
            ('boolean', 'Boolean'),
            ('json', 'JSON'),
        ],
        default='string'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dynamic_configuration'
    
    def __str__(self):
        return f"{self.key}: {self.value}"
    
    def get_typed_value(self):
        """Get value converted to appropriate type"""
        if not self.is_active:
            return None
        
        if self.config_type == 'integer':
            return int(self.value)
        elif self.config_type == 'float':
            return float(self.value)
        elif self.config_type == 'boolean':
            return self.value.lower() in ['true', '1', 'yes']
        elif self.config_type == 'json':
            import json
            return json.loads(self.value)
        else:
            return self.value
    
    def save(self, *args, **kwargs):
        """Clear cache on save"""
        super().save(*args, **kwargs)
        cache.delete(f"dynamic_config_{self.key}")

class ConfigManager:
    """Dynamic configuration manager"""
    
    @staticmethod
    def get(key, default=None):
        """Get configuration value with caching"""
        cache_key = f"dynamic_config_{key}"
        value = cache.get(cache_key)
        
        if value is None:
            try:
                config = DynamicConfiguration.objects.get(key=key, is_active=True)
                value = config.get_typed_value()
                cache.set(cache_key, value, 300)  # Cache for 5 minutes
            except DynamicConfiguration.DoesNotExist:
                value = default
        
        return value
    
    @staticmethod
    def set(key, value, config_type='string', description=''):
        """Set configuration value"""
        config, created = DynamicConfiguration.objects.get_or_create(
            key=key,
            defaults={
                'value': str(value),
                'config_type': config_type,
                'description': description
            }
        )
        
        if not created:
            config.value = str(value)
            config.config_type = config_type
            config.save()
        
        return config
```

---

## 🧪 **Testing Extensions**

### **1. Custom Test Framework**

```python
# testing/framework.py
from django.test import TestCase
from unittest.mock import Mock, patch
from core.models import User, Task

class SMSAgentTestCase(TestCase):
    """Base test case with common utilities"""
    
    def setUp(self):
        """Set up test data"""
        self.test_user = User.objects.create(
            phone_number='+1234567890',
            tier='premium',
            email='test@example.com'
        )
    
    def create_test_task(self, content="Test message", category="general"):
        """Create a test task"""
        return Task.objects.create(
            user_phone=self.test_user,
            sms_content=content,
            category=category
        )
    
    def mock_openai_response(self, response_text="Mock response", tokens=100):
        """Mock OpenAI API response"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = response_text
        mock_response.usage.total_tokens = tokens
        return mock_response
    
    def assert_task_completed(self, task, should_succeed=True):
        """Assert task completion state"""
        task.refresh_from_db()
        self.assertIsNotNone(task.completed_at)
        self.assertEqual(task.success, should_succeed)
        if should_succeed:
            self.assertIsNotNone(task.ai_response)

class ProcessorTestCase(SMSAgentTestCase):
    """Test case for processor testing"""
    
    def test_processor_registration(self):
        """Test that processor is properly registered"""
        from task_router import TaskRouter
        router = TaskRouter()
        
        # Check if our processor is in the list
        processor_classes = [type(p).__name__ for p in router.processors]
        self.assertIn(self.processor_class.__name__, processor_classes)
    
    def test_processor_can_handle(self):
        """Test processor can_handle method"""
        processor = self.processor_class()
        
        # Test positive cases
        for test_input in self.positive_test_cases:
            with self.subTest(input=test_input):
                self.assertTrue(processor.can_handle(test_input))
        
        # Test negative cases
        for test_input in self.negative_test_cases:
            with self.subTest(input=test_input):
                self.assertFalse(processor.can_handle(test_input))
```

---

## 📚 **Extension Best Practices**

### **1. Code Quality Standards**

```python
# quality/standards.py
"""
Extension development standards for SMS-to-AI Agent

1. Code Style:
   - Follow PEP 8 for Python code
   - Use type hints for function parameters and return values
   - Write docstrings for all public methods
   - Use meaningful variable and function names

2. Testing:
   - Write unit tests for all new functionality
   - Aim for >90% code coverage
   - Include integration tests for external services
   - Test error conditions and edge cases

3. Documentation:
   - Document all new API endpoints
   - Include configuration options
   - Provide usage examples
   - Update relevant documentation files

4. Performance:
   - Cache frequently accessed data
   - Use database indexes for new queries
   - Implement rate limiting for new endpoints
   - Monitor resource usage

5. Security:
   - Validate all input data
   - Use parameterized queries
   - Implement proper authentication
   - Audit sensitive operations
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class ExtensionBase:
    """Base class for all extensions"""
    
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.enabled = True
        logger.info(f"Initializing extension: {name} v{version}")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate extension configuration"""
        raise NotImplementedError("Extensions must implement validate_config")
    
    def initialize(self) -> bool:
        """Initialize the extension"""
        raise NotImplementedError("Extensions must implement initialize")
    
    def cleanup(self) -> None:
        """Clean up extension resources"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get extension status"""
        return {
            'name': self.name,
            'version': self.version,
            'enabled': self.enabled,
            'status': 'active' if self.enabled else 'inactive'
        }
```

### **2. Extension Manager**

```python
# extensions/manager.py
from typing import Dict, List, Type
import importlib
import logging

logger = logging.getLogger(__name__)

class ExtensionManager:
    """Manages system extensions"""
    
    def __init__(self):
        self.extensions: Dict[str, ExtensionBase] = {}
        self.load_order: List[str] = []
    
    def register_extension(self, extension_class: Type[ExtensionBase], config: Dict[str, Any] = None):
        """Register a new extension"""
        try:
            extension = extension_class(**config or {})
            
            if extension.validate_config(config or {}):
                self.extensions[extension.name] = extension
                self.load_order.append(extension.name)
                logger.info(f"Registered extension: {extension.name}")
                return True
            else:
                logger.error(f"Invalid configuration for extension: {extension.name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to register extension: {e}")
            return False
    
    def load_all_extensions(self):
        """Load all registered extensions"""
        for name in self.load_order:
            extension = self.extensions[name]
            try:
                if extension.initialize():
                    logger.info(f"Loaded extension: {name}")
                else:
                    logger.error(f"Failed to load extension: {name}")
                    extension.enabled = False
            except Exception as e:
                logger.error(f"Error loading extension {name}: {e}")
                extension.enabled = False
    
    def get_active_extensions(self) -> List[ExtensionBase]:
        """Get list of active extensions"""
        return [ext for ext in self.extensions.values() if ext.enabled]
    
    def disable_extension(self, name: str) -> bool:
        """Disable an extension"""
        if name in self.extensions:
            self.extensions[name].enabled = False
            self.extensions[name].cleanup()
            logger.info(f"Disabled extension: {name}")
            return True
        return False
    
    def get_extension_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all extensions"""
        return {
            name: extension.get_status()
            for name, extension in self.extensions.items()
        }
```

---

## 🔗 **Related Documentation**

- **[Architecture Guide](ARCHITECTURE.md)** - System architecture overview
- **[Django Integration](DJANGO.md)** - Django implementation details
- **[API Reference](../user-guides/API_REFERENCE.md)** - REST API documentation
- **[Configuration Guide](../getting-started/CONFIGURATION.md)** - System configuration

---

**🔧 Your system is now ready for extensions! Use these patterns to safely add new features while maintaining system stability and performance.** 