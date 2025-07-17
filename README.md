# SMS-to-Gemini AI System

A system that allows you to send tasks to an AI agent via SMS and receive SMS-friendly summaries of completed work back on your phone.

## Features

- **SMS Integration**: Send tasks via text message to your AI agent
- **AI-Powered Processing**: Uses Google's Gemini AI to handle complex tasks
- **SMS-Friendly Responses**: Automatically summarizes results to fit SMS character limits
- **Docker Deployment**: Easy containerized deployment with ngrok for webhook exposure
- **Error Handling**: Robust error handling and fallback mechanisms

## Prerequisites

- Python 3.1 Docker and Docker Compose
- Twilio account (for SMS functionality)
- Google AI API key (for Gemini AI)
- Ngrok account (for exposing local server)

## Quick Start

### 1 Clone and Setup

```bash
git clone <repository-url>
cd sms2AIagent
```

### 2. Configure Environment Variables

Copy the example environment file and configure your credentials:

```bash
cp env.example .env
```

Edit `.env` with your actual credentials:

```env
# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890e AI Configuration
GOOGLE_API_KEY=your_google_api_key_here

# Ngrok Configuration
NGROK_AUTHTOKEN=your_ngrok_auth_token_here
```

### 3. Start the System

```bash
docker-compose up --build
```

### 4. Configure Twilio Webhook1 Go to your Twilio Console
2. Navigate to Phone Numbers → Manage → Active numbers
3. Click on your phone number
4et the webhook URL for incoming messages to:
   ```
   https://your-ngrok-url.ngrok-free.app/sms
   ```
5. Set the HTTP method to POST

### 5 Test the System

Send an SMS to your Twilio phone number with a task like:
- "Write a short poem about coding"
- "Explain quantum computing in simple terms
- Create a todo list for a weekend project
## How It Works1. **Receive SMS**: Twilio receives your SMS and forwards it to the Flask webhook
2**AI Processing**: The system sends your task to Google's Gemini AI for processing
3**Summarization**: The AI response is automatically summarized to fit SMS character limits
4. **Response**: The summarized result is sent back to your phone via SMS

## Configuration Options

### AI Model Settings

You can customize the AI behavior by modifying these settings in `app.py`:

```python
# Change the AI model
model = genai.GenerativeModel('gemini-2.0-flash')

# Adjust safety settings
safety_settings =[object Object]  HARM_CATEGORY_HATE_SPEECH':BLOCK_NONE,    HARM_CATEGORY_HARASSMENT':BLOCK_NONE,    HARM_CATEGORY_SEXUALLY_EXPLICIT':BLOCK_NONE,  HARM_CATEGORY_DANGEROUS_CONTENT: LOCK_NONE'
}
```

### SMS Length Limits

The system automatically summarizes responses to fit SMS limits. You can adjust this in the environment variables:

```env
MAX_SMS_LENGTH=160
```

## Development

### Local Development (without Docker)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

### Testing

The system includes basic error handling and logging. Check the console output for debugging information.

## Troubleshooting

### Common Issues
1**"A client is not initialized"**: Check your environment variables are properly set2**"AI response was blocked"**: The AI model blocked your request for safety reasons
3. **Ngrok connection issues**: Verify your ngrok authtoken is correct
4. **Twilio webhook not receiving messages**: Ensure the webhook URL is correctly configured

### Logs

Check the Docker logs for detailed error information:

```bash
docker-compose logs web
docker-compose logs ngrok
```

## Security Considerations

- Keep your API keys secure and never commit them to version control
- The `.env` file is already in `.gitignore` for security
- Consider implementing rate limiting for production use
- Review and adjust AI safety settings based on your use case

## API Endpoints

- `POST /sms`: Main webhook endpoint for receiving SMS messages from Twilio

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 