import os
import logging
import time
from datetime import datetime
from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai
from dotenv import load_dotenv
from functools import wraps

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

# Initialize Gemini AI Client
try:
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")
    
    genai.configure(api_key=google_api_key)
    
    # Get model from environment or use default
    ai_model = os.environ.get("AI_MODEL", "gemini-2.0-flash")
    
    # Added safety_settings to be less restrictive. Tune if needed.
    model = genai.GenerativeModel(
        ai_model,
        safety_settings={
            'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
            'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
            'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
            'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE'
        }
    )
    logger.info(f"Successfully initialized Google AI Client with model: {ai_model}")
except Exception as e:
    logger.error(f"Error initializing Google AI Client: {e}")
    model = None

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
1. Helpful, accurate, and concise
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
    
    Text:{text}
    
    Summary:"""
    try:
        summary_result = model.generate_content(summary_prompt)
        summary = summary_result.text.strip()
        
        # Fallback if summary is still too long
        if len(summary) > max_length:
            summary = text[:max_length-3] + "..."   
        return summary
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
        "ai_model_available": model is not None,
        "twilio_available": twilio_client is not None
    }
    return status

@app.route("/sms", methods=['POST'])
@rate_limit
def sms_reply():
    """Receive SMS from Twilio, process with AI, and send reply."""

    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')

    logger.info(f"Received message from {from_number}: '{incoming_msg}'")

    if not model or not twilio_client:
        logger.error("A client (Gemini or Twilio) is not initialized. Cannot process request.")
        return Response(status=500)

    try:
        # --- Step 1: Perform the main task with the AI agent ---
        logger.info("Asking AI agent to perform the main task...")
        
        # Create enhanced prompt
        enhanced_prompt = create_enhanced_prompt(incoming_msg)
        main_result = model.generate_content(enhanced_prompt)

        # Robust check for response content
        try:
            detailed_text = main_result.text
            logger.info("AI agent generated a detailed response.")
        except ValueError:
            # If .text fails, it's likely the prompt was blocked
            logger.warning(f"AI response was blocked. Feedback: {main_result.prompt_feedback}")
            twilio_client.messages.create(
                body='Sorry, your request could not be processed. It may have been blocked for safety reasons. Please try a different prompt.',
                from_=twilio_phone_number,
                to=from_number
            )
            return Response(str(MessagingResponse()), mimetype='application/xml')

        # --- Step 2: Summarize the result for SMS ---
        logger.info("Summarizing response for SMS...")
        max_sms_length = int(os.environ.get("MAX_SMS_LENGTH", 160))
        sms_friendly_text = summarize_for_sms(detailed_text, max_sms_length)

        logger.info(f"Generated SMS-friendly summary: '{sms_friendly_text}'")
        # --- Step 3: Send the summary back to the user via Twilio ---
        twilio_client.messages.create(
            body=sms_friendly_text,
            from_=twilio_phone_number,
            to=from_number
        )
        logger.info(f"Successfully sent summary to {from_number}")

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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting SMS Agent on port {port} with debug={debug}")
    app.run(debug=debug, port=port, host='0.0.0.0')