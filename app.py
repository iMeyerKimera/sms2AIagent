import os
from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# --- Initialize Clients ---

# Initialize Gemini AI Client
try:
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")
    genai.configure(api_key=google_api_key)
    # Added safety_settings to be less restrictive. Tune if needed.
    model = genai.GenerativeModel(
        'gemini-2.0-flash',
        safety_settings={
            'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
            'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
            'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
            'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE'
        }
    )
except Exception as e:
    print(f"Error initializing Google AI Client: {e}")
    model = None

# Initialize Twilio Client
try:
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    twilio_phone_number = os.environ.get("TWILIO_PHONE_NUMBER")
    if not all([account_sid, auth_token, twilio_phone_number]):
        raise ValueError("Twilio credentials not fully set in environment variables.")
    twilio_client = Client(account_sid, auth_token)
except Exception as e:
    print(f"Error initializing Twilio Client: {e}")
    twilio_client = None


@app.route("/sms", methods=['POST'])
def sms_reply():
    """Receive SMS from Twilio, process with AI, and send reply."""

    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')

    print(f"Received message from {from_number}: '{incoming_msg}'")

    if not model or not twilio_client:
        print("A client (Gemini or Twilio) is not initialized. Cannot process request.")
        return Response(status=500)

    try:
        # --- Step 1: Perform the main task with the AI agent ---
        print("Asking AI agent to perform the main task...")
        main_result = model.generate_content(incoming_msg)

        # ADDED: Robust check for response content.
        # This handles cases where the API blocks the prompt for safety reasons.
        try:
            detailed_text = main_result.text
        except ValueError:
            # If .text fails, it's likely the prompt was blocked.
            print(f"AI response was blocked. Feedback: {main_result.prompt_feedback}")
            twilio_client.messages.create(
                body='Sorry, your request could not be processed. It may have been blocked for safety reasons. Please try a different prompt.',
                from_=twilio_phone_number,
                to=from_number
            )
            # Acknowledge the request was received and handled.
            return Response(str(MessagingResponse()), mimetype='application/xml')

        print("AI agent generated a detailed response.")

        # --- Step 2: Summarize the result for SMS ---
        print("Asking AI agent to summarize the response for SMS...")
        summary_prompt = f'Please summarize the following text to be under 160 characters, suitable for an SMS message. Be concise and direct. Text: "{detailed_text}"'
        summary_result = model.generate_content(summary_prompt)

        try:
            sms_friendly_text = summary_result.text
        except ValueError:
            print(f"AI summary response was blocked. Feedback: {summary_result.prompt_feedback}")
            # Fallback to a simple truncation if summarization fails
            sms_friendly_text = (detailed_text[:155] + '...') if len(detailed_text) > 155 else detailed_text

        print(f"Generated SMS-friendly summary: '{sms_friendly_text}'")

        # --- Step 3: Send the summary back to the user via Twilio ---
        twilio_client.messages.create(
            body=sms_friendly_text,
            from_=twilio_phone_number,
            to=from_number
        )
        print(f"Successfully sent summary to {from_number}")

    except Exception as e:
        # This will now catch other unexpected errors (e.g., network issues, invalid API key)
        print(f"An unexpected error occurred: {e}")
        try:
            twilio_client.messages.create(
                body='Sorry, an unexpected error occurred and I could not process your request. Please check the server logs.',
                from_=twilio_phone_number,
                to=from_number
            )
        except Exception as twilio_error:
            print(f"Failed to send error message via Twilio: {twilio_error}")

    # Return an empty TwiML response to acknowledge receipt of the message
    return Response(str(MessagingResponse()), mimetype='application/xml')


if __name__ == "__main__":
    app.run(debug=True, port=5000)