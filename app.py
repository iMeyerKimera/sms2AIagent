import os
import logging
import time
from datetime import datetime
from flask import Flask, request, Response, jsonify, send_file
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from functools import wraps
import json

# Import our custom modules
from cursor_agent import CursorAgent
from voice_assistant import VoiceAssistant

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sms_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Rate limiting storage (in production, use Redis)
request_timestamps = {}
MAX_REQUESTS_PER_HOUR = 10

def rate_limit(f):
    """Simple rate limiting decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from_number = request.values.get('From', 'unknown')
        current_time = time.time()
        
        # Clean old timestamps (older than 1 hour)
        request_timestamps[from_number] = [
            ts for ts in request_timestamps.get(from_number, []) if current_time - ts < 3600
        ]
        
        # Check rate limit
        if len(request_timestamps.get(from_number, [])) >= MAX_REQUESTS_PER_HOUR:
            logger.warning(f"Rate limit exceeded for {from_number}")
            return Response(
                str(MessagingResponse().message("Rate limit exceeded. Please wait before sending another request.")),
                mimetype='application/xml'
            )
        
        # Add current timestamp
        if from_number not in request_timestamps:
            request_timestamps[from_number] = []
        request_timestamps[from_number].append(current_time)
        
        return f(*args, **kwargs)
    return decorated_function

# --- Initialize Clients ---

# Initialize Cursor AI Agent
try:
    cursor_agent = CursorAgent()
    logger.info("Successfully initialized Cursor AI Agent")
except Exception as e:
    logger.error(f"Error initializing Cursor AI Agent: {e}")
    cursor_agent = None

# Initialize Voice Assistant
try:
    voice_assistant = VoiceAssistant()
    if voice_assistant.enable_voice:
        logger.info("Voice assistant enabled and initialized")
    else:
        logger.info("Voice assistant disabled")
except Exception as e:
    logger.error(f"Error initializing Voice Assistant: {e}")
    voice_assistant = None

# Initialize Twilio Client
try:
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    twilio_phone_number = os.environ.get("TWILIO_PHONE_NUMBER")
    if not all([account_sid, auth_token, twilio_phone_number]):
        raise ValueError("Twilio credentials not fully set in environment variables.")
    twilio_client = Client(account_sid, auth_token)
    logger.info("Successfully initialized Twilio Client")
except Exception as e:
    logger.error(f"Error initializing Twilio Client: {e}")
    twilio_client = None

def create_enhanced_prompt(user_message):
    """Create an enhanced prompt for better AI responses"""
    system_prompt = """You are a helpful AI assistant that can perform various tasks. 
    When responding to user requests:
    1. Be helpful, accurate, and concise
    2. If asked to create something, provide practical and actionable results
    3. If asked to explain something, use clear and simple language
    4. If asked to analyze something, provide insights and recommendations
    5. Always consider the context and intent of the user's request
    
    User request: """
    
    return f"{system_prompt}{user_message}"

def summarize_for_sms(text, max_length=160):
    """Summarize text to fit SMS character limits"""
    if len(text) <= max_length:
        return text
    
    summary_prompt = f"""Please summarize the following text to be under {max_length} characters, 
    suitable for an SMS message. Be concise, direct, and preserve the most important information. 
    If the text is too long to summarize meaningfully, provide a brief overview with key points.
    
    Text: {text}
    
    Summary: """
    
    try:
        # Use Cursor AI for summarization
        result = cursor_agent.create_task(summary_prompt)
        if result["success"]:
            summary = result["response"].strip()
            
            # Fallback if summary is still too long
            if len(summary) > max_length:
                summary = text[:max_length-3] + "..."
            return summary
        else:
            # Fallback to simple truncation
            return text[:max_length-3] + "..." if len(text) > max_length else text
    except Exception as e:
        logger.error(f"Error in summarization: {e}")
        # Fallback to simple truncation
        return text[:max_length-3] + "..." if len(text) > max_length else text

@app.route("/health", methods=['GET'])
def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cursor_agent_available": cursor_agent is not None,
        "voice_assistant_available": voice_assistant is not None and voice_assistant.enable_voice,
        "twilio_available": twilio_client is not None
    }
    return jsonify(status)

@app.route("/voice", methods=['POST'])
def voice_endpoint():
    """Voice assistant endpoint for Siri/Alexa integration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        action = data.get("action")
        text = data.get("text", "")
        
        if action == "text_to_speech":
            if not text:
                return jsonify({"error": "No text provided"}), 400
            
            result = voice_assistant.create_voice_response(text)
            if result["success"]:
                return jsonify({
                    "success": True,
                    "audio_file": result["audio_file"],
                    "duration": result["duration"]
                })
            else:
                return jsonify({"error": result["error"]}), 500
        
        elif action == "speech_to_text":
            audio_file = data.get("audio_file")
            result = voice_assistant.speech_to_text(audio_file)
            return jsonify(result)
        
        else:
            return jsonify({"error": "Invalid action"}), 400
            
    except Exception as e:
        logger.error(f"Voice endpoint error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/audio/<filename>")
def serve_audio(filename):
    """Serve generated audio files"""
    try:
        return send_file(filename, mimetype='audio/mpeg')
    except Exception as e:
        logger.error(f"Error serving audio file {filename}: {e}")
        return jsonify({"error": "Audio file not found"}), 404

@app.route("/sms", methods=['POST'])
@rate_limit
def sms_reply():
    """Receive SMS from Twilio, process with Cursor AI, and send reply."""

    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')

    logger.info(f"Received message from {from_number}: '{incoming_msg}'")

    if not cursor_agent or not twilio_client:
        logger.error("A client (Cursor AI or Twilio) is not initialized. Cannot process request.")
        return Response(status=500)

    try:
        # --- Step 1: Process the task with Cursor AI agent ---
        logger.info("Asking Cursor AI agent to perform the task...")
        
        # Create enhanced prompt
        enhanced_prompt = create_enhanced_prompt(incoming_msg)
        result = cursor_agent.create_task(enhanced_prompt)

        if not result["success"]:
            logger.error(f"Cursor AI task failed: {result.get('error', 'Unknown error')}")
            twilio_client.messages.create(
                body='Sorry, I encountered an error processing your request. Please try again.',
                from_=twilio_phone_number,
                to=from_number
            )
            return Response(str(MessagingResponse()), mimetype='application/xml')

        detailed_text = result["response"]
        task_type = result.get("task_type", "general")
        
        logger.info(f"Cursor AI agent completed task (type: {task_type})")

        # --- Step 2: Create voice response if enabled ---
        voice_response = None
        if voice_assistant and voice_assistant.enable_voice:
            logger.info("Creating voice response...")
            voice_result = voice_assistant.create_voice_response(detailed_text)
            if voice_result["success"]:
                voice_response = voice_result["audio_file"]
                logger.info(f"Voice response created: {voice_response}")

        # --- Step 3: Summarize the result for SMS ---
        logger.info("Summarizing response for SMS...")
        max_sms_length = int(os.environ.get("MAX_SMS_LENGTH", 160))
        sms_friendly_text = summarize_for_sms(detailed_text, max_sms_length)

        logger.info(f"Generated SMS-friendly summary: '{sms_friendly_text}'")

        # --- Step 4: Send the summary back to the user via Twilio ---
        twilio_client.messages.create(
            body=sms_friendly_text,
            from_=twilio_phone_number,
            to=from_number
        )
        logger.info(f"Successfully sent summary to {from_number}")

        # --- Step 5: If voice response was created, send it via MMS ---
        if voice_response:
            try:
                # Note: Twilio MMS requires the file to be accessible via URL
                # In production, you'd upload the file to a cloud service
                logger.info("Voice response would be sent via MMS in production")
            except Exception as e:
                logger.error(f"Failed to send voice response: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        try:
            twilio_client.messages.create(
                body='Sorry, an unexpected error occurred and I could not process your request. Please try again later.',
                from_=twilio_phone_number,
                to=from_number
            )
        except Exception as twilio_error:
            logger.error(f"Failed to send error message via Twilio: {twilio_error}")

    # Return an empty TwiML response to acknowledge receipt of the message
    return Response(str(MessagingResponse()), mimetype='application/xml')

@app.route("/cursor/workspace", methods=['GET'])
def get_cursor_workspace():
    """Get Cursor workspace information"""
    if not cursor_agent:
        return jsonify({"error": "Cursor AI agent not available"}), 503
    
    try:
        workspace_info = cursor_agent.get_workspace_info()
        return jsonify({
            "success": True,
            "workspace_info": workspace_info
        })
    except Exception as e:
        logger.error(f"Error getting workspace info: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting SMS-to-Cursor Agent on port {port} with debug={debug}")
    app.run(debug=debug, port=port, host='0.0.0.0')