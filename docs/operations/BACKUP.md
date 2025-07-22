# 💾 Backup & Recovery Guide

**Comprehensive backup and disaster recovery procedures for SMS-to-AI Agent**

---

## 📋 **Overview**

This guide covers backup strategies, automated backup procedures, disaster recovery planning, and data restoration processes to ensure your SMS-to-AI Agent system can recover from various failure scenarios.

---

## 🎯 **Backup Strategy**

### **What to Backup**

#### **Critical Data**
- **PostgreSQL Database**: User data, tasks, error logs
- **Configuration Files**: Environment variables, settings
- **Application Code**: Custom modifications, extensions
- **Static Files**: Uploads, generated content
- **SSL Certificates**: Security certificates
- **Logs**: Application and system logs

#### **Backup Types**
- **Full Backup**: Complete system snapshot
- **Incremental Backup**: Changes since last backup
- **Differential Backup**: Changes since last full backup
- **Point-in-Time**: Continuous backup for specific recovery

---

## 🗄️ **Database Backup**

### **PostgreSQL Backup Scripts**

#### **Daily Full Backup**
```bash
#!/bin/bash
# scripts/backup_database.sh

# Configuration
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATABASE="sms_agent_db"
USER="sms_agent"
RETENTION_DAYS=7

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
BACKUP_FILE="$BACKUP_DIR/sms_agent_backup_$TIMESTAMP.sql"
pg_dump -h database -U $USER -d $DATABASE > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Verify backup
if [ -f "${BACKUP_FILE}.gz" ]; then
    echo "Backup created successfully: ${BACKUP_FILE}.gz"
    
    # Log backup info
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
    echo "$(date): Backup completed - Size: $BACKUP_SIZE" >> $BACKUP_DIR/backup.log
else
    echo "ERROR: Backup failed!"
    exit 1
fi

# Clean old backups
find $BACKUP_DIR -name "sms_agent_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Clean old logs
find $BACKUP_DIR -name "backup.log" -size +10M -exec truncate -s 1M {} \;

echo "Database backup completed successfully"
```

#### **Incremental Backup with WAL**
```bash
#!/bin/bash
# scripts/wal_backup.sh

# PostgreSQL WAL archiving configuration
# Add to postgresql.conf:
# wal_level = replica
# archive_mode = on
# archive_command = 'cp %p /backups/wal/%f'
# max_wal_senders = 3

WAL_DIR="/backups/wal"
RETENTION_HOURS=72

# Create WAL directory
mkdir -p $WAL_DIR

# Clean old WAL files (keep 72 hours)
find $WAL_DIR -type f -mtime +3 -delete

echo "WAL backup maintenance completed"
```

### **Automated Backup Setup**

#### **Crontab Configuration**
```bash
# Add to crontab (crontab -e)

# Daily full backup at 2 AM
0 2 * * * /path/to/sms2AIagent/scripts/backup_database.sh >> /var/log/backup.log 2>&1

# Hourly WAL cleanup
0 * * * * /path/to/sms2AIagent/scripts/wal_backup.sh >> /var/log/wal_backup.log 2>&1

# Weekly system backup
0 3 * * 0 /path/to/sms2AIagent/scripts/system_backup.sh >> /var/log/system_backup.log 2>&1
```

#### **Docker-Based Backup**
```yaml
# docker-compose.backup.yml
version: '3.8'

services:
  backup:
    image: postgres:15
    volumes:
      - ./backups:/backups
      - ./scripts:/scripts
    environment:
      - PGPASSWORD=${DB_PASSWORD}
    command: /scripts/backup_database.sh
    profiles:
      - backup
    depends_on:
      - database

  # Backup scheduler
  backup-scheduler:
    image: alpine:latest
    volumes:
      - ./scripts:/scripts
      - ./backups:/backups
      - /var/run/docker.sock:/var/run/docker.sock
    command: |
      sh -c "
        apk add --no-cache docker-cli dcron
        echo '0 2 * * * cd /app && docker-compose -f docker-compose.yml -f docker-compose.backup.yml run --rm backup' | crontab -
        crond -f
      "
    profiles:
      - scheduler
```

---

## 🗂️ **File System Backup**

### **Application Files Backup**

```bash
#!/bin/bash
# scripts/system_backup.sh

BACKUP_ROOT="/backups/system"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
APP_DIR="/app"

# Create backup directory
mkdir -p $BACKUP_ROOT

# Create system backup
tar -czf "$BACKUP_ROOT/system_backup_$TIMESTAMP.tar.gz" \
    --exclude='*.log' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='node_modules' \
    $APP_DIR

# Backup configuration
tar -czf "$BACKUP_ROOT/config_backup_$TIMESTAMP.tar.gz" \
    .env \
    docker-compose.yml \
    nginx/ \
    scripts/

# Backup logs separately
tar -czf "$BACKUP_ROOT/logs_backup_$TIMESTAMP.tar.gz" logs/

# Clean old system backups (keep 30 days)
find $BACKUP_ROOT -name "system_backup_*.tar.gz" -mtime +30 -delete
find $BACKUP_ROOT -name "config_backup_*.tar.gz" -mtime +30 -delete
find $BACKUP_ROOT -name "logs_backup_*.tar.gz" -mtime +7 -delete

echo "System backup completed"
```

### **Docker Volume Backup**

```bash
#!/bin/bash
# scripts/volume_backup.sh

VOLUMES="sms2aiagent_postgres_data sms2aiagent_redis_data"
BACKUP_DIR="/backups/volumes"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

for VOLUME in $VOLUMES; do
    echo "Backing up volume: $VOLUME"
    
    docker run --rm \
        -v $VOLUME:/source:ro \
        -v $BACKUP_DIR:/backup \
        alpine:latest \
        tar -czf /backup/${VOLUME}_${TIMESTAMP}.tar.gz -C /source .
    
    if [ $? -eq 0 ]; then
        echo "Volume $VOLUME backed up successfully"
    else
        echo "ERROR: Failed to backup volume $VOLUME"
    fi
done

# Clean old volume backups (keep 14 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +14 -delete

echo "Volume backup completed"
```

---

## ☁️ **Cloud Backup Integration**

### **AWS S3 Backup**

```bash
#!/bin/bash
# scripts/s3_backup.sh

# Configuration
S3_BUCKET="your-backup-bucket"
AWS_REGION="us-east-1"
LOCAL_BACKUP_DIR="/backups"

# Install AWS CLI if not present
if ! command -v aws &> /dev/null; then
    echo "AWS CLI not found. Installing..."
    pip install awscli
fi

# Sync backups to S3
aws s3 sync $LOCAL_BACKUP_DIR s3://$S3_BUCKET/sms-agent-backups/ \
    --region $AWS_REGION \
    --delete \
    --exclude "*.log"

if [ $? -eq 0 ]; then
    echo "Backup successfully uploaded to S3"
else
    echo "ERROR: Failed to upload backup to S3"
    exit 1
fi

# Set lifecycle policy for old backups
aws s3api put-bucket-lifecycle-configuration \
    --bucket $S3_BUCKET \
    --lifecycle-configuration file://s3-lifecycle-policy.json
```

### **S3 Lifecycle Policy**

```json
{
  "Rules": [
    {
      "ID": "BackupRetention",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        },
        {
          "Days": 365,
          "StorageClass": "DEEP_ARCHIVE"
        }
      ],
      "Expiration": {
        "Days": 2555
      }
    }
  ]
}
```

---

## 🔄 **Recovery Procedures**

### **Database Recovery**

#### **Full Database Restore**
```bash
#!/bin/bash
# scripts/restore_database.sh

BACKUP_FILE=$1
DATABASE="sms_agent_db"
USER="sms_agent"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Starting database restore from: $BACKUP_FILE"

# Stop application
echo "Stopping application..."
docker-compose down

# Start only database
echo "Starting database service..."
docker-compose up -d database

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 30

# Drop existing database and recreate
echo "Recreating database..."
docker-compose exec database psql -U $USER -c "DROP DATABASE IF EXISTS $DATABASE;"
docker-compose exec database psql -U $USER -c "CREATE DATABASE $DATABASE;"

# Restore from backup
echo "Restoring data..."
gunzip -c $BACKUP_FILE | docker-compose exec -T database psql -U $USER -d $DATABASE

if [ $? -eq 0 ]; then
    echo "Database restore completed successfully"
    
    # Start full application
    echo "Starting application..."
    docker-compose up -d
    
    echo "Recovery completed successfully"
else
    echo "ERROR: Database restore failed"
    exit 1
fi
```

#### **Point-in-Time Recovery**
```bash
#!/bin/bash
# scripts/pitr_restore.sh

BASE_BACKUP=$1
TARGET_TIME=$2
WAL_DIR="/backups/wal"

if [ -z "$BASE_BACKUP" ] || [ -z "$TARGET_TIME" ]; then
    echo "Usage: $0 <base_backup.sql.gz> <target_time>"
    echo "Example: $0 backup_20240120_020000.sql.gz '2024-01-20 14:30:00'"
    exit 1
fi

echo "Starting point-in-time recovery to: $TARGET_TIME"

# Stop application
docker-compose down

# Start database in recovery mode
cat > recovery.conf << EOF
restore_command = 'cp $WAL_DIR/%f %p'
recovery_target_time = '$TARGET_TIME'
recovery_target_action = 'promote'
EOF

# Mount recovery.conf and start database
docker-compose up -d database

echo "Point-in-time recovery initiated. Monitor logs for completion."
```

### **System Recovery**

#### **Complete System Restore**
```bash
#!/bin/bash
# scripts/system_restore.sh

SYSTEM_BACKUP=$1
CONFIG_BACKUP=$2
DB_BACKUP=$3

if [ -z "$SYSTEM_BACKUP" ] || [ -z "$CONFIG_BACKUP" ] || [ -z "$DB_BACKUP" ]; then
    echo "Usage: $0 <system_backup> <config_backup> <db_backup>"
    exit 1
fi

echo "Starting complete system restore..."

# Stop all services
docker-compose down

# Restore configuration
echo "Restoring configuration..."
tar -xzf $CONFIG_BACKUP

# Restore application files
echo "Restoring application files..."
tar -xzf $SYSTEM_BACKUP -C /

# Restore database
echo "Restoring database..."
./scripts/restore_database.sh $DB_BACKUP

echo "System restore completed"
```

---

## 🧪 **Backup Testing**

### **Backup Verification Script**

```bash
#!/bin/bash
# scripts/test_backup.sh

BACKUP_FILE=$1
TEST_DB="sms_agent_test"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

echo "Testing backup: $BACKUP_FILE"

# Create test database
docker-compose exec database psql -U sms_agent -c "CREATE DATABASE $TEST_DB;"

# Restore backup to test database
gunzip -c $BACKUP_FILE | docker-compose exec -T database psql -U sms_agent -d $TEST_DB

# Verify data integrity
TABLES=$(docker-compose exec database psql -U sms_agent -d $TEST_DB -t -c "SELECT tablename FROM pg_tables WHERE schemaname='public';")
TABLE_COUNT=$(echo "$TABLES" | wc -l)

echo "Tables found: $TABLE_COUNT"

for TABLE in $TABLES; do
    if [ ! -z "$TABLE" ]; then
        COUNT=$(docker-compose exec database psql -U sms_agent -d $TEST_DB -t -c "SELECT COUNT(*) FROM $TABLE;")
        echo "Table $TABLE: $COUNT records"
    fi
done

# Clean up test database
docker-compose exec database psql -U sms_agent -c "DROP DATABASE $TEST_DB;"

echo "Backup verification completed"
```

### **Recovery Testing**

```bash
#!/bin/bash
# scripts/test_recovery.sh

# This should be run in a test environment
echo "WARNING: This will destroy current data. Continue? (yes/no)"
read CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Recovery test cancelled"
    exit 1
fi

# Find latest backup
LATEST_BACKUP=$(ls -t /backups/sms_agent_backup_*.sql.gz | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "No backups found"
    exit 1
fi

echo "Testing recovery with: $LATEST_BACKUP"

# Perform recovery
./scripts/restore_database.sh $LATEST_BACKUP

# Verify system functionality
echo "Verifying system functionality..."
curl -f http://localhost:5001/health || {
    echo "Health check failed"
    exit 1
}

echo "Recovery test completed successfully"
```

---

## 📊 **Backup Monitoring**

### **Backup Status Dashboard**

```python
# monitoring/backup_status.py
import os
import datetime
from pathlib import Path

class BackupMonitor:
    def __init__(self, backup_dir="/backups"):
        self.backup_dir = Path(backup_dir)
    
    def get_backup_status(self):
        """Get status of all backups"""
        status = {
            'database': self._check_database_backups(),
            'system': self._check_system_backups(),
            'logs': self._check_log_backups(),
            'overall_health': 'healthy'
        }
        
        # Determine overall health
        if any(s['status'] == 'critical' for s in status.values() if isinstance(s, dict)):
            status['overall_health'] = 'critical'
        elif any(s['status'] == 'warning' for s in status.values() if isinstance(s, dict)):
            status['overall_health'] = 'warning'
        
        return status
    
    def _check_database_backups(self):
        """Check database backup status"""
        pattern = "sms_agent_backup_*.sql.gz"
        backups = list(self.backup_dir.glob(pattern))
        
        if not backups:
            return {'status': 'critical', 'message': 'No database backups found'}
        
        latest = max(backups, key=os.path.getctime)
        age = datetime.datetime.now() - datetime.datetime.fromtimestamp(latest.stat().st_ctime)
        
        if age.days > 1:
            return {'status': 'critical', 'message': f'Latest backup is {age.days} days old'}
        elif age.seconds > 25 * 3600:  # 25 hours
            return {'status': 'warning', 'message': f'Latest backup is {age.seconds // 3600} hours old'}
        
        return {
            'status': 'healthy',
            'message': f'Latest backup: {latest.name}',
            'count': len(backups),
            'size': self._format_size(latest.stat().st_size)
        }
    
    def _format_size(self, size_bytes):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
```

---

## 📋 **Disaster Recovery Plan**

### **Recovery Time Objectives (RTO)**
- **Critical Services**: 15 minutes
- **Full System**: 1 hour
- **Complete Data Recovery**: 4 hours

### **Recovery Point Objectives (RPO)**
- **Database**: 1 hour (incremental backups)
- **Configuration**: 24 hours (daily backups)
- **Logs**: 24 hours (daily backups)

### **Emergency Contacts**
- **System Administrator**: [Contact Info]
- **Database Administrator**: [Contact Info]
- **Cloud Provider Support**: [Contact Info]
- **Management**: [Contact Info]

---

## 🔗 **Related Documentation**

- **[Production Guide](PRODUCTION.md)** - Production deployment
- **[Monitoring Guide](MONITORING.md)** - System monitoring
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Issue resolution

---

**💾 Your backup and recovery system is now configured for comprehensive data protection and disaster recovery!** 