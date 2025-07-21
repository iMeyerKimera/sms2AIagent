# 🗄️ Database Architecture & Management

**Complete database schema, architecture, and management guide for SMS-to-AI Agent**

---

## 📋 **Overview**

The SMS-to-AI Agent uses **PostgreSQL** as the primary database with the following key features:
- **Django ORM** for database operations
- **Automated migrations** for schema changes
- **Indexing strategies** for performance
- **Backup and recovery** procedures
- **Multi-tier user management**

---

## 🏗️ **Database Architecture**

### **Core Schema Design**

```sql
-- Users Table: Primary user management
CREATE TABLE users (
    phone_number VARCHAR(17) PRIMARY KEY,  -- E.164 format
    tier VARCHAR(20) DEFAULT 'free',       -- User subscription tier
    email VARCHAR(255),                    -- Optional email
    full_name VARCHAR(255),                -- Optional full name
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW(),
    total_requests INTEGER DEFAULT 0,
    monthly_requests INTEGER DEFAULT 0,
    rate_limit_reset TIMESTAMP DEFAULT NOW(),
    timezone VARCHAR(50) DEFAULT 'UTC',
    preferences JSONB DEFAULT '{}'
);

-- Tasks Table: SMS processing tasks
CREATE TABLE tasks (
    id BIGSERIAL PRIMARY KEY,
    user_phone VARCHAR(17) REFERENCES users(phone_number),
    sms_content TEXT NOT NULL,
    ai_response TEXT,
    category VARCHAR(50) DEFAULT 'general',
    processing_time FLOAT DEFAULT 0.0,
    tokens_used INTEGER DEFAULT 0,
    complexity_score FLOAT DEFAULT 1.0,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Error Logs Table: System error tracking
CREATE TABLE error_logs (
    id BIGSERIAL PRIMARY KEY,
    user_phone VARCHAR(17) REFERENCES users(phone_number),
    task_id BIGINT REFERENCES tasks(id),
    error_type VARCHAR(50) NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'
);
```

---

## 📊 **Data Models**

### **User Model**
**Purpose**: Primary user management and tier tracking

**Fields**:
- `phone_number` (PK): E.164 format phone number
- `tier`: User subscription level (free/premium/enterprise)
- `email`: Optional email address
- `full_name`: Optional full name
- `created_at`: Account creation timestamp
- `last_active`: Last activity timestamp
- `total_requests`: Lifetime request count
- `monthly_requests`: Current month request count
- `rate_limit_reset`: When rate limit window resets
- `timezone`: User timezone preference
- `preferences`: JSON preferences storage

**Relationships**:
- One-to-many with Tasks
- One-to-many with ErrorLogs

### **Task Model**
**Purpose**: Track SMS processing tasks and AI responses

**Fields**:
- `id` (PK): Auto-incrementing task ID
- `user_phone` (FK): Reference to user
- `sms_content`: Original SMS message content
- `ai_response`: Generated AI response
- `category`: Task category (general/coding/debug/etc.)
- `processing_time`: Time taken to process (seconds)
- `tokens_used`: AI tokens consumed
- `complexity_score`: Task complexity rating (0.0-1.0)
- `success`: Whether task completed successfully
- `error_message`: Error details if failed
- `created_at`: Task creation timestamp
- `completed_at`: Task completion timestamp
- `metadata`: Additional task metadata (JSON)

**Relationships**:
- Many-to-one with User
- One-to-many with ErrorLogs

### **ErrorLog Model**
**Purpose**: System error tracking and debugging

**Fields**:
- `id` (PK): Auto-incrementing error ID
- `user_phone` (FK): Associated user (optional)
- `task_id` (FK): Associated task (optional)
- `error_type`: Error category
- `error_message`: Error description
- `stack_trace`: Full stack trace for debugging
- `timestamp`: When error occurred
- `resolved`: Whether error has been addressed
- `metadata`: Additional error context (JSON)

---

## 🔍 **Indexing Strategy**

### **Performance Indexes**

```sql
-- User-related indexes
CREATE INDEX idx_users_tier ON users(tier);
CREATE INDEX idx_users_last_active ON users(last_active);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Task-related indexes
CREATE INDEX idx_tasks_user_phone_created ON tasks(user_phone, created_at DESC);
CREATE INDEX idx_tasks_category_created ON tasks(category, created_at DESC);
CREATE INDEX idx_tasks_success_created ON tasks(success, created_at DESC);
CREATE INDEX idx_tasks_completed_at ON tasks(completed_at);

-- Error log indexes
CREATE INDEX idx_error_logs_type_timestamp ON error_logs(error_type, timestamp DESC);
CREATE INDEX idx_error_logs_user_timestamp ON error_logs(user_phone, timestamp DESC);
CREATE INDEX idx_error_logs_resolved_timestamp ON error_logs(resolved, timestamp DESC);

-- Analytics indexes
CREATE INDEX idx_tasks_created_at_category ON tasks(created_at, category);
CREATE INDEX idx_tasks_created_at_success ON tasks(created_at, success);
```

### **Query Optimization**

```sql
-- User activity analysis
EXPLAIN ANALYZE 
SELECT COUNT(*) FROM tasks 
WHERE user_phone = '+1234567890' 
AND created_at >= NOW() - INTERVAL '30 days';

-- Category performance analysis
EXPLAIN ANALYZE
SELECT 
    category,
    COUNT(*) as task_count,
    AVG(processing_time) as avg_time,
    AVG(CASE WHEN success THEN 1 ELSE 0 END) * 100 as success_rate
FROM tasks 
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY category
ORDER BY task_count DESC;
```

---

## 🚀 **Database Operations**

### **Common Queries**

#### **User Management**
```sql
-- Get user statistics
SELECT 
    tier,
    COUNT(*) as user_count,
    AVG(total_requests) as avg_requests
FROM users 
GROUP BY tier;

-- Active users in last 24 hours
SELECT COUNT(*) 
FROM users 
WHERE last_active >= NOW() - INTERVAL '24 hours';

-- Top users by activity
SELECT 
    phone_number,
    tier,
    total_requests,
    last_active
FROM users 
ORDER BY total_requests DESC 
LIMIT 10;
```

#### **Task Analytics**
```sql
-- Daily task volume
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_tasks,
    COUNT(CASE WHEN success THEN 1 END) as successful_tasks,
    AVG(processing_time) as avg_processing_time
FROM tasks 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date;

-- Category breakdown
SELECT 
    category,
    COUNT(*) as task_count,
    AVG(complexity_score) as avg_complexity,
    AVG(processing_time) as avg_time
FROM tasks 
GROUP BY category 
ORDER BY task_count DESC;
```

#### **Error Analysis**
```sql
-- Error trends
SELECT 
    error_type,
    COUNT(*) as error_count,
    COUNT(CASE WHEN resolved THEN 1 END) as resolved_count
FROM error_logs 
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY error_type 
ORDER BY error_count DESC;

-- Unresolved errors
SELECT 
    error_type,
    error_message,
    timestamp,
    user_phone
FROM error_logs 
WHERE resolved = FALSE 
ORDER BY timestamp DESC;
```

---

## 🔧 **Database Management**

### **Migrations**

#### **Django Migration Commands**
```bash
# Create migration
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate

# Show migration status
docker-compose exec web python manage.py showmigrations

# Migrate specific app
docker-compose exec web python manage.py migrate core

# Rollback migration
docker-compose exec web python manage.py migrate core 0001
```

#### **Custom Migration Example**
```python
# migrations/0002_add_user_preferences.py
from django.db import migrations, models
import django.contrib.postgres.fields

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='preferences',
            field=models.JSONField(default=dict, blank=True),
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_users_preferences_gin ON core_user USING gin (preferences);",
            reverse_sql="DROP INDEX IF EXISTS idx_users_preferences_gin;"
        ),
    ]
```

### **Database Maintenance**

#### **Performance Monitoring**
```sql
-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index usage statistics
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;

-- Database connections
SELECT 
    datname,
    numbackends,
    xact_commit,
    xact_rollback,
    blks_read,
    blks_hit
FROM pg_stat_database;
```

#### **Cleanup Operations**
```sql
-- Analyze tables for query planner
ANALYZE;

-- Update table statistics
VACUUM ANALYZE users;
VACUUM ANALYZE tasks;
VACUUM ANALYZE error_logs;

-- Remove old error logs (keep 90 days)
DELETE FROM error_logs 
WHERE timestamp < NOW() - INTERVAL '90 days' 
AND resolved = TRUE;

-- Archive old completed tasks (keep 1 year)
CREATE TABLE tasks_archive AS 
SELECT * FROM tasks 
WHERE completed_at < NOW() - INTERVAL '1 year';

DELETE FROM tasks 
WHERE completed_at < NOW() - INTERVAL '1 year';
```

---

## 💾 **Backup & Recovery**

### **Backup Strategies**

#### **Automated Daily Backup**
```bash
#!/bin/bash
# backup_database.sh

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATABASE="sms_agent_db"
USER="sms_agent"

# Create backup
pg_dump -h database -U $USER -d $DATABASE > $BACKUP_DIR/backup_$TIMESTAMP.sql

# Compress backup
gzip $BACKUP_DIR/backup_$TIMESTAMP.sql

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: backup_$TIMESTAMP.sql.gz"
```

#### **Point-in-Time Recovery Setup**
```bash
# Enable WAL archiving in postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /backups/wal/%f'
max_wal_senders = 3
```

### **Recovery Procedures**

#### **Full Database Restore**
```bash
# Stop application
docker-compose down

# Remove existing data
docker volume rm sms2aiagent_postgres_data

# Start database
docker-compose up -d database

# Wait for database to be ready
sleep 30

# Restore backup
gunzip -c backup_20240101_120000.sql.gz | \
docker-compose exec -T database psql -U sms_agent -d sms_agent_db

# Start application
docker-compose up -d
```

#### **Selective Data Recovery**
```sql
-- Restore specific table from backup
DROP TABLE IF EXISTS tasks_temp;
CREATE TABLE tasks_temp AS SELECT * FROM tasks WHERE 1=0;

-- Import from backup file (manual process)
\copy tasks_temp FROM 'tasks_backup.csv' CSV HEADER;

-- Verify data
SELECT COUNT(*) FROM tasks_temp;

-- Replace current data
BEGIN;
TRUNCATE tasks;
INSERT INTO tasks SELECT * FROM tasks_temp;
DROP TABLE tasks_temp;
COMMIT;
```

---

## 📈 **Performance Optimization**

### **PostgreSQL Configuration**

#### **Memory Settings**
```conf
# postgresql.conf optimizations
shared_buffers = 256MB                    # 25% of total RAM
effective_cache_size = 1GB                # 75% of total RAM
work_mem = 4MB                           # Per query memory
maintenance_work_mem = 64MB              # Maintenance operations
```

#### **Connection Settings**
```conf
max_connections = 100                    # Adjust based on usage
shared_preload_libraries = 'pg_stat_statements'
track_activity_query_size = 2048
```

### **Query Optimization**

#### **Slow Query Analysis**
```sql
-- Enable query statistics
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slow queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Reset statistics
SELECT pg_stat_statements_reset();
```

#### **Index Optimization**
```sql
-- Find missing indexes
SELECT 
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch,
    seq_tup_read / seq_scan as avg_seq_read
FROM pg_stat_user_tables 
WHERE seq_scan > 0 
ORDER BY seq_tup_read DESC;

-- Unused indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan
FROM pg_stat_user_indexes 
WHERE idx_scan = 0;
```

---

## 🔐 **Security & Access Control**

### **Database Security**

#### **User Permissions**
```sql
-- Application user (limited permissions)
CREATE USER sms_agent WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE sms_agent_db TO sms_agent;
GRANT USAGE ON SCHEMA public TO sms_agent;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sms_agent;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO sms_agent;

-- Read-only analytics user
CREATE USER analytics_readonly WITH PASSWORD 'analytics_password';
GRANT CONNECT ON DATABASE sms_agent_db TO analytics_readonly;
GRANT USAGE ON SCHEMA public TO analytics_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_readonly;
```

#### **Row Level Security**
```sql
-- Enable RLS for sensitive operations
ALTER TABLE error_logs ENABLE ROW LEVEL SECURITY;

-- Policy for application user
CREATE POLICY app_user_policy ON error_logs
FOR ALL TO sms_agent
USING (TRUE);

-- Policy for analytics user (no sensitive data)
CREATE POLICY analytics_policy ON error_logs
FOR SELECT TO analytics_readonly
USING (resolved = TRUE);
```

---

## 📊 **Monitoring & Alerts**

### **Database Monitoring**

#### **Key Metrics to Monitor**
```sql
-- Connection count
SELECT COUNT(*) FROM pg_stat_activity;

-- Database size
SELECT pg_size_pretty(pg_database_size('sms_agent_db'));

-- Table sizes
SELECT 
    relname,
    pg_size_pretty(pg_total_relation_size(relid))
FROM pg_stat_user_tables 
ORDER BY pg_total_relation_size(relid) DESC;

-- Lock monitoring
SELECT 
    mode,
    locktype,
    database,
    relation,
    page,
    tuple,
    virtualxid,
    transactionid,
    pid,
    granted
FROM pg_locks;
```

#### **Automated Health Checks**
```bash
#!/bin/bash
# db_health_check.sh

# Check database connectivity
if ! docker-compose exec database pg_isready -U sms_agent; then
    echo "ALERT: Database not responding"
    exit 1
fi

# Check disk space
DISK_USAGE=$(docker-compose exec database df -h /var/lib/postgresql/data | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "ALERT: Database disk usage at ${DISK_USAGE}%"
fi

# Check connection count
CONNECTIONS=$(docker-compose exec database psql -U sms_agent -d sms_agent_db -t -c "SELECT COUNT(*) FROM pg_stat_activity;")
if [ $CONNECTIONS -gt 80 ]; then
    echo "ALERT: High connection count: $CONNECTIONS"
fi

echo "Database health check completed successfully"
```

---

## 🎯 **Best Practices**

### **Development**
- ✅ **Use migrations** for all schema changes
- ✅ **Test migrations** on staging before production
- ✅ **Add indexes** for frequently queried columns
- ✅ **Use JSONB** for flexible schema needs
- ✅ **Validate data** at application and database level

### **Production**
- ✅ **Monitor performance** regularly
- ✅ **Backup daily** with automated verification
- ✅ **Use connection pooling** for better performance
- ✅ **Enable query logging** for slow queries
- ✅ **Set up replication** for high availability

### **Security**
- ✅ **Use strong passwords** for database users
- ✅ **Limit user permissions** to minimum required
- ✅ **Enable SSL** for database connections
- ✅ **Regular security updates** for PostgreSQL
- ✅ **Audit database access** regularly

---

**🎉 Your database is now optimized for performance, reliability, and security!**

**See also: [Production Guide](../operations/PRODUCTION.md) and [Troubleshooting Guide](../operations/TROUBLESHOOTING.md)** 