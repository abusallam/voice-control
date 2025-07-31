# 🎤 VoiceWhisper - Voice Control for Linux

**A production-ready voice-to-text system for Debian 12 GNOME/Wayland**

Transform your voice into text instantly with AI-powered speech recognition. Perfect for dictation, note-taking, and hands-free computing.

![VoiceWhisper Demo](https://img.shields.io/badge/Platform-Debian%2012%20GNOME-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![License](https://img.shields.io/badge/License-GPL--2.0-red)

## ✨ Features

- 🎙️ **Instant Voice Recognition** - Powered by OpenAI Whisper
- 🖥️ **System Tray Integration** - Easy access from your desktop
- ⌨️ **Automatic Typing** - Text appears where your cursor is
- 🎧 **Continuous Listening** - Stream your voice to text in real-time
- 🛡️ **Production-Ready** - Comprehensive error handling and recovery
- 🔒 **Privacy-First** - All processing happens locally, no cloud services
- 🌍 **Multi-Language** - Auto-detects language or specify your preference
- ⚡ **Wayland Native** - Optimized for modern Linux desktops

## 🚀 Quick Start

### One-Command Installation

```bash
git clone https://github.com/your-username/voice-control.git
cd voice-control
./install.sh
```

### Launch System Tray

```bash
./voice_control_tray.py
```

### Set Keyboard Shortcut

1. **Settings** → **Keyboard** → **Keyboard Shortcuts** → **Custom Shortcuts**
2. Add shortcut:
   - **Name**: Quick Voice Record
   - **Command**: `/home/$USER/.local/bin/voice-quick-record`
   - **Shortcut**: `Ctrl+Alt+V`

## 🎯 How It Works

1. **Press `Ctrl+Alt+V`** (or click tray icon)
2. **Speak clearly** for 5 seconds
3. **Watch your words appear** where your cursor is!

## 📋 System Requirements

- **OS**: Debian 12 (Bookworm) with GNOME
- **Display**: Wayland or X11 support
- **Audio**: PulseAudio or PipeWire
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM (8GB recommended)
- **Storage**: 2GB free space

## 🛠️ Installation

### Automatic Installation

```bash
# Clone the repository
git clone https://github.com/your-username/voice-control.git
cd voice-control

# Run the installer
./install.sh

# Start the system tray
./voice_control_tray.py
```

### Manual Installation

<details>
<summary>Click to expand manual installation steps</summary>

#### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install -y \
    python3-venv python3-dev python3-pip \
    portaudio19-dev libasound2-dev libpulse-dev \
    build-essential pkg-config libcairo2-dev \
    libgirepository1.0-dev gir1.2-gtk-3.0 \
    libgtk-3-dev python3-gi python3-gi-cairo \
    gir1.2-ayatanaappindicator3-0.1 \
    wtype xdotool wl-clipboard libnotify-bin
```

#### 2. Setup Python Environment

```bash
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -r requirements.txt
```

#### 3. Make Scripts Executable

```bash
chmod +x voice_control_tray.py
chmod +x voice_whisper.py
chmod +x install.sh
```

</details>

## 🎛️ Usage

### System Tray Features

- **🎙️ Quick Record (5s)** - Single voice recording
- **🎧 Continuous Listening** - Real-time voice streaming
- **🤖 AI Agent Services** - Access to voice control engine
- **🛡️ Error Handler Status** - System health monitoring
- **🔧 System Diagnostics** - Troubleshooting tools
- **⚙️ Settings** - Configuration options
- **🚪 Exit** - Clean shutdown

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Alt+V` | Quick voice record (5 seconds) |
| `Ctrl+Alt+L` | Toggle continuous listening |

### Command Line Usage

```bash
# Single recording
./voice_whisper.py --duration 5

# Continuous mode
./voice_whisper.py --continuous

# Different model sizes
./voice_whisper.py --model small    # Better accuracy
./voice_whisper.py --model tiny     # Faster processing

# Test audio devices
./voice_whisper.py --test-audio
```

## 🔧 Configuration

### Audio Settings

The system auto-detects your audio devices. To manually configure:

```bash
# List available audio devices
./voice_whisper.py --test-audio

# Test microphone
arecord -l
arecord -D default -f cd -t wav -d 5 test.wav
aplay test.wav
```

### Language Settings

```python
# In voice_whisper.py, modify the transcribe call:
result = self.model.transcribe(audio_file, language="en")  # English
result = self.model.transcribe(audio_file, language="es")  # Spanish
result = self.model.transcribe(audio_file, language="fr")  # French
# Or leave as None for auto-detection
```

## 🐛 Troubleshooting

### Common Issues

**No Audio Detected**
```bash
# Check audio devices
./voice_whisper.py --test-audio

# Test microphone
arecord -D default -f cd -t wav -d 5 test.wav && aplay test.wav
```

**Text Not Typing**
- Ensure `wtype` and `xdotool` are installed
- Check if you're using Wayland or X11
- Try the clipboard fallback (text gets copied, press Ctrl+V)

**System Tray Not Appearing**
```bash
# Install AppIndicator support
sudo apt install gir1.2-ayatanaappindicator3-0.1

# Restart GNOME Shell
Alt+F2, type 'r', press Enter
```

**Model Loading Issues**
```bash
# Try smaller model
./voice_whisper.py --model tiny

# Check available disk space
df -h
```

### Diagnostic Tools

```bash
# Run system diagnostics
python3 test_error_handler.py

# Check error logs
journalctl --user -f

# Test clipboard functionality
python3 test_clipboard.py
```

## 🏗️ Architecture

```
voice-control/
├── voice_control_tray.py      # System tray application
├── voice_whisper.py           # Core voice recognition
├── voice_control/             # Core modules
│   ├── core/                  # Error handling, resource management
│   ├── gui/                   # System tray, notifications
│   └── system/                # Service management, input handling
├── install.sh                 # Automated installer
├── requirements.txt           # Python dependencies
└── docs/                      # Documentation
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/your-username/voice-control.git
cd voice-control
./install.sh
source .venv/bin/activate

# Run tests
python -m pytest tests/

# Code formatting
black voice_control/
flake8 voice_control/
```

## 📄 License

This project is licensed under the GPL-2.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition engine
- [GNOME Project](https://www.gnome.org/) - Desktop environment
- [Debian Project](https://www.debian.org/) - Operating system

## 📞 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/your-username/voice-control/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-username/voice-control/discussions)
- 📖 **Documentation**: [Wiki](https://github.com/your-username/voice-control/wiki)

---

**Made with ❤️ for the Linux community**

*Transform your voice into text with the power of AI - completely offline and privacy-focused.*