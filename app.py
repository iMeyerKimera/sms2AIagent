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
    model = genai.GenerativeModel('gemini-2.0-flash')
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

    # Get the message body and sender's number from the incoming request
    incoming_msg = request.values.get('Body', '').strip()
    from_number = request.values.get('From', '')

    print(f"Received message from {from_number}: '{incoming_msg}'")

    if not model or not twilio_client:
        print("A client (Gemini or Twilio) is not initialized. Cannot process request.")
        return Response(status=500)

    try:
        # --- Step 1: Perform the main task with the AI agent ---
        # This is where you would integrate the "Cursor AI" agent.
        # We are using Gemini here as a powerful, general-purpose agent.
        print("Asking AI agent to perform the main task...")
        main_task_prompt = incoming_msg
        main_result = model.generate_content(main_task_prompt)
        detailed_text = main_result.text
        print("AI agent generated a detailed response.")

        # --- Step 2: Summarize the result for SMS ---
        print("Asking AI agent to summarize the response for SMS...")
        summary_prompt = f'Please summarize the following text to be under 160 characters, suitable for an SMS message. Be concise and direct. Text: "{detailed_text}"'
        summary_result = model.generate_content(summary_prompt)
        sms_friendly_text = summary_result.text
        print(f"Generated SMS-friendly summary: '{sms_friendly_text}'")

        # --- Step 3: Send the summary back to the user via Twilio ---
        twilio_client.messages.create(
            body=sms_friendly_text,
            from_=twilio_phone_number,
            to=from_number
        )
        print(f"Successfully sent summary to {from_number}")

    except Exception as e:
        print(f"An error occurred: {e}")
        # --- Error Handling: Inform the user if something went wrong ---
        try:
            twilio_client.messages.create(
                body='Sorry, I encountered an error and could not process your request. Please try again.',
                from_=twilio_phone_number,
                to=from_number
            )
        except Exception as twilio_error:
            print(f"Failed to send error message via Twilio: {twilio_error}")

    # Return an empty TwiML response to acknowledge receipt of the message
    return Response(str(MessagingResponse()), mimetype='application/xml')


if __name__ == "__main__":
    # This block is for local development without Docker
    # When using Docker, the `flask run` command is used instead.
    app.run(debug=True, port=5000)