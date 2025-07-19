#!/bin/bash

# ================================================
# DOCKER HEALTH CHECK SCRIPT FOR SMS AGENT
# ================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to log messages
log() {
    echo -e "${GREEN}[HEALTH]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Health check function
health_check() {
    local exit_code=0
    
    log "Starting comprehensive health check..."
    
    # 1. Check if the Flask app is responding
    log "Checking Flask application..."
    if curl -f -s http://localhost:5000/health > /dev/null; then
        log "✅ Flask application is responding"
    else
        error "❌ Flask application is not responding"
        exit_code=1
    fi
    
    # 2. Check database connectivity
    log "Checking database connectivity..."
    if [ -f "/app/task_analytics.db" ]; then
        if sqlite3 /app/task_analytics.db "SELECT COUNT(*) FROM sqlite_master;" > /dev/null 2>&1; then
            log "✅ Task analytics database is accessible"
        else
            warn "⚠️ Task analytics database exists but is not accessible"
            exit_code=1
        fi
    else
        warn "⚠️ Task analytics database not found (will be created on first use)"
    fi
    
    if [ -f "/app/notifications.db" ]; then
        if sqlite3 /app/notifications.db "SELECT COUNT(*) FROM sqlite_master;" > /dev/null 2>&1; then
            log "✅ Notifications database is accessible"
        else
            warn "⚠️ Notifications database exists but is not accessible"
        fi
    else
        warn "⚠️ Notifications database not found (will be created on first use)"
    fi
    
    # 3. Check log directory
    log "Checking log directory..."
    if [ -d "/app/logs" ] && [ -w "/app/logs" ]; then
        log "✅ Log directory is writable"
    else
        error "❌ Log directory is not accessible or writable"
        exit_code=1
    fi
    
    # 4. Check critical environment variables
    log "Checking critical environment variables..."
    local missing_vars=()
    
    local critical_vars=(
        "TWILIO_ACCOUNT_SID"
        "TWILIO_AUTH_TOKEN"
        "OPENAI_API_KEY"
        "FLASK_SECRET_KEY"
    )
    
    for var in "${critical_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        error "❌ Missing critical environment variables: ${missing_vars[*]}"
        exit_code=1
    else
        log "✅ All critical environment variables are set"
    fi
    
    # 5. Check Python modules
    log "Checking Python module imports..."
    python3 -c "
import sys
modules = ['flask', 'twilio', 'openai', 'sqlite3', 'logging']
missing = []
for module in modules:
    try:
        __import__(module)
    except ImportError:
        missing.append(module)

if missing:
    print(f'Missing modules: {missing}')
    sys.exit(1)
else:
    print('All required modules available')
" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log "✅ All required Python modules are available"
    else
        error "❌ Some required Python modules are missing"
        exit_code=1
    fi
    
    # 6. Check disk space
    log "Checking disk space..."
    local disk_usage=$(df /app | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -lt 90 ]; then
        log "✅ Disk usage is acceptable ($disk_usage%)"
    else
        warn "⚠️ High disk usage: $disk_usage%"
    fi
    
    # 7. Memory check
    log "Checking memory usage..."
    local mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ "$mem_usage" -lt 85 ]; then
        log "✅ Memory usage is acceptable ($mem_usage%)"
    else
        warn "⚠️ High memory usage: $mem_usage%"
    fi
    
    # 8. Check process status
    log "Checking process status..."
    if pgrep -f "gunicorn.*app:app" > /dev/null; then
        log "✅ Gunicorn processes are running"
    else
        error "❌ Gunicorn processes not found"
        exit_code=1
    fi
    
    # Final status
    if [ $exit_code -eq 0 ]; then
        log "🎉 All health checks passed!"
    else
        error "💥 Health check failed!"
    fi
    
    return $exit_code
}

# Run health check
health_check 