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
        "CURSOR_API_KEY",
        "OPENAI_API_KEY"
    ]
    
    optional_vars = [
        "CURSOR_WORKSPACE_ID",
        "NGROK_AUTHTOKEN",
        "ENABLE_VOICE_ASSISTANT",
        "VOICE_LANGUAGE",
        "VOICE_RATE",
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

def test_cursor_ai():
    """Test Cursor AI integration"""
    print("\n🤖 Testing Cursor AI integration...")
    
    try:
        from cursor_agent import CursorAgent
        
        cursor_agent = CursorAgent()
        
        # Test with a simple task
        result = cursor_agent.create_task("Say 'Hello, world!' in exactly 3 words.")
        
        if result["success"] and result["response"]:
            print(f"✅ Cursor AI working! Test response: '{result['response'][:100]}...'")
            return True
        else:
            print(f"❌ Cursor AI returned error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Cursor AI test failed: {e}")
        return False

def test_voice_assistant():
    """Test Voice Assistant functionality"""
    print("\n🎤 Testing Voice Assistant...")
    
    try:
        from voice_assistant import VoiceAssistant
        
        voice_assistant = VoiceAssistant()
        
        if voice_assistant.enable_voice:
            print("✅ Voice assistant enabled")
            
            # Test text-to-speech
            test_text = "Hello, this is a test of the voice assistant."
            result = voice_assistant.text_to_speech(test_text)
            
            if result["success"]:
                print("✅ Text-to-speech working")
                return True
            else:
                print(f"❌ Text-to-speech failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print("⚠️  Voice assistant disabled (optional)")
            return True
            
    except Exception as e:
        print(f"❌ Voice assistant test failed: {e}")
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
        test_cursor_ai,
        test_voice_assistant,
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
        print("4. Use voice endpoints for Siri/Alexa integration")
    else:
        print(f"⚠️  {passed}/{total} tests passed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 