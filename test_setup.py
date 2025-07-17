#!/usr/bin/env python3
"""
Test script to verify the SMS-to-Cursor agent setup.
Run this script to check if all components are properly configured.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment_variables():
    """Test if all required environment variables are set"""
    print("🔍 Testing environment variables...")
    
    required_vars = [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_PHONE_NUMBER",
        "GOOGLE_API_KEY"
    ]
    
    optional_vars = [
        "NGROK_AUTHTOKEN",
        "AI_MODEL",
        "MAX_SMS_LENGTH"
    ]
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_required.append(var)
        else:
            print(f"✅ {var}: Set")
    
    for var in optional_vars:
        if not os.environ.get(var):
            missing_optional.append(var)
        else:
            print(f"✅ {var}: Set")
    
    if missing_required:
        print(f"❌ Missing required environment variables: {missing_required}")
        return False
    if missing_optional:
        print(f"⚠️  Missing optional environment variables: {missing_optional}")
    
    print("✅ All required environment variables are set!")
    return True

def test_google_ai():
    """Test Google AI API connection"""
    print("\n🤖 Testing Google AI API...")
    
    try:
        import google.generativeai as genai
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)
        
        model_name = os.environ.get("AI_MODEL", "gemini-2.0-flash")
        model = genai.GenerativeModel(model_name)
        
        # Test with a simple prompt
        response = model.generate_content("Say 'Hello, world!' in exactly 3 words.")
        
        if hasattr(response, 'text') and response.text:
            print(f"✅ Google AI API working! Test response: '{response.text}'")
            return True
        else:
            print("❌ Google AI API returned empty response")
            return False
            
    except Exception as e:
        print(f"❌ Google AI API test failed: {e}")
        return False

def test_twilio():
    """Test Twilio API connection"""
    print("\n📱 Testing Twilio API...")
    
    try:
        from twilio.rest import Client
        
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        
        client = Client(account_sid, auth_token)
        
        # Test by fetching account info
        account = client.api.accounts(account_sid).fetch()
        
        if account.status == 'active':
            print(f"✅ Twilio API working! Account: {account.friendly_name}")
            return True
        else:
            print(f"❌ Twilio account not active: {account.status}")
            return False
            
    except Exception as e:
        print(f"❌ Twilio API test failed: {e}")
        return False

def test_flask_app():
    """Test if Flask app can start"""
    print("\n🌐 Testing Flask application...")
    
    try:
        # Import the app
        from app import app
        
        # Test if the app can be created
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Flask app working! Health endpoint responding.")
                return True
            else:
                print(f"❌ Flask app health check failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 SMS-to-Cursor Agent Setup Test")
    print("="*40)
    
    tests = [
        test_environment_variables,
        test_google_ai,
        test_twilio,
        test_flask_app
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    print("📊 Test Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All {total} tests passed! Your setup is ready to go.")
        print("\nNext steps:")
        print("1. Run: docker-compose up --build")
        print("2. Configure your Twilio webhook URL")
        print("3. Send an SMS to test the system!")
    else:
        print(f"⚠️  {passed}/{total} tests passed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 