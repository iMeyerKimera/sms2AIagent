#!/bin/bash

# =====================================================
# Enhanced SMS-to-Cursor AI Agent Deployment Script
# PostgreSQL-Focused System
# =====================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
REBUILD=false
PULL_IMAGES=false
SHOW_LOGS=false
BACKUP_DATA=false

# Help function
show_help() {
    echo "Enhanced SMS-to-Cursor AI Agent Deployment Script"
    echo "PostgreSQL-Based System"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -r, --rebuild            Rebuild images from scratch"
    echo "  -p, --pull               Pull latest base images"
    echo "  -l, --logs               Show logs after deployment"
    echo "  -b, --backup             Backup existing data before deployment"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                       # Standard deployment"
    echo "  $0 --rebuild             # Rebuild and deploy"
    echo "  $0 --backup --rebuild    # Backup, rebuild, and deploy"
    echo "  $0 --logs                # Deploy and show logs"
    echo ""
    echo "Environment File:"
    echo "  The system uses .env file. Copy from env.example if needed."
    echo ""
    echo "Database:"
    echo "  PostgreSQL is used for all environments with persistent volumes."
}

# Log function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--rebuild)
            REBUILD=true
            shift
            ;;
        -p|--pull)
            PULL_IMAGES=true
            shift
            ;;
        -l|--logs)
            SHOW_LOGS=true
            shift
            ;;
        -b|--backup)
            BACKUP_DATA=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            error "Unknown option: $1. Use --help for usage information."
            ;;
    esac
done

log "Starting PostgreSQL-based SMS AI Agent deployment"

# Check if environment file exists
if [ ! -f ".env" ]; then
    warn "Environment file not found: .env"
    
    if [ -f "env.example" ]; then
        log "Copying env.example to .env"
        cp env.example .env
        warn "Please edit .env with your actual configuration before continuing."
        read -p "Press Enter to continue or Ctrl+C to exit..."
    else
        error "No environment file or example found. Please create .env file."
    fi
fi

# Create necessary directories
log "Creating necessary directories..."
mkdir -p logs backups database/init database/backups database/scripts

# Set appropriate permissions
chmod 755 logs backups
chmod 700 database/backups  # Restrict backup access

# Backup existing data if requested
if [ "$BACKUP_DATA" = true ]; then
    log "Creating backup of existing data..."
    if [ -d "backups" ] && [ "$(ls -A backups)" ]; then
        timestamp=$(date +%Y%m%d_%H%M%S)
        backup_dir="backups/pre_deploy_backup_$timestamp"
        mkdir -p "$backup_dir"
        
        # Backup database if running
        if docker-compose ps database | grep -q "Up"; then
            log "Backing up PostgreSQL database..."
            docker-compose exec -T database pg_dump -U sms_agent -d sms_agent_db > "$backup_dir/database_backup.sql"
            if [ $? -eq 0 ]; then
                log "Database backup created: $backup_dir/database_backup.sql"
                gzip "$backup_dir/database_backup.sql"
            else
                warn "Database backup failed"
            fi
        fi
        
        # Backup logs
        if [ -d "logs" ] && [ "$(ls -A logs)" ]; then
            cp -r logs "$backup_dir/"
            log "Logs backed up to $backup_dir/logs"
        fi
    fi
fi

# Pull images if requested
if [ "$PULL_IMAGES" = true ]; then
    log "Pulling latest base images..."
    docker-compose pull
fi

# Stop existing containers
log "Stopping existing containers..."
docker-compose down

# Build/rebuild images
if [ "$REBUILD" = true ]; then
    log "Rebuilding images from scratch..."
    docker-compose build --no-cache
else
    log "Building images..."
    docker-compose build
fi

# Start services
log "Starting PostgreSQL-based services..."
docker-compose up -d

# Wait for services to be ready
log "Waiting for services to start..."
sleep 15

# Health check with retries
log "Performing health check..."
max_retries=30
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    if curl -f -s http://localhost:5001/health > /dev/null; then
        log "✅ Application is healthy and ready!"
        break
    else
        retry_count=$((retry_count + 1))
        if [ $retry_count -eq $max_retries ]; then
            error "❌ Application failed to start after $max_retries attempts"
        fi
        echo -n "."
        sleep 3
    fi
done

# Check database connectivity
log "Checking PostgreSQL database connectivity..."
if docker-compose exec -T database pg_isready -U sms_agent -d sms_agent_db > /dev/null 2>&1; then
    log "✅ PostgreSQL database is ready!"
else
    warn "⚠️  PostgreSQL database connectivity check failed"
fi

# Show deployment information
echo ""
echo -e "${GREEN}🚀 Deployment completed successfully!${NC}"
echo ""
echo "📊 Service Information:"
echo "  Web Application: http://localhost:5001"
echo "  Admin Dashboard: http://localhost:5001/admin/"
echo "  Ngrok Panel:     http://localhost:4040"
echo ""

# Get ngrok URL if available
if command -v curl &> /dev/null; then
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o 'https://[^"]*\.ngrok[^"]*' | head -1)
    if [ ! -z "$NGROK_URL" ]; then
        echo "🌐 Public URL:    $NGROK_URL"
        echo "   Webhook URL:  $NGROK_URL/sms/receive"
        echo ""
    fi
fi

# Database information
echo "🗄️  Database:      PostgreSQL 15"
echo "   Host:         localhost:5432"
echo "   Database:     sms_agent_db"
echo "   Status:       $(docker-compose ps database --format "table {{.State}}" | tail -1)"
echo ""

# Show container status
echo "📦 Container Status:"
docker-compose ps --format "table {{.Name}}\t{{.State}}\t{{.Ports}}"
echo ""

echo "📁 Data Directories:"
echo "   Logs:         ./logs/"
echo "   Backups:      ./database/backups/"
echo "   DB Data:      Docker volume (postgres_data)"
echo ""

# Show next steps
echo "🔧 Next Steps:"
echo "  1. Edit .env file with your API keys"
echo "  2. Configure Twilio webhook: [NGROK_URL]/sms/receive"
echo "  3. Test health endpoint: curl http://localhost:5001/health"
echo "  4. Access Django admin: http://localhost:5001/admin/"
echo "  5. Access custom dashboard: http://localhost:5001/dashboard/"
echo ""

# Database management commands
echo "💾 Database Management:"
echo "  # Connect to database:"
echo "  docker-compose exec database psql -U sms_agent -d sms_agent_db"
echo ""
echo "  # Create manual backup:"
echo "  docker-compose exec database pg_dump -U sms_agent -d sms_agent_db > backup.sql"
echo ""
echo "  # View database logs:"
echo "  docker-compose logs database"
echo ""

# Show logs if requested
if [ "$SHOW_LOGS" = true ]; then
    echo ""
    log "Showing application logs (Ctrl+C to exit):"
    docker-compose logs -f web
fi

echo ""
echo -e "${GREEN}✨ Your PostgreSQL-powered SMS AI Assistant is ready!${NC}" 