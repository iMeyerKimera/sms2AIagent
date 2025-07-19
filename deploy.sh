#!/bin/bash

# ================================================
# ENHANCED SMS-TO-CURSOR AI AGENT DEPLOYMENT SCRIPT
# ================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to validate environment variables
validate_env() {
    local missing_vars=()
    
    # Required variables
    local required_vars=(
        "TWILIO_ACCOUNT_SID"
        "TWILIO_AUTH_TOKEN" 
        "TWILIO_PHONE_NUMBER"
        "OPENAI_API_KEY"
        "FLASK_SECRET_KEY"
    )
    
    print_status "Validating environment variables..."
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        print_error "Please set these variables in your .env file"
        return 1
    fi
    
    print_success "All required environment variables are set"
    return 0
}

# Function to check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check for Docker
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        return 1
    fi
    
    # Check for Docker Compose
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        return 1
    fi
    
    # Check Docker daemon
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker daemon is not running. Please start Docker first."
        return 1
    fi
    
    print_success "All requirements satisfied"
    return 0
}

# Function to setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [[ ! -f .env ]]; then
        print_warning ".env file not found. Creating from template..."
        if [[ -f env.example ]]; then
            cp env.example .env
            print_success "Created .env file from template"
            print_warning "Please edit .env file with your actual credentials before proceeding"
            read -p "Press Enter after you've updated the .env file..."
        else
            print_error "env.example template not found"
            return 1
        fi
    fi
    
    # Load environment variables
    if [[ -f .env ]]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    # Create necessary directories
    mkdir -p logs data
    chmod 755 logs data
    
    print_success "Environment setup complete"
}

# Function to build and start services
deploy_services() {
    print_status "Building and deploying services..."
    
    # Stop existing containers
    print_status "Stopping existing containers..."
    docker-compose down --remove-orphans || true
    
    # Build the application
    print_status "Building application container..."
    docker-compose build --no-cache
    
    # Start services
    print_status "Starting services..."
    docker-compose up -d
    
    # Wait for health check
    print_status "Waiting for services to be healthy..."
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose ps | grep -q "healthy"; then
            print_success "Services are healthy and running"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            print_error "Services failed to become healthy within timeout"
            docker-compose logs
            return 1
        fi
        
        print_status "Attempt $attempt/$max_attempts - waiting..."
        sleep 10
        ((attempt++))
    done
}

# Function to show service status
show_status() {
    print_status "Service Status:"
    docker-compose ps
    
    echo ""
    print_status "Service Logs (last 10 lines):"
    docker-compose logs --tail=10 web
    
    echo ""
    print_status "Testing endpoints..."
    
    # Test health endpoint
    local health_url="http://localhost:5001/health"
    if curl -s "$health_url" > /dev/null; then
        print_success "Health endpoint responding: $health_url"
    else
        print_warning "Health endpoint not responding: $health_url"
    fi
    
    # Test admin dashboard
    local admin_url="http://localhost:5001/admin/"
    if curl -s "$admin_url" > /dev/null; then
        print_success "Admin dashboard responding: $admin_url"
    else
        print_warning "Admin dashboard not responding: $admin_url"
    fi
    
    # Show ngrok status if available
    if docker-compose ps | grep -q ngrok; then
        print_status "Ngrok tunnel:"
        local ngrok_url="http://localhost:4040/api/tunnels"
        if command_exists jq; then
            curl -s "$ngrok_url" | jq -r '.tunnels[0].public_url' 2>/dev/null || echo "Ngrok API not available"
        else
            echo "Visit http://localhost:4040 to see ngrok tunnel URL"
        fi
    fi
}

# Function to setup production optimizations
setup_production() {
    print_status "Applying production optimizations..."
    
    # Set production environment variables
    export FLASK_ENV=production
    export FLASK_DEBUG=false
    
    # Update docker-compose for production
    if [[ ! -f docker-compose.prod.yml ]]; then
        print_status "Creating production docker-compose configuration..."
        cat > docker-compose.prod.yml << EOF
version: '3.8'
services:
  web:
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "200m"
        max-file: "10"
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
  
  nginx:
    image: nginx:alpine
    container_name: sms_agent_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
    restart: always
    networks:
      - sms_network
EOF
    fi
    
    print_success "Production optimizations applied"
}

# Main deployment function
main() {
    echo "================================================"
    echo "ENHANCED SMS-TO-CURSOR AI AGENT DEPLOYMENT"
    echo "================================================"
    echo ""
    
    # Parse command line arguments
    local mode="development"
    while [[ $# -gt 0 ]]; do
        case $1 in
            --production|-p)
                mode="production"
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [--production|-p] [--help|-h]"
                echo "  --production, -p    Deploy in production mode"
                echo "  --help, -h          Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    print_status "Deployment mode: $mode"
    
    # Run deployment steps
    check_requirements || exit 1
    setup_environment || exit 1
    validate_env || exit 1
    
    if [[ "$mode" == "production" ]]; then
        setup_production || exit 1
    fi
    
    deploy_services || exit 1
    show_status
    
    echo ""
    print_success "Deployment completed successfully!"
    echo ""
    print_status "Next steps:"
    echo "1. Visit http://localhost:5001/health to verify the system is healthy"
    echo "2. Visit http://localhost:5001/admin/ to access the admin dashboard"
    echo "3. Configure your Twilio webhook to point to your ngrok URL + /sms"
    echo "4. Send a test SMS to verify end-to-end functionality"
    echo ""
    
    if [[ "$mode" == "production" ]]; then
        print_warning "Production deployment complete. Remember to:"
        echo "- Set up SSL certificates"
        echo "- Configure firewall rules"
        echo "- Set up monitoring and alerts"
        echo "- Regular database backups"
    fi
}

# Run main function
main "$@" 