# 🤝 Contributing to SMS-to-AI Agent

Thank you for your interest in contributing to SMS-to-AI Agent! This document provides guidelines and best practices for contributing to the project.

---

## 📋 **Table of Contents**

- [Code of Conduct](#-code-of-conduct)
- [Getting Started](#-getting-started)
- [Development Setup](#-development-setup)
- [Code Style and Standards](#-code-style-and-standards)
- [Security Guidelines](#-security-guidelines)
- [Pull Request Process](#-pull-request-process)
- [Issue Reporting](#-issue-reporting)
- [Testing Guidelines](#-testing-guidelines)
- [Documentation](#-documentation)
- [Release Process](#-release-process)
- [Acknowledgment](#-acknowledgments)

---

## 📜 **Code of Conduct**

### **Our Standards**

We are committed to providing a welcoming and inspiring community for all. By participating in this project, you agree to:

- **Be respectful** and inclusive of all contributors
- **Be collaborative** and open to constructive feedback
- **Be professional** in all interactions
- **Be responsible** for your contributions and their impact

### **Unacceptable Behavior**

- Harassment, discrimination, or offensive behavior
- Trolling, insulting, or derogatory comments
- Publishing others' private information without permission
- Any conduct inappropriate in a professional setting

### **Reporting Issues**

If you experience or witness unacceptable behavior, please report it to the project maintainers.

---

## 🚀 **Getting Started**

### **Before You Start**

1. **Check existing issues** to avoid duplicate work
2. **Read the documentation** to understand the project structure
3. **Join discussions** in GitHub Issues or Discussions
4. **Start small** with bug fixes or documentation improvements

### **Types of Contributions**

- 🐛 **Bug fixes** - Help improve stability
- ✨ **New features** - Add functionality
- 📚 **Documentation** - Improve guides and docs
- 🧪 **Tests** - Add or improve test coverage
- 🔧 **Refactoring** - Improve code quality
- 🚀 **Performance** - Optimize performance
- 🔒 **Security** - Fix security vulnerabilities

---

## 🛠️ **Development Setup**

### **Prerequisites**

- Python 3.8+
- Docker and Docker Compose
- Git
- A code editor (VS Code recommended)

### **Local Development Setup**

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/sms2AIagent.git
cd sms2AIagent

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp env.example .env
# Edit .env with your development credentials

# 5. Start development services
docker-compose up -d

# 6. Run migrations
python manage.py migrate

# 7. Create a superuser (optional)
python manage.py createsuperuser

# 8. Start the development server
python manage.py runserver
```

### **Pre-commit Setup**

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run pre-commit on all files
pre-commit run --all-files
```

---

## 📝 **Code Style and Standards**

### **Python Code Style**

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) and use the following tools:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

### **Configuration Files**

#### **pyproject.toml**
```toml
[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
multi_line_output = 3
```

#### **.flake8**
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist,*.egg-info
```

### **Code Style Guidelines**

#### **Naming Conventions**
- **Functions and variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Files**: `snake_case.py`

#### **Documentation**
- Use docstrings for all public functions and classes
- Follow Google docstring format
- Include type hints for function parameters and return values

#### **Example**
```python
def process_sms_message(message: str, user_id: int) -> dict[str, any]:
    """Process an incoming SMS message and route to appropriate AI service.
    
    Args:
        message: The SMS message content
        user_id: The ID of the user sending the message
        
    Returns:
        A dictionary containing the processed response and metadata
        
    Raises:
        ValueError: If message is empty or invalid
    """
    if not message.strip():
        raise ValueError("Message cannot be empty")
    
    # Process the message
    response = ai_service.process(message, user_id)
    
    return {
        "response": response,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat()
    }
```

---

## 🔒 **Security Guidelines**

### **Security Best Practices**

#### **Code Security**
- **Never commit secrets** (API keys, passwords, tokens)
- **Use environment variables** for sensitive configuration
- **Validate all inputs** to prevent injection attacks
- **Use parameterized queries** for database operations
- **Implement proper authentication** and authorization
- **Follow OWASP guidelines** for web security

#### **Secret Management**
```python
# ✅ Good - Use environment variables
import os
from django.conf import settings

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# ❌ Bad - Hardcoded secrets
api_key = "sk-1234567890abcdef"  # Never do this!
```

#### **Input Validation**
```python
# ✅ Good - Validate inputs
import re
from django.core.exceptions import ValidationError

def validate_phone_number(phone: str) -> str:
    """Validate and sanitize phone number input."""
    # Remove all non-digit characters
    cleaned = re.sub(r'\D', '', phone)
    
    if len(cleaned) < 10:
        raise ValidationError("Phone number must have at least 10 digits")
    
    return cleaned

# ❌ Bad - No validation
def process_phone(phone: str) -> str:
    return phone  # Dangerous!
```

#### **Database Security**
```python
# ✅ Good - Use parameterized queries
from django.db import connection

def get_user_messages(user_id: int) -> list:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM messages WHERE user_id = %s",
            [user_id]  # Parameterized query
        )
        return cursor.fetchall()

# ❌ Bad - String concatenation (SQL injection risk)
def get_user_messages(user_id: int) -> list:
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM messages WHERE user_id = {user_id}")  # Dangerous!
        return cursor.fetchall()
```

### **Security Checklist**

Before submitting a PR, ensure:

- [ ] No hardcoded secrets or credentials
- [ ] All inputs are properly validated
- [ ] Database queries use parameterized statements
- [ ] Authentication and authorization are implemented
- [ ] Error messages don't leak sensitive information
- [ ] Dependencies are up to date
- [ ] Security headers are properly configured
- [ ] HTTPS is enforced in production

---

## 🔄 **Pull Request Process**

### **Before Creating a PR**

1. **Ensure your code follows style guidelines**
2. **Write or update tests** for your changes
3. **Update documentation** if needed
4. **Test your changes** thoroughly
5. **Check for security issues**

### **Creating a Pull Request**

#### **PR Title Format**
```
type(scope): brief description

Examples:
feat(sms): add support for WhatsApp integration
fix(auth): resolve session timeout issue
docs(api): update API documentation
test(core): add unit tests for message processing
```

#### **PR Description Template**
```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Security review completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No hardcoded secrets
- [ ] Input validation implemented
- [ ] Error handling added

## Related Issues
Closes #123
```

### **PR Review Process**

1. **Automated checks** must pass (CI/CD)
2. **Code review** by maintainers
3. **Security review** for sensitive changes
4. **Testing verification**
5. **Documentation review**

### **Merging Guidelines**

- **Squash and merge** for feature branches
- **Rebase and merge** for hotfixes
- **Create merge commit** for major releases
- **Delete branch** after successful merge

---

## 🐛 **Issue Reporting**

### **Bug Report Template**

```markdown
## Bug Description
Clear and concise description of the bug

## Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
What you expected to happen

## Actual Behavior
What actually happened

## Environment
- OS: [e.g. macOS, Windows, Linux]
- Python Version: [e.g. 3.8.10]
- Django Version: [e.g. 3.2.0]
- Browser: [e.g. Chrome, Firefox]

## Additional Context
Any other context about the problem

## Screenshots
If applicable, add screenshots to help explain the problem
```

### **Feature Request Template**

```markdown
## Feature Description
Clear and concise description of the feature

## Problem Statement
What problem does this feature solve?

## Proposed Solution
How would you like this feature to work?

## Alternative Solutions
Any alternative solutions you've considered

## Additional Context
Any other context or screenshots about the feature request
```

---

## 🧪 **Testing Guidelines**

### **Test Structure**

```
tests/
├── unit/
│   ├── test_models.py
│   ├── test_views.py
│   └── test_services.py
├── integration/
│   ├── test_api.py
│   └── test_sms_processing.py
└── fixtures/
    └── test_data.json
```

### **Writing Tests**

#### **Unit Tests**
```python
import pytest
from unittest.mock import patch
from django.test import TestCase
from core.models import User, Message

class TestMessageProcessing(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="testuser",
            email="test@example.com"
        )
    
    def test_message_creation(self):
        """Test that messages are created correctly."""
        message = Message.objects.create(
            user=self.user,
            content="Test message",
            message_type="sms"
        )
        
        self.assertEqual(message.content, "Test message")
        self.assertEqual(message.user, self.user)
        self.assertEqual(message.message_type, "sms")
    
    @patch('core.services.ai_service.process')
    def test_ai_processing(self, mock_ai_process):
        """Test AI processing integration."""
        mock_ai_process.return_value = "AI response"
        
        result = ai_service.process_message("Hello", self.user.id)
        
        self.assertEqual(result, "AI response")
        mock_ai_process.assert_called_once_with("Hello", self.user.id)
```

#### **Integration Tests**
```python
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

class TestSMSAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
    
    def test_sms_endpoint(self):
        """Test SMS processing endpoint."""
        url = reverse('sms-process')
        data = {
            'message': 'Hello, world!',
            'phone_number': '+1234567890'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('response', response.data)
```

### **Test Coverage**

- **Minimum coverage**: 80%
- **Critical paths**: 100% coverage
- **New features**: Must include tests
- **Bug fixes**: Must include regression tests

### **Running Tests**

```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html

# Run specific test file
python manage.py test tests.unit.test_models

# Run with verbose output
python manage.py test -v 2
```

---

## 📚 **Documentation**

### **Documentation Standards**

- **Clear and concise** writing
- **Code examples** for all features
- **Step-by-step guides** for complex processes
- **Regular updates** with code changes

### **Documentation Structure**

```
docs/
├── getting-started/
│   ├── INSTALLATION.md
│   └── QUICK_START.md
├── user-guides/
│   ├── USER_GUIDE.md
│   └── ADMIN_GUIDE.md
├── development/
│   ├── ARCHITECTURE.md
│   └── API_REFERENCE.md
└── operations/
    ├── DEPLOYMENT.md
    └── TROUBLESHOOTING.md
```

### **Writing Documentation**

#### **Code Documentation**
```python
def process_sms_message(message: str, user_id: int) -> dict[str, any]:
    """Process an incoming SMS message and route to appropriate AI service.
    
    This function takes a raw SMS message and processes it through the AI
    pipeline to generate an appropriate response. It handles message
    validation, user authentication, and response formatting.
    
    Args:
        message: The SMS message content. Must be non-empty string.
        user_id: The ID of the user sending the message. Must be valid user ID.
        
    Returns:
        A dictionary containing:
            - response: The AI-generated response text
            - user_id: The ID of the user
            - timestamp: ISO format timestamp of processing
            - confidence: AI confidence score (0.0 to 1.0)
        
    Raises:
        ValueError: If message is empty or user_id is invalid
        AuthenticationError: If user is not authenticated
        ProcessingError: If AI processing fails
        
    Example:
        >>> result = process_sms_message("Hello, how are you?", 123)
        >>> print(result['response'])
        "I'm doing well, thank you for asking!"
    """
```

#### **API Documentation**
```markdown
## POST /api/sms/process

Process an incoming SMS message through the AI pipeline.

### Request Body
```json
{
    "message": "string",
    "phone_number": "string",
    "user_id": "integer"
}
```

### Response
```json
{
    "response": "string",
    "user_id": "integer",
    "timestamp": "string",
    "confidence": "float"
}
```

### Status Codes
```
- `200 OK`: Message processed successfully
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Authentication required
- `500 Internal Server Error`: Processing failed
```

---

## 🚀 **Release Process**

### **Version Numbering**

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH**
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### **Release Checklist**

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Security review completed
- [ ] Performance testing done
- [ ] Changelog updated
- [ ] Version number updated
- [ ] Release notes written
- [ ] Deployment tested

### **Creating a Release**

1. **Update version** in `__init__.py`
2. **Update changelog** with new features/fixes
3. **Create release branch** from main
4. **Run full test suite**
5. **Create GitHub release**
6. **Deploy to production**
7. **Announce release**

---

## 📞 **Getting Help**

### **Community Resources**

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: [Complete Documentation](docs/README.md)

### **Contributor Resources**

- **Development Guide**: [Development Documentation](docs/development/)
- **API Reference**: [API Documentation](docs/user-guides/API_REFERENCE.md)
- **Architecture**: [System Architecture](docs/development/ARCHITECTURE.md)

---

## 🙏 **Acknowledgments**

Thank you to all contributors who have helped make SMS-to-AI Agent better! Your contributions are valued and appreciated.

### **👨‍💻 Original Developer**

- **[iMeyerKimera](https://github.com/iMeyerKimera)** - Initial creator and architect of SMS-to-AI Agent. Thank you for envisioning and building the foundation of this project!

### **Open Source Projects That Made This Possible**

SMS-to-AI Agent is built on the shoulders of many amazing open source projects. We extend our deepest gratitude to:

#### **🏗️ Core Framework**
- **[Django](https://www.djangoproject.com/)** - The web framework for perfectionists with deadlines
- **[Django REST Framework](https://www.django-rest-framework.org/)** - Powerful and flexible toolkit for building Web APIs
- **[Django CORS Headers](https://github.com/adamchainz/django-cors-headers)** - Django app for handling server headers required for CORS

#### **🤖 AI and Machine Learning**
- **[OpenAI Python](https://github.com/openai/openai-python)** - The official Python library for the OpenAI API
- **[Cursor AI](https://cursor.sh/)** - AI-powered code editor and development assistant

#### **📱 Communication Services**
- **[Twilio Python](https://github.com/twilio/twilio-python)** - Python SDK for Twilio APIs
- **[SpeechRecognition](https://github.com/Uberi/speech_recognition)** - Speech recognition library for Python
- **[pyttsx3](https://github.com/nateshmbhat/pyttsx3)** - Text-to-speech conversion library

#### **🗄️ Database and Caching**
- **[PostgreSQL](https://www.postgresql.org/)** - The world's most advanced open source relational database
- **[psycopg2](https://www.psycopg.org/)** - PostgreSQL adapter for Python
- **[Redis](https://redis.io/)** - In-memory data structure store
- **[redis-py](https://github.com/redis/redis-py)** - Redis Python client

#### **🚀 Deployment and Infrastructure**
- **[Docker](https://www.docker.com/)** - Containerization platform
- **[Docker Compose](https://docs.docker.com/compose/)** - Multi-container Docker applications
- **[Gunicorn](https://gunicorn.org/)** - Python WSGI HTTP Server for UNIX
- **[nginx](https://nginx.org/)** - High performance HTTP server and reverse proxy

#### **🛠️ Development Tools**
- **[Python](https://www.python.org/)** - Programming language that lets you work quickly and integrate systems effectively
- **[pip](https://pip.pypa.io/)** - Package installer for Python
- **[virtualenv](https://virtualenv.pypa.io/)** - Virtual Python environment builder
- **[Git](https://git-scm.com/)** - Distributed version control system

#### **📊 Monitoring and Utilities**
- **[psutil](https://github.com/giampaolo/psutil)** - Cross-platform library for retrieving information on running processes
- **[requests](https://requests.readthedocs.io/)** - HTTP library for Python
- **[python-dateutil](https://github.com/dateutil/dateutil)** - Extensions to the standard Python datetime module
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** - Read key-value pairs from a .env file

#### **🎨 Frontend and UI**
- **[Bootstrap](https://getbootstrap.com/)** - CSS framework for developing responsive and mobile-first websites
- **[jQuery](https://jquery.com/)** - JavaScript library designed to simplify HTML DOM tree traversal and manipulation
- **[Chart.js](https://www.chartjs.org/)** - Simple yet flexible JavaScript charting library

#### **🔧 Development and Testing**
- **[pytest](https://pytest.org/)** - Framework that makes building simple and scalable test cases easy
- **[coverage.py](https://coverage.readthedocs.io/)** - Code coverage measurement for Python
- **[Black](https://black.readthedocs.io/)** - Uncompromising Python code formatter
- **[isort](https://pycqa.github.io/isort/)** - Python utility/library to sort imports alphabetically
- **[flake8](https://flake8.pycqa.org/)** - Python style guide enforcement tool
- **[mypy](https://mypy.readthedocs.io/)** - Static type checker for Python

#### **📚 Documentation and Community**
- **[GitHub](https://github.com/)** - Platform for version control and collaboration
- **[Markdown](https://daringfireball.net/projects/markdown/)** - Lightweight markup language
- **[Read the Docs](https://readthedocs.org/)** - Documentation hosting platform
- **[Stack Overflow](https://stackoverflow.com/)** - Developer community and knowledge base

### **Special Thanks**

- **Django Software Foundation** - For creating and maintaining the incredible Django framework
- **OpenAI Team** - For advancing AI technology and making it accessible to developers
- **Twilio Team** - For revolutionizing communication APIs
- **PostgreSQL Global Development Group** - For the world's most advanced open source database
- **Redis Team** - For the lightning-fast in-memory data store
- **Docker Team** - For containerization technology that revolutionized deployment

### **Community Contributors**

We're grateful to the open source community for:
- **Bug reports** that help improve stability
- **Feature requests** that guide development
- **Code contributions** that enhance functionality
- **Documentation improvements** that help users
- **Testing and feedback** that ensure quality

### **License Acknowledgments**

This project uses the MIT License, which allows for maximum freedom while requiring minimal attribution. We believe in the power of open source collaboration and are committed to giving back to the community.

---

**Last Updated**: July 22, 2025
**Version**: 1.0 