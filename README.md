## Key Features

### 🧠 AI-Powered Intelligence
- **Multimodal Understanding**: Process text, images, and voice through LLaVA integration
- **Contextual Memory**: Remembers conversation history for more natural interactions
- **Adaptive Responses**: Tailors answers based on your preferences and past interactions

### 🗣️ Voice Interaction
- **Speech Recognition**: Speak naturally to your assistant
- **Voice Output**: Responses can be read aloud with natural-sounding voice
- **Voice Commands**: Quick actions through voice shortcuts

### 📅 Scheduling & Time Management
- **Calendar Integration**: Connect with Google Calendar
- **Appointment Scheduling**: Create, modify, and cancel appointments
- **Reminders**: Set and manage reminders for important tasks
- **Time Tracking**: Monitor time spent on different activities

### 📧 Email Management
- **Email Composition**: Draft emails with AI assistance
- **Email Summarization**: Get concise summaries of your inbox
- **Smart Filtering**: Prioritize important messages
- **Quick Responses**: Generate appropriate responses to common emails

### 🌦️ Weather & News
- **Weather Forecasts**: Current conditions and forecasts for any location
- **Personalized News**: Curated news based on your interests
- **Alerts**: Notifications for severe weather or breaking news

### 🔍 Web Research
- **Information Retrieval**: Find answers to questions from the web
- **Data Summarization**: Condense lengthy articles into key points
- **Source Verification**: Check reliability of information sources

### 📝 Notes & Documentation
- **Smart Note-Taking**: Create, organize, and search notes
- **Transcription**: Convert voice to text for documentation
- **Content Generation**: Help draft documents, emails, and messages

### 📊 Knowledge Management
- **Personal Knowledge Base**: Store and retrieve your important information
- **Learning Mode**: Teach the assistant about your preferences and specialized knowledge
- **Document Analysis**: Extract insights from documents and files

### ⚙️ Customization & Extensions
- **Personalized Settings**: Configure the assistant to your preferences
- **Custom Commands**: Create shortcuts for frequent tasks
- **Integration Capability**: Connect with other services and tools
- **Workflow Automation**: Create automated sequences of tasks

## Installation

### System Requirements
- Python 3.8+ 
- 8GB RAM minimum (16GB recommended)
- 2GB free disk space
- Internet connection for online services
- Microphone (for voice features)
- Speakers (for voice output)

### Basic Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Westfall-Softwares/WestfallPersonalAssistant.git
   cd WestfallPersonalAssistant
   ```

2. **Create a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the assistant**
   ```bash
   python main.py
   ```

### Docker Installation

For a containerized installation:

1. **Build the Docker image**
   ```bash
   docker build -t westfall-assistant .
   ```

2. **Run the container**
   ```bash
   docker run -p 5000:5000 -v $(pwd)/data:/app/data westfall-assistant
   ```

### One-Line Quick Start

```bash
curl -sSL https://raw.githubusercontent.com/Westfall-Softwares/WestfallPersonalAssistant/main/install.sh | bash
```

## Configuration

### First-Time Setup

When you first run the assistant, it will guide you through the configuration process within the application. You can access settings at any time by:

- Clicking the gear icon in the main interface
- Using the keyboard shortcut `Ctrl+,` (or `Cmd+,` on Mac)

### API Keys

The following API keys can be configured directly in the settings interface:

- **OpenWeather API**: For weather forecasts ([Get key here](https://openweathermap.org/api))
- **News API**: For news features ([Get key here](https://newsapi.org))
- **Gmail API**: For email integration
- **Google Calendar API**: For calendar features
- **Azure Speech API**: For enhanced voice recognition (optional)

### Advanced Configuration

For advanced users, you can manually create a `.env` file based on the provided `.env.example`:

```bash
# Copy example configuration
cp .env.example .env

# Edit with your preferred text editor
nano .env
```

## Usage

### Starting the Assistant

```bash
python main.py
```

The assistant will be available at:
- **Web Interface**: http://localhost:5000
- **Command Line**: Direct interaction in the terminal
- **Voice Interface**: Start speaking after the assistant is running

### Voice Commands

Start voice commands with the wake word "Westfall" followed by your request:

- "Westfall, what's the weather today?"
- "Westfall, schedule a meeting with John tomorrow at 3 PM"
- "Westfall, send an email to Sarah about the project update"

### Text Commands

Type commands directly in the input field of the web interface or command line:

- `/weather [location]` - Get weather forecast
- `/email [recipient] [subject]` - Start composing an email
- `/schedule [event] [time]` - Create a calendar event
- `/note [text]` - Create a new note
- `/news [topic]` - Get latest news

### Keyboard Shortcuts

- `Ctrl+,` - Open settings
- `Ctrl+H` - View command history
- `Ctrl+N` - New conversation
- `Ctrl+S` - Save conversation
- `Ctrl+V` - Toggle voice mode
- `Esc` - Cancel current operation

## Advanced Usage

### Custom Commands

Create custom commands in the settings interface:

1. Go to Settings → Custom Commands
2. Click "Add New Command"
3. Define trigger phrase and action
4. Save your custom command

Example custom command:
- **Trigger**: "morning routine"
- **Action**: Get weather, today's calendar, and top news

### API Integration

WestfallPersonalAssistant provides a REST API for integration with other applications:

```bash
# Example API request
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the weather in New York?", "context": "weather"}'
```

API documentation is available at: http://localhost:5000/api/docs

### LLaVA Model Customization

For advanced AI customization:

1. Place custom models in the `models/llava/` directory
2. Update the model path in settings
3. Restart the assistant

Supported model formats:
- LLaVA (default)
- GGUF
- ONNX

### Extending Functionality

Create plugins in the `plugins/` directory:

```python
# Example plugin: plugins/custom_service.py
from core.plugin import WestfallPlugin

class CustomService(WestfallPlugin):
    def __init__(self):
        super().__init__(name="custom_service", version="1.0")
    
    def process(self, query, context=None):
        return {"result": f"Custom processing: {query}"}
```

## Troubleshooting

### Common Issues

#### Assistant fails to start
```
# Check if required directories exist
mkdir -p logs data models/llava tmp

# Verify Python version
python --version  # Should be 3.8+

# Ensure dependencies are installed
pip install -r requirements.txt
```

#### API Key Issues
If services are not working, check your API keys:
1. Open settings (gear icon or Ctrl+,)
2. Verify API keys are entered correctly
3. Use the "Test" button next to each key to validate

#### Voice Recognition Problems
```
# Check microphone
python -c "import pyaudio; print(pyaudio.PyAudio().get_device_info())"

# Test voice recognition directly
python utils/test_voice.py
```

#### Model Loading Errors
```
# Verify model files exist
ls -la models/llava/

# Try with text-only mode
python main.py --text-only
```

### Logs

Log files are stored in the `logs/` directory:
```bash
# View recent logs
cat logs/assistant.log | tail -n 100

# Search for errors
grep ERROR logs/assistant.log
```

### Getting Help

- **Documentation**: Full documentation is available in the `docs/` directory
- **GitHub Issues**: Report bugs at https://github.com/Westfall-Softwares/WestfallPersonalAssistant/issues
- **Community Forum**: Get help at https://community.westfallsoftwares.com

## Performance Optimization

### Memory Usage

Reduce memory footprint:
```bash
python main.py --optimize-memory
```

### GPU Acceleration

Enable GPU for faster processing:
```bash
python main.py --use-gpu
```

Supported GPU configurations:
- CUDA (NVIDIA)
- ROCm (AMD)
- DirectML (Windows)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

Developed by Westfall Developments © 2025

### Third-Party Libraries
- LLaVA - Multimodal AI capabilities
- FastAPI - Web framework
- PyTorch - Machine learning framework
- SpeechRecognition - Voice processing
- And many more listed in requirements.txt

## Contributing
(NOT AVAILABLE UNTIL AFTER BETA TESTING)
Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the security documentation

---

**Security Notice**: This application handles sensitive data and API keys. Always follow security best practices and keep your dependencies updated.
