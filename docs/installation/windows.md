---
title: "Windows Installation Guide"
description: "Complete installation guide for Westfall Personal Assistant on Windows"
category: "installation"
priority: 1
tags: ["windows", "installation", "setup", "guide"]
last_updated: "2025-09-08"
---

# Windows Installation Guide

This guide will help you install Westfall Personal Assistant on Windows 10 or Windows 11.

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10 (version 1903) or Windows 11
- **Processor**: 64-bit Intel or AMD processor
- **Memory**: 4 GB RAM
- **Storage**: 2 GB available disk space
- **Graphics**: DirectX 11 compatible
- **Network**: Internet connection for initial setup

### Recommended Requirements
- **Operating System**: Windows 11 (latest version)
- **Processor**: Intel Core i5 or AMD Ryzen 5 (or equivalent)
- **Memory**: 8 GB RAM or more
- **Storage**: 5 GB available disk space (SSD preferred)
- **Graphics**: Dedicated graphics card (for AI processing)
- **Network**: Broadband internet connection

## Installation Methods

Choose the installation method that works best for you:

### Method 1: Installer Package (Recommended)

#### Step 1: Download the Installer

1. Visit the [GitHub Releases page](https://github.com/Westfall-Softwares/WestfallPersonalAssistant/releases)
2. Find the latest release
3. Download `WestfallPersonalAssistant-Windows-Setup.exe`

#### Step 2: Run the Installer

1. **Locate the downloaded file** in your Downloads folder
2. **Right-click** on `WestfallPersonalAssistant-Windows-Setup.exe`
3. **Select "Run as administrator"** (important for proper installation)
4. **Click "Yes"** when prompted by User Account Control

#### Step 3: Follow Installation Wizard

1. **Welcome Screen**: Click "Next"
2. **License Agreement**: Read and accept the license terms
3. **Installation Directory**: Choose installation location (default recommended)
4. **Start Menu Folder**: Choose Start Menu folder name
5. **Additional Tasks**: Select desired options:
   - ✅ Create desktop shortcut
   - ✅ Add to PATH environment variable
   - ✅ Associate file types
6. **Ready to Install**: Review settings and click "Install"
7. **Completing Setup**: Click "Finish" to complete installation

#### Step 4: First Launch

1. **Launch** from desktop shortcut or Start Menu
2. **Allow firewall access** if prompted
3. **Complete initial setup** (see First Time Setup section)

### Method 2: Portable Installation

For users who prefer a portable installation without admin rights:

#### Step 1: Download Portable Package

1. Visit the [GitHub Releases page](https://github.com/Westfall-Softwares/WestfallPersonalAssistant/releases)
2. Download `WestfallPersonalAssistant-Windows-Portable.zip`

#### Step 2: Extract and Run

1. **Extract** the ZIP file to your desired location
2. **Navigate** to the extracted folder
3. **Run** `WestfallPersonalAssistant.exe`

### Method 3: From Source Code

For developers or advanced users:

#### Prerequisites

1. **Install Python 3.8+**
   - Download from [python.org](https://www.python.org/downloads/)
   - ✅ Check "Add Python to PATH" during installation

2. **Install Git**
   - Download from [git-scm.com](https://git-scm.com/download/win)

#### Installation Steps

1. **Open Command Prompt** or PowerShell as Administrator

2. **Clone the repository**:
   ```cmd
   git clone https://github.com/Westfall-Softwares/WestfallPersonalAssistant.git
   cd WestfallPersonalAssistant
   ```

3. **Create virtual environment**:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```cmd
   pip install -r requirements.txt
   ```

5. **Run the application**:
   ```cmd
   python main.py
   ```

## First Time Setup

### Initial Configuration

When you first launch Westfall Personal Assistant:

#### Step 1: Create Master Password

1. **Enter a strong master password** (this encrypts all your data)
2. **Confirm the password**
3. **Write it down** in a secure location
4. **Click "Create"**

⚠️ **Important**: If you forget your master password, there's no way to recover your encrypted data!

#### Step 2: Basic Settings

1. **Choose your preferred theme** (Light/Dark/Auto)
2. **Select language** (if multiple languages are available)
3. **Configure data directory** (default location recommended)
4. **Set up automatic backups** (highly recommended)

#### Step 3: Optional Features

Configure these optional features for enhanced functionality:

**Weather Service**:
1. Get a free API key from [OpenWeatherMap](https://openweathermap.org/api)
2. Go to Settings → API Keys → Weather
3. Enter your API key

**News Service**:
1. Get a free API key from [NewsAPI](https://newsapi.org/)
2. Go to Settings → API Keys → News
3. Enter your API key

**AI Features**:
1. Get an API key from [OpenAI](https://platform.openai.com/) (optional)
2. Go to Settings → AI → OpenAI API Key
3. Enter your API key for enhanced AI capabilities

## Troubleshooting Common Issues

### Installation Problems

#### Issue: "Windows protected your PC" message

**Cause**: Windows Defender SmartScreen blocking unsigned executable

**Solution**:
1. Click "More info"
2. Click "Run anyway"
3. Or add installer to Windows Defender exceptions

#### Issue: Installation fails with permission errors

**Solution**:
1. Right-click installer
2. Select "Run as administrator"
3. Ensure you have admin rights on the computer

#### Issue: Python not found error (source installation)

**Solution**:
1. Install Python from [python.org](https://www.python.org/downloads/)
2. ✅ Check "Add Python to PATH" during installation
3. Restart Command Prompt
4. Verify with: `python --version`

### Application Launch Issues

#### Issue: Application won't start

**Solutions**:

1. **Check system requirements**
2. **Run as administrator**
3. **Update Windows** to latest version
4. **Install Visual C++ Redistributables**:
   - Download from [Microsoft](https://docs.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)
   - Install both x86 and x64 versions

#### Issue: "DLL not found" errors

**Solutions**:
1. **Install Microsoft Visual C++ Redistributable 2019-2022**
2. **Update Windows** to latest version
3. **Check Windows Update** for optional updates

#### Issue: High DPI display issues

**Solutions**:
1. Right-click application shortcut
2. Select "Properties"
3. Go to "Compatibility" tab
4. Click "Change high DPI settings"
5. Check "Override high DPI scaling behavior"
6. Select "System (Enhanced)" from dropdown

### Performance Issues

#### Issue: Slow startup

**Solutions**:
1. **Disable startup programs** not needed
2. **Run disk cleanup** to free space
3. **Update graphics drivers**
4. **Consider SSD** if using traditional hard drive

#### Issue: High memory usage

**Solutions**:
1. **Close unnecessary applications**
2. **Increase virtual memory** (pagefile)
3. **Upgrade RAM** if possible
4. **Check Task Manager** for memory-intensive processes

## Advanced Configuration

### Windows Firewall Configuration

If you experience network connectivity issues:

1. **Open Windows Defender Firewall**
2. **Click "Allow an app through firewall"**
3. **Click "Change Settings"**
4. **Click "Allow another app..."**
5. **Browse** to WestfallPersonalAssistant.exe
6. **Check both Private and Public** networks
7. **Click OK**

### Environment Variables

For advanced users, you can configure these environment variables:

```cmd
# Data directory location
set WESTFALL_DATA_DIR=C:\Users\YourName\Documents\WestfallData

# Log level (DEBUG, INFO, WARNING, ERROR)
set WESTFALL_LOG_LEVEL=INFO

# Disable hardware acceleration
set WESTFALL_NO_HARDWARE_ACCEL=1
```

### Registry Settings

Advanced configuration via Windows Registry (use with caution):

```
[HKEY_CURRENT_USER\Software\WestfallSoftwares\PersonalAssistant]
"DataDirectory"="C:\\Users\\YourName\\Documents\\WestfallData"
"AutoStart"=dword:00000001
"MinimizeToTray"=dword:00000001
```

## Automatic Updates

### Configure Update Settings

1. **Go to Settings → Updates**
2. **Choose update frequency**:
   - Automatic (recommended)
   - Check daily
   - Check weekly
   - Manual only
3. **Select update channel**:
   - Stable (recommended)
   - Beta (for testing new features)

### Manual Update Process

1. **Download latest installer** from GitHub Releases
2. **Close** Westfall Personal Assistant
3. **Run new installer** (will update existing installation)
4. **Restart** the application

## Uninstallation

### Using Windows Settings

1. **Open Settings** (Windows key + I)
2. **Go to Apps**
3. **Find "Westfall Personal Assistant"**
4. **Click and select "Uninstall"**
5. **Follow prompts** to complete removal

### Manual Removal

If automatic uninstall doesn't work:

1. **Delete application folder** (default: `C:\Program Files\WestfallPersonalAssistant\`)
2. **Delete data folder** (default: `%APPDATA%\WestfallPersonalAssistant\`)
3. **Remove Start Menu shortcuts**
4. **Clean registry entries** (optional, use registry cleaner)

### Preserving Data

To keep your data for future reinstallation:

1. **Before uninstalling**, export your data:
   - Settings → Data → Export All Data
   - Save to secure location
2. **Back up data directory** manually:
   - Copy `%APPDATA%\WestfallPersonalAssistant\` to safe location

## Security Considerations

### Windows Defender Configuration

1. **Add data folder to exclusions** (optional, for performance):
   - Windows Security → Virus & threat protection
   - Manage settings under Virus & threat protection settings
   - Add exclusion → Folder
   - Select: `%APPDATA%\WestfallPersonalAssistant\`

### User Account Control (UAC)

- **Keep UAC enabled** for security
- **Run as standard user** (not administrator) for daily use
- **Only elevate when necessary** for installation/updates

### Backup Recommendations

1. **Use Windows File History** to back up data folder
2. **Set up OneDrive** sync for automatic cloud backup
3. **Create regular exports** of important data
4. **Test restore process** periodically

## Integration with Windows

### File Associations

The installer can associate these file types with Westfall Personal Assistant:

- `.wfa` - Westfall Assistant files
- `.wfn` - Westfall notes
- `.wft` - Westfall templates

### Context Menu Integration

Right-click context menu additions:

- **"Open with Westfall Assistant"** for supported files
- **"Import to Westfall"** for various data files
- **"Create Westfall Note"** in folders

### System Tray Integration

- **Minimize to system tray** option
- **Quick access menu** from tray icon
- **Notification integration** with Windows Action Center

## Getting Help

### Built-in Help

- **Press F1** for context-sensitive help
- **Use AI Assistant** for questions (Ctrl+Space)
- **Check Settings → Help & Support**

### Online Resources

- **Documentation**: [Full documentation](../index.md)
- **Community**: [GitHub Discussions](https://github.com/Westfall-Softwares/WestfallPersonalAssistant/discussions)
- **Issues**: [GitHub Issues](https://github.com/Westfall-Softwares/WestfallPersonalAssistant/issues)

### Log Files Location

If you need to check log files for troubleshooting:

```
%APPDATA%\WestfallPersonalAssistant\logs\
```

---

*Last updated: September 8, 2025*