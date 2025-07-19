"""
Advanced Task Router Module
Intelligent routing system for SMS-to-Cursor AI tasks with priority handling and user profiles
"""

import os
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

class TaskCategory(Enum):
    CODING = "coding"
    DEBUG = "debug"
    DESIGN = "design"
    DOCUMENTATION = "documentation"
    GENERAL = "general"
    ANALYSIS = "analysis"

class UserTier(Enum):
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class TaskRouter:
    """Advanced task routing system with intelligent categorization and priority handling"""
    
    def __init__(self):
        self.db_path = "task_analytics.db"
        self._init_database()
        self._load_routing_rules()
    
    def _init_database(self):
        """Initialize SQLite database for analytics and user management"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                phone_number TEXT PRIMARY KEY,
                tier TEXT DEFAULT 'free',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP,
                total_requests INTEGER DEFAULT 0,
                monthly_requests INTEGER DEFAULT 0,
                monthly_reset_date DATE
            )
        ''')
        
        # Tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_phone TEXT,
                task_hash TEXT UNIQUE,
                category TEXT,
                priority INTEGER,
                complexity_score REAL,
                request_text TEXT,
                response_text TEXT,
                processing_time REAL,
                success BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                tokens_used INTEGER,
                FOREIGN KEY (user_phone) REFERENCES users (phone_number)
            )
        ''')
        
        # System metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT,
                metric_value REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Error logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_phone TEXT,
                error_type TEXT,
                error_message TEXT,
                request_text TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_routing_rules(self):
        """Load routing rules and complexity weights"""
        self.routing_rules = {
            "coding_keywords": [
                "function", "class", "algorithm", "code", "program", "script",
                "api", "database", "sql", "python", "javascript", "react",
                "html", "css", "json", "xml", "regex", "loop", "array"
            ],
            "debug_keywords": [
                "error", "bug", "fix", "debug", "troubleshoot", "issue",
                "broken", "not working", "problem", "exception", "crash"
            ],
            "design_keywords": [
                "design", "ui", "ux", "layout", "interface", "mockup",
                "wireframe", "prototype", "user experience", "responsive"
            ],
            "documentation_keywords": [
                "documentation", "readme", "guide", "tutorial", "manual",
                "instructions", "explain", "how to", "steps", "process"
            ],
            "analysis_keywords": [
                "analyze", "review", "compare", "evaluate", "assess",
                "performance", "optimization", "metrics", "data", "report"
            ]
        }
        
        self.complexity_weights = {
            "word_count": 0.1,
            "technical_terms": 0.3,
            "code_mentions": 0.4,
            "multi_step": 0.2
        }
    
    def route_task(self, user_phone: str, request_text: str) -> Dict[str, Any]:
        """
        Route a task based on user profile, content analysis, and system load
        """
        try:
            # Update user activity
            user_info = self._update_user_activity(user_phone)
            
            # Analyze task complexity and category
            analysis = self._analyze_task(request_text)
            
            # Check rate limits and permissions
            rate_limit_check = self._check_rate_limits(user_phone, user_info)
            if not rate_limit_check["allowed"]:
                return rate_limit_check
            
            # Determine priority based on user tier and task complexity
            priority = self._calculate_priority(user_info, analysis)
            
            # Create task record
            task_id = self._create_task_record(user_phone, request_text, analysis, priority)
            
            # Route to appropriate handler
            routing_decision = self._make_routing_decision(analysis, priority, user_info)
            
            return {
                "success": True,
                "task_id": task_id,
                "category": analysis["category"],
                "priority": priority.name,
                "complexity_score": analysis["complexity_score"],
                "routing_decision": routing_decision,
                "user_tier": user_info["tier"],
                "estimated_tokens": analysis["estimated_tokens"]
            }
            
        except Exception as e:
            logger.error(f"Error in task routing: {e}")
            self._log_error(user_phone, "ROUTING_ERROR", str(e), request_text)
            return {
                "success": False,
                "error": "Task routing failed",
                "fallback_to_basic": True
            }
    
    def _analyze_task(self, request_text: str) -> Dict[str, Any]:
        """Analyze task complexity, category, and requirements"""
        text_lower = request_text.lower()
        
        # Categorize task
        category_scores = {}
        for category, keywords in self.routing_rules.items():
            if category.endswith("_keywords"):
                category_name = category.replace("_keywords", "")
                score = sum(1 for keyword in keywords if keyword in text_lower)
                category_scores[category_name] = score
        
        # Determine primary category
        primary_category = max(category_scores, key=category_scores.get) if category_scores else "general"
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity(request_text)
        
        # Estimate token usage
        estimated_tokens = self._estimate_tokens(request_text, complexity_score)
        
        return {
            "category": primary_category,
            "category_scores": category_scores,
            "complexity_score": complexity_score,
            "estimated_tokens": estimated_tokens,
            "word_count": len(request_text.split()),
            "has_code_blocks": "```" in request_text or "def " in request_text,
            "is_multi_step": any(word in text_lower for word in ["step", "then", "next", "after", "first", "second"])
        }
    
    def _calculate_complexity(self, request_text: str) -> float:
        """Calculate task complexity score (0-1)"""
        complexity = 0.0
        
        # Word count factor
        word_count = len(request_text.split())
        complexity += min(word_count / 100, 1.0) * self.complexity_weights["word_count"]
        
        # Technical terms factor
        technical_terms = sum(1 for word in request_text.lower().split() 
                            if word in ["api", "database", "algorithm", "framework", "library", "class", "function"])
        complexity += min(technical_terms / 5, 1.0) * self.complexity_weights["technical_terms"]
        
        # Code mentions factor
        code_indicators = request_text.count("```") + request_text.count("def ") + request_text.count("class ")
        complexity += min(code_indicators / 3, 1.0) * self.complexity_weights["code_mentions"]
        
        # Multi-step factor
        step_indicators = sum(1 for word in ["step", "then", "next", "after", "first", "second"] 
                            if word in request_text.lower())
        complexity += min(step_indicators / 3, 1.0) * self.complexity_weights["multi_step"]
        
        return min(complexity, 1.0)
    
    def _estimate_tokens(self, request_text: str, complexity_score: float) -> int:
        """Estimate token usage for the task"""
        base_tokens = len(request_text.split()) * 1.3  # Rough estimation
        complexity_multiplier = 1 + (complexity_score * 3)  # More complex = more tokens
        return int(base_tokens * complexity_multiplier)
    
    def _update_user_activity(self, phone_number: str) -> Dict[str, Any]:
        """Update user activity and return user info"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE phone_number = ?", (phone_number,))
        user = cursor.fetchone()
        
        if user:
            # Update existing user
            cursor.execute('''
                UPDATE users 
                SET last_active = CURRENT_TIMESTAMP, 
                    total_requests = total_requests + 1,
                    monthly_requests = monthly_requests + 1
                WHERE phone_number = ?
            ''', (phone_number,))
            
            # Get updated user info
            cursor.execute("SELECT * FROM users WHERE phone_number = ?", (phone_number,))
            user = cursor.fetchone()
        else:
            # Create new user
            cursor.execute('''
                INSERT INTO users (phone_number, monthly_reset_date)
                VALUES (?, date('now', '+1 month'))
            ''', (phone_number,))
            
            cursor.execute("SELECT * FROM users WHERE phone_number = ?", (phone_number,))
            user = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        return {
            "phone_number": user[0],
            "tier": user[1],
            "total_requests": user[4],
            "monthly_requests": user[5]
        }
    
    def _check_rate_limits(self, phone_number: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Check if user has exceeded rate limits"""
        tier = user_info["tier"]
        monthly_requests = user_info["monthly_requests"]
        
        # Rate limits by tier
        limits = {
            "free": {"monthly": 50, "daily": 10},
            "premium": {"monthly": 500, "daily": 50},
            "enterprise": {"monthly": 5000, "daily": 200}
        }
        
        tier_limits = limits.get(tier, limits["free"])
        
        # Check monthly limit
        if monthly_requests >= tier_limits["monthly"]:
            return {
                "allowed": False,
                "error": f"Monthly limit exceeded ({tier_limits['monthly']} requests/month for {tier} tier)",
                "upgrade_suggestion": True
            }
        
        # Check daily limit
        daily_count = self._get_daily_request_count(phone_number)
        if daily_count >= tier_limits["daily"]:
            return {
                "allowed": False,
                "error": f"Daily limit exceeded ({tier_limits['daily']} requests/day for {tier} tier)",
                "retry_after": "24 hours"
            }
        
        return {"allowed": True}
    
    def _get_daily_request_count(self, phone_number: str) -> int:
        """Get request count for today"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM tasks 
            WHERE user_phone = ? AND date(created_at) = date('now')
        ''', (phone_number,))
        
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def _calculate_priority(self, user_info: Dict[str, Any], analysis: Dict[str, Any]) -> TaskPriority:
        """Calculate task priority based on user tier and complexity"""
        tier = user_info["tier"]
        complexity = analysis["complexity_score"]
        
        # Base priority by tier
        tier_priority = {
            "free": TaskPriority.LOW,
            "premium": TaskPriority.MEDIUM,
            "enterprise": TaskPriority.HIGH
        }
        
        base_priority = tier_priority.get(tier, TaskPriority.LOW)
        
        # Adjust for complexity
        if complexity > 0.8:
            # High complexity tasks get priority boost
            if base_priority == TaskPriority.LOW:
                return TaskPriority.MEDIUM
            elif base_priority == TaskPriority.MEDIUM:
                return TaskPriority.HIGH
            else:
                return TaskPriority.URGENT
        
        return base_priority
    
    def _make_routing_decision(self, analysis: Dict[str, Any], priority: TaskPriority, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Make intelligent routing decision"""
        category = analysis["category"]
        complexity = analysis["complexity_score"]
        
        # Route based on category and complexity
        if category == "coding" and complexity > 0.6:
            model = "gpt-4" if user_info["tier"] != "free" else "gpt-3.5-turbo"
            max_tokens = 2000 if complexity > 0.8 else 1500
        elif category == "debug":
            model = "gpt-4"  # Debug tasks benefit from better reasoning
            max_tokens = 1500
        elif category == "design":
            model = "gpt-4"  # Design needs creativity
            max_tokens = 1200
        else:
            model = "gpt-3.5-turbo"  # General tasks
            max_tokens = 1000
        
        return {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": 0.3 if category in ["coding", "debug"] else 0.7,
            "use_system_prompt": True,
            "enable_code_execution": category == "coding" and user_info["tier"] == "enterprise"
        }
    
    def _create_task_record(self, user_phone: str, request_text: str, analysis: Dict[str, Any], priority: TaskPriority) -> int:
        """Create task record in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create unique hash for task
        task_hash = hashlib.md5(f"{user_phone}{request_text}{datetime.now()}".encode()).hexdigest()
        
        cursor.execute('''
            INSERT INTO tasks (user_phone, task_hash, category, priority, complexity_score, 
                             request_text, tokens_used)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_phone, task_hash, analysis["category"], priority.value, 
              analysis["complexity_score"], request_text, analysis["estimated_tokens"]))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return task_id
    
    def complete_task(self, task_id: int, response_text: str, processing_time: float, success: bool):
        """Mark task as completed and update metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tasks 
            SET response_text = ?, processing_time = ?, success = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (response_text, processing_time, success, task_id))
        
        # Update system metrics
        cursor.execute('''
            INSERT INTO system_metrics (metric_name, metric_value)
            VALUES ('processing_time', ?), ('success_rate', ?)
        ''', (processing_time, 1.0 if success else 0.0))
        
        conn.commit()
        conn.close()
    
    def _log_error(self, user_phone: str, error_type: str, error_message: str, request_text: str):
        """Log error to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO error_logs (user_phone, error_type, error_message, request_text)
            VALUES (?, ?, ?, ?)
        ''', (user_phone, error_type, error_message, request_text))
        
        conn.commit()
        conn.close()
    
    def get_user_analytics(self, phone_number: str) -> Dict[str, Any]:
        """Get analytics for a specific user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User stats
        cursor.execute("SELECT * FROM users WHERE phone_number = ?", (phone_number,))
        user = cursor.fetchone()
        
        # Task statistics
        cursor.execute('''
            SELECT category, COUNT(*), AVG(complexity_score), AVG(processing_time)
            FROM tasks WHERE user_phone = ? AND success = 1
            GROUP BY category
        ''', (phone_number,))
        task_stats = cursor.fetchall()
        
        # Recent tasks
        cursor.execute('''
            SELECT category, complexity_score, success, created_at
            FROM tasks WHERE user_phone = ?
            ORDER BY created_at DESC LIMIT 10
        ''', (phone_number,))
        recent_tasks = cursor.fetchall()
        
        conn.close()
        
        return {
            "user_info": user,
            "task_statistics": task_stats,
            "recent_tasks": recent_tasks,
            "recommendations": self._generate_user_recommendations(task_stats)
        }
    
    def _generate_user_recommendations(self, task_stats: List) -> List[str]:
        """Generate personalized recommendations for user"""
        recommendations = []
        
        if not task_stats:
            recommendations.append("Try asking for coding help to get started!")
            return recommendations
        
        # Analyze usage patterns
        categories = [stat[0] for stat in task_stats]
        
        if "coding" in categories:
            recommendations.append("Consider upgrading to Premium for access to GPT-4 for complex coding tasks")
        
        if len(categories) == 1:
            recommendations.append("Try exploring other categories like design or documentation")
        
        avg_complexity = sum(stat[2] for stat in task_stats) / len(task_stats)
        if avg_complexity > 0.7:
            recommendations.append("You're tackling complex tasks! Enterprise tier offers code execution capabilities")
        
        return recommendations 