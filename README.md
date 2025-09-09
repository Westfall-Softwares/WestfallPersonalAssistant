# Westfall Personal Assistant

A secure, enterprise-grade personal assistant with AI integration, featuring comprehensive security measures and robust credential management.

## 🔒 Security Features

This application implements comprehensive security measures including:

- ✅ **Secure Credential Storage**: All API keys and sensitive data stored using encryption
- ✅ **Environment Variable Configuration**: No hardcoded credentials in source code
- ✅ **Input Validation & Sanitization**: Comprehensive validation for all user inputs
- ✅ **Request Rate Limiting**: Protection against abuse and DoS attacks
- ✅ **Session Management**: Secure session handling with configurable timeouts
- ✅ **Content Filtering**: Protection against malicious input and prompt injection

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- PyQt5 (for desktop GUI components)
- Node.js (for web components)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Westfall-Softwares/WestfallPersonalAssistant.git
   cd WestfallPersonalAssistant
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your actual API keys and configuration
   nano .env  # or use your preferred editor
   ```

4. **Configure your API keys** (see [API Key Setup](#api-key-setup))

5. **Run the application**
   ```bash
   # For desktop GUI
   python main.py
   
   # For web server
   python app.py
   ```

## 🔑 API Key Setup

### Required API Keys

The application requires several API keys for full functionality:

#### 1. OpenAI API Key (for AI features)
- Visit: https://platform.openai.com/api-keys
- Create an account and generate an API key
- Add to `.env`: `OPENAI_API_KEY=your_openai_key_here`

#### 2. OpenWeatherMap API Key (for weather features)
- Visit: https://openweathermap.org/api
- Sign up for a free account
- Generate an API key
- Add to `.env`: `OPENWEATHER_API_KEY=your_weather_key_here`

#### 3. NewsAPI Key (for news features)
- Visit: https://newsapi.org/register
- Register for a free account
- Get your API key
- Add to `.env`: `NEWSAPI_KEY=your_news_key_here`

#### 4. Email Configuration (for email features)
Add to `.env`:
```
EMAIL_SMTP_HOST=your_smtp_server.com
EMAIL_SMTP_PORT=587
EMAIL_IMAP_HOST=your_imap_server.com
EMAIL_IMAP_PORT=993
EMAIL_USERNAME=your_email@example.com
EMAIL_PASSWORD=your_email_password
EMAIL_USE_TLS=true
EMAIL_USE_SSL=true
```

### Security Best Practices

1. **Never commit API keys to version control**
   - The `.env` file is already in `.gitignore`
   - Use strong, unique API keys
   - Rotate your API keys regularly

2. **Use environment-specific configurations**
   - Different `.env` files for development, staging, and production
   - Use secure secret management in production environments

3. **Monitor API usage**
   - Check your API usage regularly
   - Set up billing alerts for paid APIs
   - Use API key rotation for enhanced security

## 🛠️ Configuration

### Environment Variables

The application uses environment variables for configuration. Here are the key variables:

#### Security Settings
```bash
SESSION_TIMEOUT_MINUTES=30          # Session timeout
MAX_REQUESTS_PER_MINUTE=60          # Rate limiting
MAX_TOKENS_PER_HOUR=100000          # Token usage limit
API_KEY_VAULT_ENCRYPTION_KEY=...    # Encryption key for API key vault
```

#### Feature Flags
```bash
BUSINESS_FEATURES_ENABLED=false     # Enable business dashboard
CRM_ENABLED=false                   # Enable CRM features
FINANCE_TRACKING_ENABLED=false     # Enable finance tracking
SCREEN_CAPTURE_ENABLED=false       # Enable screen capture
AUTOMATION_ENABLED=false           # Enable automation features
WEB_SEARCH_ENABLED=true            # Enable web search
```

#### Application Settings
```bash
DEBUG_MODE=false                    # Debug mode
LOG_LEVEL=INFO                      # Logging level
THEME_MODE=auto                     # UI theme (auto/light/dark)
```

### Configuration Files

- **`.env`**: Environment variables (create from `.env.example`)
- **`config/settings.py`**: Main application settings
- **`config/app_config.py`**: Application configuration wrapper
- **`data/settings.json`**: Persistent user settings

## 🔧 Development

### Project Structure

```
WestfallPersonalAssistant/
├── backend/                    # Backend services
│   ├── security/              # Security modules
│   │   ├── input_validation.py    # Input validation & sanitization
│   │   ├── auth_manager.py         # Authentication management
│   │   └── api_key_vault.py        # Secure API key storage
│   └── server.py              # Backend server
├── config/                    # Configuration files
│   ├── settings.py            # Main settings
│   └── app_config.py          # Application configuration
├── core/                      # Core application logic
├── routes/                    # API routes
│   └── api_routes.py          # Web API endpoints
├── services/                  # Service modules
│   ├── email_service.py       # Email functionality
│   ├── weather_service.py     # Weather integration
│   └── news_service.py        # News integration
├── util/                      # Utility modules
├── tests/                     # Test files
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

### Running Tests

```bash
# Run security tests
python test_security.py

# Run unit tests (if pytest is available)
python -m pytest tests/

# Test specific modules
python -c "from config.app_config import get_app_config; print('Config OK')"
```

### Adding New Features

1. **Security First**: All new features must implement proper input validation
2. **Environment Configuration**: Use environment variables for any configuration
3. **Error Handling**: Implement comprehensive error handling
4. **Documentation**: Update this README and add inline documentation

## 🛡️ Security Considerations

### Input Validation

All user inputs are validated and sanitized:

```python
from backend.security.input_validation import input_validator

# Sanitize user input
safe_input = input_validator.sanitize_string(user_input, max_length=1000)

# Check for suspicious patterns
if input_validator.contains_suspicious_patterns(user_input):
    # Handle suspicious input
    pass
```

### API Endpoint Security

All API endpoints include:
- Request validation decorators
- Input sanitization
- Rate limiting
- Error handling
- Content-length limits

### Credential Management

- API keys stored in encrypted vault
- Environment variable fallbacks
- No hardcoded credentials
- Secure session management

## 🚨 Troubleshooting

### Common Issues

1. **Missing API Keys**
   - Check your `.env` file
   - Verify API key validity
   - Check API usage limits

2. **Import Errors**
   - Install missing dependencies: `pip install -r requirements.txt`
   - Check Python version compatibility

3. **Permission Errors**
   - Ensure proper file permissions
   - Check data directory access

4. **Service Unavailable**
   - Verify internet connectivity
   - Check API service status
   - Review rate limiting settings

### Getting Help

1. Check the logs: `logs/assistant.log`
2. Run the security test: `python test_security.py`
3. Verify configuration: Check `.env` file
4. Review API usage and limits

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement security best practices
4. Add tests for new features
5. Update documentation
6. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the security documentation

---

**Security Notice**: This application handles sensitive data and API keys. Always follow security best practices and keep your dependencies updated.