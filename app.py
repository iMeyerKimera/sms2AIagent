import os
import logging
import time
import asyncio
from datetime import datetime
from flask import Flask, request, Response, jsonify, send_file, session
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from functools import wraps
import json

# Load environment variables first
load_dotenv()

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sms_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import our custom modules
from cursor_agent import CursorAgent
from voice_assistant import VoiceAssistant

# Temporarily disable advanced components for testing
try:
    from task_router import TaskRouter
    from admin_dashboard import admin_bp
    from notification_system import NotificationSystem, notify_task_completion, notify_system_alert
    ADVANCED_FEATURES_AVAILABLE = True
    logger.info("Advanced features loaded successfully")
except ImportError as e:
    logger.warning(f"Advanced features not available: {e}")
    ADVANCED_FEATURES_AVAILABLE = False
    TaskRouter = None
    admin_bp = None
    NotificationSystem = None
    notify_task_completion = None
    notify_system_alert = None

# Note: logging already configured above

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Register admin blueprint
if admin_bp:
    app.register_blueprint(admin_bp)

# Initialize new components
try:
    if ADVANCED_FEATURES_AVAILABLE:
        task_router = TaskRouter()
        notification_system = NotificationSystem()
        logger.info("Successfully initialized Task Router and Notification System")
        
        # Setup default alert rules
        notification_system.setup_alert_rules()
    else:
        task_router = None
        notification_system = None
except Exception as e:
    logger.error(f"Error initializing advanced components: {e}")
    task_router = None
    notification_system = None

# Rate limiting storage (in production, use Redis)
request_timestamps = {}

def enhanced_rate_limit(f):
    """Enhanced rate limiting using task router"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from_number = request.values.get('From', 'unknown')
        
        if not task_router:
            # Fallback to basic rate limiting
            return basic_rate_limit(f)(*args, **kwargs)
        
        try:
            # Use task router for sophisticated rate limiting
            routing_result = task_router.route_task(from_number, request.values.get('Body', ''))
            
            if not routing_result["success"]:
                if "rate limit" in routing_result.get("error", "").lower():
                    logger.warning(f"Rate limit exceeded for {from_number}: {routing_result['error']}")
                    response = MessagingResponse()
                    message = routing_result["error"]
                    if routing_result.get("upgrade_suggestion"):
                        message += " Consider upgrading your tier for higher limits."
                    response.message(message)
                    return Response(str(response), mimetype='application/xml')
                else:
                    logger.error(f"Task routing error: {routing_result['error']}")
                    # Continue with fallback processing
            
            # Store routing info in request context for later use
            request.routing_info = routing_result
            
        except Exception as e:
            logger.error(f"Error in enhanced rate limiting: {e}")
            # Continue with fallback
            
        return f(*args, **kwargs)
    return decorated_function

def basic_rate_limit(f):
    """Fallback basic rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from_number = request.values.get('From', 'unknown')
        current_time = time.time()
        MAX_REQUESTS_PER_HOUR = 10
        
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

def create_enhanced_prompt(user_message, routing_info=None):
    """Create an enhanced prompt based on task analysis"""
    if routing_info and routing_info.get("success"):
        category = routing_info.get("category", "general")
        complexity = routing_info.get("complexity_score", 0)
        
        system_prompts = {
            "coding": """You are an expert software developer. When responding to coding requests:
1. Provide clean, working code with comments
2. Explain the solution approach
3. Include error handling where appropriate
4. Suggest best practices and optimizations
5. Be precise and practical""",
            
            "debug": """You are a debugging expert. When helping with issues:
1. Analyze the problem systematically
2. Identify potential root causes
3. Provide step-by-step debugging approaches
4. Suggest preventive measures
5. Be thorough and methodical""",
            
            "design": """You are a UX/UI design expert. When helping with design:
1. Consider user experience principles
2. Suggest modern, accessible solutions
3. Think about responsive design
4. Recommend best practices
5. Be creative and user-focused""",
            
            "documentation": """You are a technical writer. When creating documentation:
1. Structure information clearly
2. Use simple, precise language
3. Include practical examples
4. Consider the audience level
5. Be comprehensive yet concise""",
            
            "analysis": """You are a data analyst. When analyzing information:
1. Look for patterns and insights
2. Provide data-driven recommendations
3. Consider multiple perspectives
4. Highlight key findings
5. Be objective and thorough"""
        }
        
        system_prompt = system_prompts.get(category, """You are a helpful AI assistant. When responding:
1. Be helpful, accurate, and concise
2. Provide practical and actionable results
3. Use clear and simple language
4. Consider context and intent
5. Be professional and courteous""")
        
        complexity_note = ""
        if complexity > 0.7:
            complexity_note = "\n\nNote: This appears to be a complex request. Take extra care to provide a thorough, well-structured response."
        
        return f"{system_prompt}{complexity_note}\n\nUser request: {user_message}"
    
    # Fallback to basic prompt
    return f"""You are a helpful AI assistant. Be helpful, accurate, and concise.
    
User request: {user_message}"""

def summarize_for_sms(text, max_length=160):
    """Enhanced summarization with better logic"""
    if len(text) <= max_length:
        return text
    
    # Try to preserve important information
    lines = text.split('\n')
    if len(lines) > 1:
        # If multi-line, try to get the first meaningful line
        for line in lines:
            line = line.strip()
            if line and len(line) <= max_length:
                return line
    
    # Try cursor agent for intelligent summarization
    if cursor_agent:
        summary_prompt = f"""Summarize this text in {max_length} characters or less for SMS. Keep the most important information:

{text}

Summary:"""
        
        try:
            result = cursor_agent.create_task(summary_prompt)
            if result["success"]:
                summary = result["response"].strip()
                if len(summary) <= max_length:
                    return summary
        except Exception as e:
            logger.error(f"Error in AI summarization: {e}")
    
    # Fallback to smart truncation
    if len(text) > max_length - 3:
        # Try to break at sentence or word boundary
        truncated = text[:max_length - 3]
        last_space = truncated.rfind(' ')
        last_period = truncated.rfind('.')
        
        if last_period > max_length * 0.7:  # If period is reasonably close to end
            return text[:last_period + 1]
        elif last_space > max_length * 0.8:  # If space is close to end
            return truncated[:last_space] + "..."
        else:
            return truncated + "..."
    
    return text

@app.route("/health", methods=['GET'])
def health_check():
    """Enhanced health check with system metrics"""
    try:
        # Get system metrics if task router is available
        if task_router:
            from admin_dashboard import AdminAnalytics
            analytics = AdminAnalytics()
            system_health = analytics.get_system_health()
            
            status = {
                "status": system_health["status"],
                "timestamp": datetime.now().isoformat(),
                "cursor_agent_available": cursor_agent is not None,
                "voice_assistant_available": voice_assistant is not None and voice_assistant.enable_voice,
                "twilio_available": twilio_client is not None,
                "task_router_available": task_router is not None,
                "notification_system_available": notification_system is not None,
                "metrics": {
                    "error_rate": system_health["error_rate"],
                    "avg_response_time": system_health["avg_response_time"],
                    "active_users_hour": system_health["active_users_hour"]
                }
            }
        else:
            status = {
                "status": "basic",
                "timestamp": datetime.now().isoformat(),
                "cursor_agent_available": cursor_agent is not None,
                "voice_assistant_available": voice_assistant is not None and voice_assistant.enable_voice,
                "twilio_available": twilio_client is not None,
                "task_router_available": False,
                "notification_system_available": False
            }
        
        return jsonify(status)
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

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
@enhanced_rate_limit
def sms_reply():
    """Enhanced SMS processing with routing and notifications"""
    start_time = time.time()
    
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')

    logger.info(f"Received message from {from_number}: '{incoming_msg}'")

    if not cursor_agent or not twilio_client:
        logger.error("A client (Cursor AI or Twilio) is not initialized. Cannot process request.")
        return Response(status=500)

    routing_info = getattr(request, 'routing_info', None)
    task_id = None

    try:
        # --- Step 1: Process the task with enhanced routing ---
        logger.info("Processing task with enhanced routing...")
        
        # Get routing configuration if available
        routing_config = {}
        if routing_info and routing_info.get("success"):
            task_id = routing_info.get("task_id")
            routing_config = routing_info.get("routing_decision", {})
            logger.info(f"Task routed: ID={task_id}, Category={routing_info.get('category')}, Priority={routing_info.get('priority')}")
        
        # Create enhanced prompt based on routing
        enhanced_prompt = create_enhanced_prompt(incoming_msg, routing_info)
        
        # Configure Cursor AI based on routing
        if routing_config:
            # You could pass routing config to cursor_agent here
            # For now, we'll use the standard approach
            pass
        
        result = cursor_agent.create_task(enhanced_prompt)

        if not result["success"]:
            logger.error(f"Cursor AI task failed: {result.get('error', 'Unknown error')}")
            
            # Mark task as failed if we have task tracking
            if task_id and task_router:
                processing_time = time.time() - start_time
                task_router.complete_task(task_id, "", processing_time, False)
            
            twilio_client.messages.create(
                body='Sorry, I encountered an error processing your request. Please try again.',
                from_=twilio_phone_number,
                to=from_number
            )
            return Response(str(MessagingResponse()), mimetype='application/xml')

        detailed_text = result["response"]
        task_type = result.get("task_type", "general")
        
        logger.info(f"Task completed (type: {task_type})")

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

        # --- Step 5: Complete task tracking and send notifications ---
        processing_time = time.time() - start_time
        
        if task_id and task_router:
            task_router.complete_task(task_id, sms_friendly_text, processing_time, True)
        
        # Send completion notification if notification system is available
        if notification_system and ADVANCED_FEATURES_AVAILABLE:
            try:
                task_data = {
                    'category': routing_info.get('category', 'general') if routing_info else 'general',
                    'processing_time': round(processing_time, 2)
                }
                # Run async notification
                asyncio.create_task(notify_task_completion(from_number, task_data))
            except Exception as e:
                logger.error(f"Error sending notification: {e}")

        # --- Step 6: Voice response handling ---
        if voice_response:
            try:
                logger.info("Voice response would be sent via MMS in production")
            except Exception as e:
                logger.error(f"Failed to send voice response: {e}")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        
        # Mark task as failed
        if task_id and task_router:
            processing_time = time.time() - start_time
            task_router.complete_task(task_id, "", processing_time, False)
        
        # Send system alert
        if notification_system and ADVANCED_FEATURES_AVAILABLE:
            try:
                asyncio.create_task(notify_system_alert(
                    "SMS Processing Error", 
                    "error", 
                    f"Error processing SMS from {from_number}: {str(e)}"
                ))
            except Exception:
                pass
        
        try:
            twilio_client.messages.create(
                body='Sorry, an unexpected error occurred. Please try again later.',
                from_=twilio_phone_number,
                to=from_number
            )
        except Exception as twilio_error:
            logger.error(f"Failed to send error message via Twilio: {twilio_error}")

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

# Background task to check system alerts
def check_system_alerts():
    """Background task to monitor system health and send alerts"""
    if not notification_system or not task_router:
        return
    
    try:
        from admin_dashboard import AdminAnalytics
        analytics = AdminAnalytics()
        
        # Get current metrics
        metrics = analytics.get_system_health()
        
        # Check alert conditions
        triggered_alerts = notification_system.check_alert_conditions(metrics)
        
        # Send alerts
        for alert in triggered_alerts:
            asyncio.create_task(notify_system_alert(
                alert['name'],
                alert['alert_level'],
                f"Alert triggered: {alert['name']} - Current metrics: {metrics}"
            ))
            
    except Exception as e:
        logger.error(f"Error in system alert check: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting Enhanced SMS-to-Cursor Agent on port {port} with debug={debug}")
    
    # Start background alert monitoring if components are available
    if notification_system and task_router and ADVANCED_FEATURES_AVAILABLE:
        import threading
        alert_thread = threading.Timer(300.0, check_system_alerts)  # Check every 5 minutes
        alert_thread.daemon = True
        alert_thread.start()
        logger.info("Started background alert monitoring")
    
    app.run(debug=debug, port=port, host='0.0.0.0')