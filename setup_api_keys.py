#!/usr/bin/env python3
"""
API Key Setup Script for SMS-to-Cursor Agent
Helps you configure your API keys for the system
"""

import os
import getpass
from pathlib import Path

def setup_env_file():
    """Create or update .env file with API keys"""
    
    print("🔑 SMS-to-Cursor Agent API Key Setup")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print("📁 Found existing .env file")
        overwrite = input("Do you want to overwrite it? (y/N): ").lower()
        if overwrite != 'y':
            print("Setup cancelled.")
            return
    else:
        print("📁 Creating new .env file")
    
    print("\n📋 Let's configure your API keys:")
    
    # Twilio Configuration
    print("\n📱 Twilio Configuration:")
    twilio_account_sid = input("Enter your Twilio Account SID: ").strip()
    twilio_auth_token = getpass.getpass("Enter your Twilio Auth Token: ").strip()
    twilio_phone_number = input("Enter your Twilio Phone Number (+1234567890): ").strip()
    
    # OpenAI Configuration
    print("\n🤖 OpenAI Configuration:")
    print("Note: You need an OpenAI API key for Cursor AI integration")
    print("Get one at: https://platform.openai.com/api-keys")
    openai_api_key = getpass.getpass("Enter your OpenAI API Key (sk-...): ").strip()
    
    # Cursor AI Configuration
    print("\n💻 Cursor AI Configuration:")
    print("Note: Cursor AI uses OpenAI API under the hood")
    print("You can use the same OpenAI API key for Cursor AI")
    cursor_api_key = input("Enter your Cursor AI API Key (or press Enter to use OpenAI key): ").strip()
    if not cursor_api_key:
        cursor_api_key = openai_api_key
        print("Using OpenAI API key for Cursor AI")
    
    cursor_workspace_id = input("Enter your Cursor Workspace ID (optional): ").strip()
    
    # Ngrok Configuration
    print("\n🌐 Ngrok Configuration:")
    print("Get your ngrok authtoken at: https://dashboard.ngrok.com/get-started/your-authtoken")
    ngrok_authtoken = input("Enter your Ngrok Auth Token: ").strip()
    
    # Voice Assistant Configuration
    print("\n🎤 Voice Assistant Configuration:")
    enable_voice = input("Enable voice assistant? (y/N): ").lower().strip()
    enable_voice = "True" if enable_voice == 'y' else "False"
    
    voice_language = input("Voice language (en-US): ").strip() or "en-US"
    voice_rate = input("Voice rate (150): ").strip() or "150"
    
    # Create .env content
    env_content = f"""# Twilio Configuration
TWILIO_ACCOUNT_SID={twilio_account_sid}
TWILIO_AUTH_TOKEN={twilio_auth_token}
TWILIO_PHONE_NUMBER={twilio_phone_number}

# Cursor AI Configuration
CURSOR_API_KEY={cursor_api_key}
CURSOR_WORKSPACE_ID={cursor_workspace_id}

# OpenAI Configuration
OPENAI_API_KEY={openai_api_key}

# Ngrok Configuration
NGROK_AUTHTOKEN={ngrok_authtoken}

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True

# Voice Assistant Configuration
ENABLE_VOICE_ASSISTANT={enable_voice}
VOICE_LANGUAGE={voice_language}
VOICE_RATE={voice_rate}

# SMS Configuration
MAX_SMS_LENGTH=160
"""
    
    # Write .env file
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print(f"\n✅ Successfully created .env file")
        
        # Test the configuration
        print("\n🧪 Testing configuration...")
        test_configuration()
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

def test_configuration():
    """Test the API key configuration"""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    print("🔍 Testing API keys...")
    
    # Test OpenAI API key
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key and openai_key.startswith("sk-"):
        print("✅ OpenAI API key format looks correct")
    else:
        print("❌ OpenAI API key format is incorrect (should start with 'sk-')")
    
    # Test Twilio credentials
    twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    twilio_token = os.environ.get("TWILIO_AUTH_TOKEN")
    if twilio_sid and twilio_token:
        print("✅ Twilio credentials are set")
    else:
        print("❌ Twilio credentials are missing")
    
    # Test ngrok token
    ngrok_token = os.environ.get("NGROK_AUTHTOKEN")
    if ngrok_token:
        print("✅ Ngrok authtoken is set")
    else:
        print("❌ Ngrok authtoken is missing")
    
    print("\n📋 Next steps:")
    print("1. Run: docker-compose up --build")
    print("2. Test the system with: python test_setup.py")
    print("3. Configure your Twilio webhook URL")

def main():
    """Main setup function"""
    try:
        setup_env_file()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")

if __name__ == "__main__":
    main() 