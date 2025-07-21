# 🗄️ Database Documentation

## 📋 **Database Overview**

The Enhanced SMS-to-Cursor AI Agent uses SQLite databases for persistent data storage with automatic schema management, migrations, and performance optimization.

### **Database Files**
- **`task_analytics.db`**: Main application database (users, tasks, metrics, errors)
- **`notifications.db`**: Notification system database (templates, history, preferences)

### **Storage Location**
- **Container Path**: `/app/data/` (persistent volume)
- **Host Path**: `./data/` (mounted volume)
- **Backup Location**: `/app/data/backups/`

### **Key Features**
- **Automatic Schema Creation**: Tables created on first run
- **Migration System**: Version-based schema updates
- **Performance Indexes**: Optimized queries with proper indexing
- **Sample Data**: Demonstration data for development
- **Backup System**: Automated daily backups
- **Health Monitoring**: Database integrity checks

---

## 🏗️ **Schema Documentation**

### **task_analytics.db Schema**

#### **users** Table
Primary user management and tier tracking.

```sql
CREATE TABLE users (
    phone_number TEXT PRIMARY KEY,           -- User's phone number (unique identifier)
    tier TEXT DEFAULT 'free',               -- User tier: free, premium, enterprise
    created_at TEXT DEFAULT (datetime('now')), -- Account creation timestamp
    last_active TEXT DEFAULT (datetime('now')), -- Last activity timestamp
    total_requests INTEGER DEFAULT 0,        -- Total requests made by user
    monthly_requests INTEGER DEFAULT 0,      -- Current month request count
    rate_limit_reset TEXT                   -- Next rate limit reset timestamp
);

-- Indexes for performance
CREATE INDEX idx_users_last_active ON users(last_active);
CREATE INDEX idx_users_tier ON users(tier);
```

**Sample Data:**
```sql
INSERT INTO users VALUES 
('+1234567890', 'premium', '2025-01-01 10:00:00', '2025-07-19 12:00:00', 45, 15, NULL),
('+1987654321', 'free', '2025-01-15 14:30:00', '2025-07-19 10:30:00', 23, 8, NULL);
```

#### **tasks** Table
Complete task execution history and analytics.

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Unique task identifier
    user_phone TEXT,                        -- Foreign key to users.phone_number
    category TEXT,                          -- Task category: coding, debug, design, etc.
    complexity_score REAL,                  -- AI-calculated complexity (0.0-1.0)
    priority TEXT,                          -- Task priority: low, medium, high, urgent
    processing_time REAL,                   -- Processing time in seconds
    success INTEGER DEFAULT 1,              -- Success flag (1=success, 0=failure)
    created_at TEXT DEFAULT (datetime('now')), -- Task creation timestamp
    completed_at TEXT,                      -- Task completion timestamp
    tokens_used INTEGER DEFAULT 0,          -- AI tokens consumed
    request_text TEXT,                      -- Original user request
    response_text TEXT,                     -- AI response (optional)
    task_hash TEXT UNIQUE,                  -- Unique task hash for deduplication
    FOREIGN KEY (user_phone) REFERENCES users (phone_number)
);

-- Performance indexes
CREATE INDEX idx_tasks_user_phone ON tasks(user_phone);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_tasks_category ON tasks(category);
CREATE INDEX idx_tasks_success ON tasks(success);
```

**Categories:**
- `coding`: Programming tasks, code generation
- `debug`: Error analysis, troubleshooting
- `design`: UI/UX design, architecture
- `documentation`: Writing docs, guides
- `analysis`: Data analysis, research
- `general`: General questions, conversations

#### **error_logs** Table
System error tracking and debugging.

```sql
CREATE TABLE error_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Unique error identifier
    timestamp TEXT DEFAULT (datetime('now')), -- Error timestamp
    error_type TEXT,                        -- Error classification
    error_message TEXT,                     -- Detailed error message
    user_phone TEXT,                        -- Associated user (if applicable)
    task_id INTEGER,                        -- Associated task (if applicable)
    request_text TEXT,                      -- Request that caused error
    FOREIGN KEY (task_id) REFERENCES tasks (id)
);

-- Index for performance
CREATE INDEX idx_error_logs_timestamp ON error_logs(timestamp);
CREATE INDEX idx_error_logs_type ON error_logs(error_type);
```

**Error Types:**
- `API_ERROR`: External API failures
- `VALIDATION_ERROR`: Input validation failures
- `TIMEOUT_ERROR`: Processing timeouts
- `ROUTING_ERROR`: Task routing failures
- `DATABASE_ERROR`: Database operation failures

#### **system_metrics** Table
Real-time system performance tracking.

```sql
CREATE TABLE system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Unique metric identifier
    metric_name TEXT,                       -- Metric name/type
    metric_value REAL,                      -- Metric value
    timestamp TEXT DEFAULT (datetime('now')), -- Measurement timestamp
    metadata TEXT                           -- Additional metric data (JSON)
);

-- Index for time-series queries
CREATE INDEX idx_system_metrics_timestamp ON system_metrics(timestamp);
CREATE INDEX idx_system_metrics_name ON system_metrics(metric_name);
```

**Metric Types:**
- `processing_time`: Task processing duration
- `success_rate`: Task success percentage
- `memory_usage`: System memory consumption
- `cpu_usage`: CPU utilization percentage
- `active_users`: Current active user count

#### **db_version** Table
Database schema version tracking.

```sql
CREATE TABLE db_version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Version record ID
    version INTEGER NOT NULL,               -- Schema version number
    updated_at TEXT DEFAULT (datetime('now')), -- Migration timestamp
    migration_notes TEXT                    -- Migration description
);
```

#### **notification_preferences** Table
User notification settings (added in migration v2).

```sql
CREATE TABLE notification_preferences (
    phone_number TEXT PRIMARY KEY,          -- User phone number
    email_notifications BOOLEAN DEFAULT 1,  -- Email notifications enabled
    sms_notifications BOOLEAN DEFAULT 1,    -- SMS notifications enabled
    task_completion_alerts BOOLEAN DEFAULT 1, -- Task completion alerts
    system_alerts BOOLEAN DEFAULT 1,        -- System alerts enabled
    updated_at TEXT DEFAULT (datetime('now')), -- Last update timestamp
    FOREIGN KEY (phone_number) REFERENCES users (phone_number)
);
```

---

### **notifications.db Schema**

#### **notification_templates** Table
Reusable notification message templates.

```sql
CREATE TABLE notification_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Template ID
    name TEXT UNIQUE,                       -- Template name/identifier
    type TEXT,                             -- Notification type: sms, email, slack
    subject_template TEXT,                  -- Subject template with variables
    body_template TEXT,                     -- Body template with variables
    variables TEXT,                         -- JSON array of variable names
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Creation timestamp
);
```

#### **notification_history** Table
Complete notification delivery log.

```sql
CREATE TABLE notification_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- History record ID
    recipient TEXT,                         -- Recipient (phone, email, channel)
    type TEXT,                             -- Notification type
    subject TEXT,                          -- Message subject/title
    body TEXT,                             -- Message content
    status TEXT,                           -- sent, failed, pending
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Send timestamp
    delivery_status TEXT,                   -- delivered, bounced, opened
    error_message TEXT                      -- Error details if failed
);
```

#### **user_preferences** Table
Per-user notification preferences.

```sql
CREATE TABLE user_preferences (
    user_phone TEXT PRIMARY KEY,           -- User phone number
    email TEXT,                            -- User's email address
    sms_enabled BOOLEAN DEFAULT 1,         -- SMS notifications enabled
    email_enabled BOOLEAN DEFAULT 0,       -- Email notifications enabled
    webhook_url TEXT,                      -- Custom webhook URL
    slack_webhook TEXT,                    -- Personal Slack webhook
    preferred_channels TEXT,               -- JSON array of preferred channels
    quiet_hours_start INTEGER,             -- Quiet hours start (0-23)
    quiet_hours_end INTEGER,               -- Quiet hours end (0-23)
    timezone TEXT DEFAULT 'UTC'           -- User's timezone
);
```

#### **alert_rules** Table
System alert configuration and rules.

```sql
CREATE TABLE alert_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Rule ID
    name TEXT,                             -- Rule name/description
    condition_type TEXT,                   -- error_rate, response_time, usage
    condition_value TEXT,                  -- Threshold value
    alert_level TEXT,                      -- info, warning, critical
    notification_channels TEXT,            -- JSON array of channels
    enabled BOOLEAN DEFAULT 1,             -- Rule enabled/disabled
    cooldown_minutes INTEGER DEFAULT 60,   -- Minimum time between alerts
    last_triggered TIMESTAMP              -- Last trigger timestamp
);
```

---

## 🔄 **Migration System**

### **Version Tracking**

The system automatically tracks database schema versions and applies migrations as needed.

**Current Version**: 2
- **Version 1**: Initial schema creation
- **Version 2**: Performance indexes and notification preferences

### **Migration Process**

```python
def _run_migrations(self):
    """Run database migrations based on current version"""
    current_version = self._get_database_version()
    target_version = 2  # Update when adding new migrations
    
    if current_version < 2:
        # Migration to version 2
        self._add_performance_indexes()
        self._create_notification_preferences_table()
        self._update_database_version(2, "Added performance indexes and notification preferences")
```

### **Adding New Migrations**

To add a new migration:

1. **Increment target version** in `_run_migrations()`
2. **Add migration logic** for the new version
3. **Update version** with `_update_database_version()`
4. **Test migration** on sample data

Example:
```python
# Migration to version 3
if current_version < 3:
    try:
        cursor.execute("""
            ALTER TABLE users ADD COLUMN 
            email_address TEXT DEFAULT NULL
        """)
        
        cursor.execute("""
            CREATE TABLE user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_phone TEXT,
                session_token TEXT,
                expires_at TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        
        conn.commit()
        self._update_database_version(3, "Added email addresses and user sessions")
        
    except Exception as e:
        logger.warning(f"Migration to version 3 failed: {e}")
```

---

## 📊 **Database Queries**

### **Common Analytics Queries**

#### **User Statistics**
```sql
-- Total users by tier
SELECT tier, COUNT(*) as user_count 
FROM users 
GROUP BY tier;

-- Active users (last 24 hours)
SELECT COUNT(DISTINCT user_phone) as active_users
FROM tasks 
WHERE created_at >= datetime('now', '-24 hours');

-- User growth over time
SELECT 
    DATE(created_at) as date,
    COUNT(*) as new_users,
    SUM(COUNT(*)) OVER (ORDER BY DATE(created_at)) as total_users
FROM users 
GROUP BY DATE(created_at)
ORDER BY date;
```

#### **Task Analytics**
```sql
-- Tasks by category (last 30 days)
SELECT 
    category,
    COUNT(*) as task_count,
    AVG(complexity_score) as avg_complexity,
    AVG(processing_time) as avg_time,
    COUNT(*) FILTER (WHERE success = 1) * 100.0 / COUNT(*) as success_rate
FROM tasks 
WHERE created_at >= datetime('now', '-30 days')
GROUP BY category
ORDER BY task_count DESC;

-- Performance trends (daily)
SELECT 
    DATE(created_at) as date,
    COUNT(*) as task_count,
    AVG(processing_time) as avg_processing_time,
    COUNT(*) FILTER (WHERE success = 1) * 100.0 / COUNT(*) as success_rate
FROM tasks 
WHERE created_at >= datetime('now', '-7 days')
GROUP BY DATE(created_at)
ORDER BY date;

-- Top users by activity
SELECT 
    u.phone_number,
    u.tier,
    COUNT(t.id) as total_tasks,
    AVG(t.processing_time) as avg_time,
    MAX(t.created_at) as last_task
FROM users u
LEFT JOIN tasks t ON u.phone_number = t.user_phone
GROUP BY u.phone_number
ORDER BY total_tasks DESC
LIMIT 10;
```

#### **Error Analysis**
```sql
-- Error rate by type
SELECT 
    error_type,
    COUNT(*) as error_count,
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM error_logs) as percentage
FROM error_logs 
WHERE timestamp >= datetime('now', '-24 hours')
GROUP BY error_type
ORDER BY error_count DESC;

-- Errors by user
SELECT 
    user_phone,
    COUNT(*) as error_count,
    COUNT(DISTINCT error_type) as error_types
FROM error_logs 
WHERE user_phone IS NOT NULL
GROUP BY user_phone
ORDER BY error_count DESC;
```

### **Performance Optimization Queries**

#### **Index Usage Analysis**
```sql
-- Check index usage
EXPLAIN QUERY PLAN 
SELECT * FROM tasks 
WHERE user_phone = '+1234567890' 
AND created_at >= datetime('now', '-7 days');

-- Find slow queries (enable query planner)
PRAGMA query_planner = ON;
```

#### **Database Statistics**
```sql
-- Table sizes
SELECT 
    name as table_name,
    COUNT(*) as row_count
FROM sqlite_master 
WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
GROUP BY name;

-- Database file size
SELECT page_count * page_size as size_bytes 
FROM pragma_page_count(), pragma_page_size();
```

---

## 🛠️ **Database Administration**

### **Backup Procedures**

#### **Automated Backups**
```bash
# Daily backup script (runs in container)
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/app/data/backups"
mkdir -p $BACKUP_DIR

# Backup main database
sqlite3 /app/data/task_analytics.db ".backup $BACKUP_DIR/task_analytics_$DATE.db"

# Backup notifications database
sqlite3 /app/data/notifications.db ".backup $BACKUP_DIR/notifications_$DATE.db"

# Compress backups
gzip $BACKUP_DIR/task_analytics_$DATE.db
gzip $BACKUP_DIR/notifications_$DATE.db

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

#### **Manual Backup**
```bash
# Create immediate backup
docker-compose exec web sqlite3 /app/data/task_analytics.db ".backup /app/data/backup_$(date +%Y%m%d).db"

# Export to SQL
docker-compose exec web sqlite3 /app/data/task_analytics.db ".dump" > backup.sql
```

### **Database Maintenance**

#### **Vacuum and Optimize**
```sql
-- Rebuild database to reclaim space
VACUUM;

-- Update table statistics
ANALYZE;

-- Check database integrity
PRAGMA integrity_check;

-- Optimize specific table
VACUUM users;
```

#### **Monitoring Queries**
```sql
-- Database health check
SELECT 
    'task_analytics.db' as database,
    COUNT(*) as table_count
FROM sqlite_master 
WHERE type = 'table';

-- Check for orphaned records
SELECT COUNT(*) as orphaned_tasks
FROM tasks t
LEFT JOIN users u ON t.user_phone = u.phone_number
WHERE u.phone_number IS NULL;

-- Check index efficiency
SELECT 
    name,
    tbl_name,
    sql
FROM sqlite_master 
WHERE type = 'index' AND tbl_name IN ('users', 'tasks', 'error_logs');
```

### **Data Cleanup**

#### **Automated Cleanup Procedures**
```python
def cleanup_old_data():
    """Clean up old data to maintain performance"""
    conn = sqlite3.connect('/app/data/task_analytics.db')
    cursor = conn.cursor()
    
    # Remove error logs older than 90 days
    cursor.execute("""
        DELETE FROM error_logs 
        WHERE timestamp < datetime('now', '-90 days')
    """)
    
    # Remove system metrics older than 30 days
    cursor.execute("""
        DELETE FROM system_metrics 
        WHERE timestamp < datetime('now', '-30 days')
    """)
    
    # Archive completed tasks older than 1 year
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks_archive AS 
        SELECT * FROM tasks WHERE 1=0
    """)
    
    cursor.execute("""
        INSERT INTO tasks_archive 
        SELECT * FROM tasks 
        WHERE completed_at < datetime('now', '-365 days')
    """)
    
    cursor.execute("""
        DELETE FROM tasks 
        WHERE completed_at < datetime('now', '-365 days')
    """)
    
    conn.commit()
    conn.close()
```

---

## 📈 **Performance Tuning**

### **Query Optimization**

#### **Essential Indexes**
```sql
-- User activity queries
CREATE INDEX idx_users_last_active ON users(last_active);
CREATE INDEX idx_users_tier ON users(tier);

-- Task queries
CREATE INDEX idx_tasks_user_phone ON tasks(user_phone);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_tasks_category ON tasks(category);
CREATE INDEX idx_tasks_success ON tasks(success);

-- Error log queries
CREATE INDEX idx_error_logs_timestamp ON error_logs(timestamp);
CREATE INDEX idx_error_logs_type ON error_logs(error_type);

-- System metrics queries
CREATE INDEX idx_system_metrics_timestamp ON system_metrics(timestamp);
CREATE INDEX idx_system_metrics_name ON system_metrics(metric_name);
```

#### **Composite Indexes**
```sql
-- User activity with success filter
CREATE INDEX idx_tasks_user_success_date ON tasks(user_phone, success, created_at);

-- Category performance analysis
CREATE INDEX idx_tasks_category_date ON tasks(category, created_at);
```

### **SQLite Configuration**

#### **Performance Settings**
```sql
-- Enable WAL mode for better concurrency
PRAGMA journal_mode = WAL;

-- Increase cache size (in pages)
PRAGMA cache_size = 10000;

-- Synchronous mode for better performance
PRAGMA synchronous = NORMAL;

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Set busy timeout
PRAGMA busy_timeout = 30000;
```

### **Connection Pool Management**

```python
import sqlite3
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._configure_connection()
    
    def _configure_connection(self):
        """Configure SQLite connection for optimal performance"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = 10000")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 30000")
        conn.close()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Database Locked Errors**
```bash
# Check for processes holding database lock
lsof /app/data/task_analytics.db

# Fix locked database
sqlite3 /app/data/task_analytics.db "BEGIN IMMEDIATE; ROLLBACK;"
```

#### **Corruption Recovery**
```sql
-- Check database integrity
PRAGMA integrity_check;

-- Recover from corruption
.recover /app/data/task_analytics_recovered.db
```

#### **Performance Issues**
```sql
-- Find missing indexes
EXPLAIN QUERY PLAN SELECT * FROM tasks WHERE user_phone = ?;

-- Check table statistics
SELECT * FROM sqlite_stat1;

-- Update statistics
ANALYZE;
```

### **Monitoring Scripts**

#### **Database Health Check**
```bash
#!/bin/bash
# Database health monitoring script

DB_PATH="/app/data/task_analytics.db"
LOG_FILE="/app/logs/database_health.log"

echo "$(date): Starting database health check" >> $LOG_FILE

# Check database accessibility
if sqlite3 $DB_PATH "SELECT 1;" > /dev/null 2>&1; then
    echo "$(date): Database accessible" >> $LOG_FILE
else
    echo "$(date): ERROR - Database not accessible" >> $LOG_FILE
    exit 1
fi

# Check integrity
INTEGRITY=$(sqlite3 $DB_PATH "PRAGMA integrity_check;")
if [ "$INTEGRITY" = "ok" ]; then
    echo "$(date): Database integrity OK" >> $LOG_FILE
else
    echo "$(date): ERROR - Database integrity issues: $INTEGRITY" >> $LOG_FILE
fi

# Check size
SIZE=$(du -h $DB_PATH | cut -f1)
echo "$(date): Database size: $SIZE" >> $LOG_FILE

# Check record counts
USERS=$(sqlite3 $DB_PATH "SELECT COUNT(*) FROM users;")
TASKS=$(sqlite3 $DB_PATH "SELECT COUNT(*) FROM tasks;")
ERRORS=$(sqlite3 $DB_PATH "SELECT COUNT(*) FROM error_logs;")

echo "$(date): Records - Users: $USERS, Tasks: $TASKS, Errors: $ERRORS" >> $LOG_FILE
```

---

## 🔮 **Future Enhancements**

### **Planned Database Features**

1. **Sharding Support**: Horizontal partitioning for large datasets
2. **Read Replicas**: Read-only database replicas for analytics
3. **Data Archiving**: Automated archiving of historical data
4. **Real-time Sync**: Multi-instance database synchronization
5. **Advanced Analytics**: Time-series data optimization

### **Migration to PostgreSQL**

For high-scale deployments, consider migrating to PostgreSQL:

```python
# Database abstraction layer for future migration
class DatabaseAdapter:
    def __init__(self, db_type='sqlite', connection_string=None):
        if db_type == 'sqlite':
            self.engine = SQLiteEngine(connection_string)
        elif db_type == 'postgresql':
            self.engine = PostgreSQLEngine(connection_string)
    
    def execute_query(self, query, params=None):
        return self.engine.execute(query, params)
```

### **Analytics Warehouse**

For advanced analytics, consider data warehouse integration:

- **Time-series databases**: InfluxDB for metrics
- **Data lakes**: S3 + Spark for big data analytics
- **Business intelligence**: Grafana for visualization

---

This comprehensive database documentation covers all aspects of the Enhanced SMS-to-Cursor AI Agent's data persistence layer. For additional support, refer to the source code or contact the development team. 