#!/bin/bash

# SMS-to-Cursor Agent Deployment Script
# This script helps you deploy the SMS agent system

set -e  # Exit on any error

echo🚀 SMS-to-Cursor Agent Deployment Script"
echo "========================================

#Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! echo "Please copy env.example to .env and configure your credentials:
    echocp env.example .env"
    echo "Then edit .env with your actual API keys and credentials.exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first.exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Test the setup
echo "
echo🔍Testing setup...python3 test_setup.py

if  $? -ne 0]; then
    echo "❌ Setup test failed. Please fix the issues above before deploying."
    exit 1fi

echo ""
echo "✅ Setup test passed"

# Build and start the containers
echo ""
echo "🐳 Building and starting containers..."
docker-compose up --build -d

# Wait a moment for containers to start
echo "⏳ Waiting for containers to start..."
sleep 10

# Check if containers are running
echo ""
echo "🔍 Checking container status..."
if docker-compose ps | grep -q "Up; then
    echo✅ Containers are running successfully!
else   echo "❌ Containers failed to start properly."
    echo "Check the logs with: docker-compose logs  exit1i

# Get ngrok URL
echo "
echo🌐 Getting ngrok URL..."
sleep 5  # Give ngrok time to start

# Try to get the ngrok URL from the API
NGROK_URL=$(curl -s http://localhost:4040api/tunnels | grep -opublic_url:"^"]*' | cut -d'"-f4| head -1)

if-n "$NGROK_URL]; then
    echo✅ Ngrok URL: $NGROK_URL"
    echo ""
    echo📱 Next steps:"
    echo1. Go to your Twilio Console"
    echo "2. Navigate to Phone Numbers → Manage → Active numbers"
    echo3. Click on your phone number  echo "4et the webhook URL for incoming messages to:    echo   $NGROK_URL/sms  echo "5. Set the HTTP method to POST"
    echo "6. Save the configuration"
    echo ""
    echo🎉Your SMS-to-Cursor agent is now running!"
    echo "Send an SMS to your Twilio phone number to test it.
else
    echo "⚠️  Could not retrieve ngrok URL automatically.echoPlease check the ngrok interface at http://localhost:440echo "and manually configure your Twilio webhook URL.fi

echo 📋 Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop system: docker-compose down
echo  Restart: docker-compose restart"
echo "  Health check: curl http://localhost:5001/health" 