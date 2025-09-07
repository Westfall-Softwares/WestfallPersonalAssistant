# Westfall Personal Assistant

A secure, AI-powered personal assistant application with comprehensive productivity tools.

## Features

- 🔐 **Secure Storage**: Military-grade encryption for passwords and sensitive data
- 🤖 **AI Assistant**: Integrated AI chat with context awareness
- 📧 **Email Client**: Full IMAP/SMTP email management
- 🔑 **Password Manager**: Encrypted password storage with generator
- 📝 **Notes**: Rich text notes with categories
- 📅 **Calendar**: Event scheduling and reminders
- 🌤️ **Weather**: Real-time weather and forecasts
- 📰 **News Reader**: RSS and NewsAPI integration
- 🎵 **Music Player**: Audio playback with playlists
- 💰 **Finance Tracker**: Income/expense management
- ✅ **Todo List**: Task management
- 🍳 **Recipe Manager**: Recipe storage and search
- 📁 **File Manager**: File system navigation
- 🌐 **Web Browser**: Integrated web browsing
- 👥 **Contacts**: Contact management system

## Installation

### Requirements
- Python 3.8 or higher
- Windows, macOS, or Linux

### Setup
```bash
# Clone the repository
git clone https://github.com/Westfall-Softwares/WestfallPersonalAssistant.git
cd WestfallPersonalAssistant

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## First Run

1. **Create Master Password**: On first launch, you'll be prompted to create a master password. This password encrypts all your sensitive data.

2. **Configure API Keys** (Optional):
   - OpenWeatherMap API key for weather
   - NewsAPI key for news
   - OpenAI API key for advanced AI features

## Keyboard Shortcuts

### Feature Shortcuts
- `Ctrl+E` - Open Email
- `Ctrl+P` - Open Password Manager
- `Ctrl+N` - Open Notes
- `Ctrl+T` - Open Todo
- `Ctrl+W` - Open Weather
- `Ctrl+B` - Open Browser
- `Ctrl+F` - Open File Manager
- `Ctrl+M` - Open Music Player
- `Ctrl+R` - Open Recipes
- `Ctrl+,` - Open Settings

### System Shortcuts
- `Ctrl+K` - Focus search/command bar
- `Ctrl+Space` - Toggle AI Assistant
- `Ctrl+/` - Show keyboard shortcuts
- `Ctrl+D` - Toggle dark mode
- `F1` - Show help
- `F11` - Toggle fullscreen
- `Escape` - Close current window
- `Ctrl+Q` - Quit application

## AI Assistant

The AI Assistant can help you with:
- Writing emails
- Generating passwords
- Creating notes
- Scheduling events
- Getting information
- Troubleshooting issues

### Using AI Assistant

1. **Quick Access**: Press `Ctrl+Space` or click the AI Assistant button
2. **Command Bar**: Type in the search bar with prefix `ai:` or `?`
3. **Context Aware**: The AI knows which window you're using

### Example Commands
- "ai: help me write an email to John about the meeting"
- "? what's on my calendar today"
- "ai: generate a secure password for my bank"
- "? summarize today's news"

## Security

- All passwords are encrypted using AES-256
- Master password required on startup
- Auto-lock after 15 minutes of inactivity
- Secure API key storage
- No data leaves your device without encryption

## Building

To create a standalone executable:

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller westfall_assistant.spec

# Find executable in dist/ folder
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## License

MIT License - See LICENSE file for details

## Support

For issues or questions, please visit:
https://github.com/Westfall-Softwares/WestfallPersonalAssistant/issues

## Credits

Developed by Westfall Softwares