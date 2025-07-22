#!/bin/bash

# SMS-to-AI Agent Admin User Creation Script
# This script helps create admin users for the dashboard

echo "🔐 SMS-to-AI Agent - Admin User Creation"
echo "========================================"
echo ""

# Check if Docker is running
if ! docker-compose ps | grep -q "web.*Up"; then
    echo "❌ Error: Application is not running."
    echo "Please start the application first:"
    echo "  docker-compose up -d"
    exit 1
fi

echo "Choose creation method:"
echo "1) Interactive mode (recommended)"
echo "2) Quick mode with defaults"
echo "3) List existing admin users"
echo ""

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo "🚀 Starting interactive admin user creation..."
        docker-compose exec web python manage.py create_admin
        ;;
    2)
        echo "📝 Quick admin user creation"
        read -p "Username [admin]: " username
        username=${username:-admin}
        
        read -p "Email (optional): " email
        
        echo "⚠️  Password will be generated automatically for security"
        
        # Generate a random password
        password=$(openssl rand -base64 12)
        
        docker-compose exec web python manage.py create_admin \
            --username "$username" \
            --email "$email" \
            --password "$password" \
            --superuser \
            --no-input
        
        echo ""
        echo "✅ Admin user created successfully!"
        echo "Username: $username"
        echo "Password: $password"
        echo ""
        echo "⚠️  IMPORTANT: Save these credentials securely!"
        echo ""
        ;;
    3)
        echo "📋 Listing existing admin users..."
        docker-compose exec web python manage.py list_admins
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "🌐 Dashboard URL: http://localhost:5001/dashboard/"
echo ""
echo "Need help? Check the documentation:"
echo "  docs/user-guides/ADMIN_GUIDE.md" 