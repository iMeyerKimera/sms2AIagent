"""
PostgreSQL Database Manager
Provides robust database management for the Enhanced SMS-to-Cursor AI Agent
"""

import os
import logging
from contextlib import contextmanager
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import json
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import psycopg2
    import psycopg2.extras
    import psycopg2.pool
except ImportError:
    raise RuntimeError("PostgreSQL support requires psycopg2. Install with: pip install psycopg2-binary")


class DatabaseManager:
    """
    PostgreSQL Database Manager
    Provides connection management, schema initialization, and health monitoring
    """
    
    def __init__(self, database_url: str = None, notification_db_url: str = None, pool_size: int = 10):
        """
        Initialize PostgreSQL database manager
        
        Args:
            database_url: PostgreSQL connection URL
            notification_db_url: Notification database URL (defaults to main database)
            pool_size: Connection pool size for better performance
        """
        # Default database URLs
        if not database_url:
            database_url = os.environ.get('DATABASE_URL', 
                'postgresql://sms_agent:secure_password_123@localhost:5432/sms_agent_db')
        
        if not notification_db_url:
            notification_db_url = os.environ.get('NOTIFICATION_DB_URL', database_url)
        
        self.database_url = database_url
        self.notification_db_url = notification_db_url
        
        # Parse database configurations
        self.main_db_config = self._parse_database_url(database_url)
        self.notification_db_config = self._parse_database_url(notification_db_url)
        
        # Initialize connection pools for better performance
        self._init_connection_pools(pool_size)
        
        # Initialize database schemas
        self._init_databases()
        
        logger.info(f"PostgreSQL Database Manager initialized - Main: {self.main_db_config['database']}, "
                   f"Notifications: {self.notification_db_config['database']}")
    
    def _parse_database_url(self, url: str) -> Dict[str, Any]:
        """Parse PostgreSQL database URL and return connection configuration"""
        parsed = urlparse(url)
        
        if parsed.scheme != 'postgresql':
            raise ValueError(f"Only PostgreSQL URLs are supported. Got: {parsed.scheme}")
        
        return {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/') or 'sms_agent_db',
            'username': parsed.username or 'sms_agent',
            'password': parsed.password or 'secure_password_123'
        }
    
    def _init_connection_pools(self, pool_size: int):
        """Initialize connection pools for better performance"""
        try:
            # Main database connection pool
            self.main_pool = psycopg2.pool.ThreadedConnectionPool(
                1, pool_size,
                host=self.main_db_config['host'],
                port=self.main_db_config['port'],
                database=self.main_db_config['database'],
                user=self.main_db_config['username'],
                password=self.main_db_config['password']
            )
            
            # Notification database connection pool (may be same as main)
            if self.notification_db_config != self.main_db_config:
                self.notification_pool = psycopg2.pool.ThreadedConnectionPool(
                    1, pool_size // 2,  # Smaller pool for notifications
                    host=self.notification_db_config['host'],
                    port=self.notification_db_config['port'],
                    database=self.notification_db_config['database'],
                    user=self.notification_db_config['username'],
                    password=self.notification_db_config['password']
                )
            else:
                self.notification_pool = self.main_pool
                
            logger.info("Connection pools initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize connection pools: {e}")
            raise
    
    @contextmanager
    def get_connection(self, db_type: str = 'main'):
        """
        Get database connection from pool
        
        Args:
            db_type: 'main' for main database, 'notifications' for notification database
        """
        pool = self.main_pool if db_type == 'main' else self.notification_pool
        conn = None
        
        try:
            conn = pool.getconn()
            conn.autocommit = False
            yield conn
        finally:
            if conn:
                pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, db_type: str = 'main'):
        """Get database cursor with automatic commit/rollback"""
        with self.get_connection(db_type) as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            try:
                yield cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: tuple = None, db_type: str = 'main', fetch: str = 'all') -> Optional[List[Dict]]:
        """
        Execute PostgreSQL query and return results
        
        Args:
            query: SQL query string
            params: Query parameters
            db_type: Database to query ('main' or 'notifications')
            fetch: 'all', 'one', or 'none' for fetchall(), fetchone(), or no fetch
        """
        with self.get_cursor(db_type) as cursor:
            cursor.execute(query, params or ())
            
            if fetch == 'all':
                return [dict(row) for row in cursor.fetchall()]
            elif fetch == 'one':
                row = cursor.fetchone()
                return dict(row) if row else None
            else:
                return None
    
    def execute_many(self, query: str, params_list: List[tuple], db_type: str = 'main') -> int:
        """
        Execute query with multiple parameter sets (bulk operations)
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
            db_type: Database to query
            
        Returns:
            Number of affected rows
        """
        with self.get_cursor(db_type) as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    def _init_databases(self):
        """Initialize PostgreSQL database schemas"""
        try:
            self._init_main_database()
            self._init_notification_database()
            self._create_indexes()
            self._insert_initial_data()
            logger.info("PostgreSQL database schemas initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing databases: {e}")
            raise
    
    def _init_main_database(self):
        """Initialize main database schema"""
        schema_queries = [
            # Create custom types
            """
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_tier') THEN
                    CREATE TYPE user_tier AS ENUM ('free', 'premium', 'enterprise');
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_priority') THEN
                    CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high', 'urgent');
                END IF;
            END $$;
            """,
            
            # Users table
            """
            CREATE TABLE IF NOT EXISTS users (
                phone_number VARCHAR(20) PRIMARY KEY,
                tier user_tier DEFAULT 'free',
                created_at TIMESTAMP DEFAULT NOW(),
                last_active TIMESTAMP DEFAULT NOW(),
                total_requests INTEGER DEFAULT 0,
                monthly_requests INTEGER DEFAULT 0,
                rate_limit_reset TIMESTAMP,
                email VARCHAR(255),
                full_name VARCHAR(255),
                timezone VARCHAR(50) DEFAULT 'UTC',
                preferences JSONB DEFAULT '{}'::jsonb
            )
            """,
            
            # Tasks table
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                user_phone VARCHAR(20) REFERENCES users(phone_number) ON DELETE CASCADE,
                category VARCHAR(50),
                complexity_score REAL,
                priority task_priority DEFAULT 'medium',
                processing_time REAL,
                success BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT NOW(),
                completed_at TIMESTAMP,
                tokens_used INTEGER DEFAULT 0,
                request_text TEXT,
                response_text TEXT,
                task_hash VARCHAR(64) UNIQUE,
                metadata JSONB DEFAULT '{}'::jsonb,
                error_message TEXT
            )
            """,
            
            # Error logs table
            """
            CREATE TABLE IF NOT EXISTS error_logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT NOW(),
                error_type VARCHAR(50),
                error_message TEXT,
                user_phone VARCHAR(20),
                task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
                request_text TEXT,
                stack_trace TEXT,
                severity VARCHAR(20) DEFAULT 'error'
            )
            """,
            
            # System metrics table
            """
            CREATE TABLE IF NOT EXISTS system_metrics (
                id SERIAL PRIMARY KEY,
                metric_name VARCHAR(100),
                metric_value REAL,
                timestamp TIMESTAMP DEFAULT NOW(),
                metadata JSONB DEFAULT '{}'::jsonb,
                tags VARCHAR(255)[]
            )
            """,
            
            # Database version table
            """
            CREATE TABLE IF NOT EXISTS db_version (
                id SERIAL PRIMARY KEY,
                version INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT NOW(),
                migration_notes TEXT
            )
            """,
            
            # Notification preferences table
            """
            CREATE TABLE IF NOT EXISTS notification_preferences (
                phone_number VARCHAR(20) PRIMARY KEY REFERENCES users(phone_number) ON DELETE CASCADE,
                email_notifications BOOLEAN DEFAULT true,
                sms_notifications BOOLEAN DEFAULT true,
                task_completion_alerts BOOLEAN DEFAULT true,
                system_alerts BOOLEAN DEFAULT true,
                quiet_hours_start INTEGER CHECK (quiet_hours_start >= 0 AND quiet_hours_start <= 23),
                quiet_hours_end INTEGER CHECK (quiet_hours_end >= 0 AND quiet_hours_end <= 23),
                updated_at TIMESTAMP DEFAULT NOW()
            )
            """
        ]
        
        with self.get_cursor('main') as cursor:
            for query in schema_queries:
                cursor.execute(query)
    
    def _init_notification_database(self):
        """Initialize notification database schema"""
        schema_queries = [
            # Create notification status enum
            """
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notification_status') THEN
                    CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'delivered', 'failed', 'bounced');
                END IF;
            END $$;
            """,
            
            # Notification templates table
            """
            CREATE TABLE IF NOT EXISTS notification_templates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE,
                type VARCHAR(20),
                subject_template TEXT,
                body_template TEXT,
                variables JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                active BOOLEAN DEFAULT true
            )
            """,
            
            # Notification history table
            """
            CREATE TABLE IF NOT EXISTS notification_history (
                id SERIAL PRIMARY KEY,
                recipient VARCHAR(255),
                type VARCHAR(20),
                subject TEXT,
                body TEXT,
                status notification_status DEFAULT 'pending',
                sent_at TIMESTAMP DEFAULT NOW(),
                delivery_status VARCHAR(20),
                error_message TEXT,
                template_id INTEGER REFERENCES notification_templates(id) ON DELETE SET NULL,
                metadata JSONB DEFAULT '{}'::jsonb
            )
            """,
            
            # User communication preferences
            """
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_phone VARCHAR(20) PRIMARY KEY,
                email VARCHAR(255),
                sms_enabled BOOLEAN DEFAULT true,
                email_enabled BOOLEAN DEFAULT false,
                webhook_url VARCHAR(500),
                slack_webhook VARCHAR(500),
                preferred_channels TEXT[],
                quiet_hours_start INTEGER,
                quiet_hours_end INTEGER,
                timezone VARCHAR(50) DEFAULT 'UTC',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
            """,
            
            # Alert rules table
            """
            CREATE TABLE IF NOT EXISTS alert_rules (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                condition_type VARCHAR(50),
                condition_value VARCHAR(100),
                alert_level VARCHAR(20),
                notification_channels TEXT[],
                enabled BOOLEAN DEFAULT true,
                cooldown_minutes INTEGER DEFAULT 60,
                last_triggered TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
            """
        ]
        
        with self.get_cursor('notifications') as cursor:
            for query in schema_queries:
                cursor.execute(query)
    
    def _create_indexes(self):
        """Create performance indexes"""
        main_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_tier ON users(tier)",
            "CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_user_phone ON tasks(user_phone)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_success ON tasks(success)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_user_created ON tasks(user_phone, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp ON error_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_error_logs_type ON error_logs(error_type)",
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(metric_name)",
            "CREATE INDEX IF NOT EXISTS idx_system_metrics_name_timestamp ON system_metrics(metric_name, timestamp)"
        ]
        
        notification_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_notification_history_sent_at ON notification_history(sent_at)",
            "CREATE INDEX IF NOT EXISTS idx_notification_history_type ON notification_history(type)",
            "CREATE INDEX IF NOT EXISTS idx_notification_history_status ON notification_history(status)",
            "CREATE INDEX IF NOT EXISTS idx_notification_history_recipient ON notification_history(recipient)",
            "CREATE INDEX IF NOT EXISTS idx_alert_rules_enabled ON alert_rules(enabled)"
        ]
        
        # Create main database indexes
        for index_query in main_indexes:
            try:
                with self.get_cursor('main') as cursor:
                    cursor.execute(index_query)
            except Exception as e:
                logger.warning(f"Failed to create main index: {e}")
        
        # Create notification database indexes
        for index_query in notification_indexes:
            try:
                with self.get_cursor('notifications') as cursor:
                    cursor.execute(index_query)
            except Exception as e:
                logger.warning(f"Failed to create notification index: {e}")
    
    def _insert_initial_data(self):
        """Insert initial data for system functionality"""
        # Insert database version
        version_query = """
        INSERT INTO db_version (version, migration_notes) 
        VALUES (1, 'Initial PostgreSQL schema') 
        ON CONFLICT DO NOTHING
        """
        
        # Insert default notification templates
        template_queries = [
            """
            INSERT INTO notification_templates (name, type, subject_template, body_template, variables)
            VALUES (
                'task_completion', 
                'sms', 
                'Task Completed', 
                'Your task "{{task_category}}" has been completed successfully in {{processing_time}}s.',
                '{"task_category": "string", "processing_time": "number"}'::jsonb
            ) ON CONFLICT (name) DO NOTHING
            """,
            """
            INSERT INTO notification_templates (name, type, subject_template, body_template, variables)
            VALUES (
                'system_alert', 
                'email', 
                'System Alert: {{alert_level}}', 
                'Alert: {{message}}\nTime: {{timestamp}}\nLevel: {{alert_level}}',
                '{"alert_level": "string", "message": "string", "timestamp": "string"}'::jsonb
            ) ON CONFLICT (name) DO NOTHING
            """
        ]
        
        try:
            with self.get_cursor('main') as cursor:
                cursor.execute(version_query)
            
            with self.get_cursor('notifications') as cursor:
                for query in template_queries:
                    cursor.execute(query)
                    
            logger.info("Initial data inserted successfully")
        except Exception as e:
            logger.warning(f"Failed to insert initial data: {e}")
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about database configuration"""
        return {
            "main_database": {
                "type": "postgresql",
                "host": self.main_db_config['host'],
                "port": self.main_db_config['port'],
                "database": self.main_db_config['database'],
                "url": self.database_url
            },
            "notification_database": {
                "type": "postgresql",
                "host": self.notification_db_config['host'],
                "port": self.notification_db_config['port'],
                "database": self.notification_db_config['database'],
                "url": self.notification_db_url
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive database health check"""
        health = {"status": "healthy", "databases": {}, "performance": {}}
        
        # Check main database
        try:
            with self.get_cursor('main') as cursor:
                # Basic connectivity
                cursor.execute("SELECT 1")
                
                # Check table counts
                cursor.execute("""
                    SELECT 
                        'users' as table_name, COUNT(*) as count FROM users
                    UNION ALL
                    SELECT 'tasks', COUNT(*) FROM tasks
                    UNION ALL
                    SELECT 'error_logs', COUNT(*) FROM error_logs
                """)
                table_counts = {row['table_name']: row['count'] for row in cursor.fetchall()}
                
                # Check database size
                cursor.execute("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as db_size
                """)
                db_size = cursor.fetchone()['db_size']
                
                health["databases"]["main"] = {
                    "status": "healthy",
                    "type": "postgresql",
                    "table_counts": table_counts,
                    "database_size": db_size
                }
        except Exception as e:
            health["databases"]["main"] = {"status": "unhealthy", "error": str(e)}
            health["status"] = "unhealthy"
        
        # Check notification database
        try:
            with self.get_cursor('notifications') as cursor:
                cursor.execute("SELECT 1")
                
                cursor.execute("""
                    SELECT 
                        'notification_history' as table_name, COUNT(*) as count FROM notification_history
                    UNION ALL
                    SELECT 'notification_templates', COUNT(*) FROM notification_templates
                    UNION ALL
                    SELECT 'alert_rules', COUNT(*) FROM alert_rules
                """)
                notification_counts = {row['table_name']: row['count'] for row in cursor.fetchall()}
                
                health["databases"]["notifications"] = {
                    "status": "healthy",
                    "type": "postgresql",
                    "table_counts": notification_counts
                }
        except Exception as e:
            health["databases"]["notifications"] = {"status": "unhealthy", "error": str(e)}
            health["status"] = "unhealthy"
        
        # Performance metrics
        try:
            with self.get_cursor('main') as cursor:
                cursor.execute("""
                    SELECT 
                        numbackends as active_connections,
                        xact_commit as transactions_committed,
                        xact_rollback as transactions_rolled_back,
                        tup_returned as tuples_returned,
                        tup_fetched as tuples_fetched
                    FROM pg_stat_database 
                    WHERE datname = current_database()
                """)
                performance_data = dict(cursor.fetchone())
                health["performance"] = performance_data
        except Exception as e:
            logger.warning(f"Could not fetch performance metrics: {e}")
        
        return health
    
    def close_pools(self):
        """Close connection pools gracefully"""
        try:
            if hasattr(self, 'main_pool'):
                self.main_pool.closeall()
            if hasattr(self, 'notification_pool') and self.notification_pool != self.main_pool:
                self.notification_pool.closeall()
            logger.info("Connection pools closed successfully")
        except Exception as e:
            logger.error(f"Error closing connection pools: {e}")


# Global database manager instance
db_manager: Optional[DatabaseManager] = None

def get_database_manager() -> DatabaseManager:
    """Get global PostgreSQL database manager instance"""
    global db_manager
    if db_manager is None:
        database_url = os.environ.get('DATABASE_URL')
        notification_db_url = os.environ.get('NOTIFICATION_DB_URL')
        pool_size = int(os.environ.get('DB_POOL_SIZE', '10'))
        db_manager = DatabaseManager(database_url, notification_db_url, pool_size)
    return db_manager

def init_database_manager(database_url: str = None, notification_db_url: str = None, pool_size: int = 10):
    """Initialize global PostgreSQL database manager with specific configuration"""
    global db_manager
    db_manager = DatabaseManager(database_url, notification_db_url, pool_size) 