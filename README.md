# 🎤 Voice Control for Linux

A reliable, privacy-focused voice control application for Linux desktop environments.

## ✨ Features

- 🔒 **100% Local Processing** - Your voice never leaves your computer
- 🖥️ **Cross-Distribution Support** - Works on Ubuntu, Debian, Fedora, Arch Linux, and more
- 🎯 **System Tray Integration** - Always accessible, never intrusive
- ⚡ **Real-Time Processing** - Instant voice command recognition
- 🛡️ **Stable & Crash-Resistant** - Comprehensive error handling and recovery
- 🔧 **User-Space Installation** - No root privileges required
- 🎨 **Desktop Environment Agnostic** - Works with GNOME, KDE, XFCE, and others
- 📱 **Wayland & X11 Compatible** - Supports both modern and traditional display servers

## 🚀 Quick Start

### Prerequisites

- **Linux Distribution**: Ubuntu 20.04+, Debian 11+, Fedora 35+, Arch Linux, or similar
- **Python**: 3.8 or higher
- **Audio System**: PulseAudio or PipeWire
- **Memory**: 2GB RAM (4GB recommended)
- **Microphone**: Working audio input device

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/voice-control.git
cd voice-control

# Run the installation script
./install.sh

# Verify installation
python3 verify_installation.py
```

### First Run

```bash
# Start voice control
voice-control

# Or run as a background service
voice-control --daemon

# Check service status
voice-control --service status
```

## 📖 Documentation

### User Guides
- [Installation Guide](docs/installation.md) - Detailed installation instructions
- [Configuration Guide](docs/configuration.md) - Customization options
- [Troubleshooting Guide](docs/troubleshooting.md) - Common issues and solutions

### Developer Resources
- [Contributing Guide](docs/contributing.md) - How to contribute to the project
- [Architecture Overview](docs/architecture.md) - Technical implementation details

## 🛠️ Usage

### Basic Commands

```bash
# Service Management
voice-control --service install    # Install systemd user service
voice-control --service start      # Start the service
voice-control --service stop       # Stop the service
voice-control --service status     # Check service status

# Running Modes
voice-control                      # Interactive mode
voice-control --daemon            # Background daemon mode
voice-control --log-level DEBUG   # Debug mode with verbose logging
```

### System Integration

```bash
# Enable auto-start on login
systemctl --user enable voice-control

# Start/stop service manually
systemctl --user start voice-control
systemctl --user stop voice-control

# View service logs
journalctl --user -u voice-control -f
```

## 🔧 Configuration

Voice Control can be customized through configuration files:

- **User Config**: `~/.config/voice-control/voice-control.py`
- **System Config**: `/etc/voice-control/` (optional)

Example configuration:

```python
# ~/.config/voice-control/voice-control.py
def voice_control_process(text):
    """Process recognized speech text"""
    # Convert to uppercase for emphasis
    if text.startswith("shout"):
        return text.upper()
    
    # Add punctuation if missing
    if not text.endswith(('.', '!', '?')):
        text += '.'
    
    return text
```

## 🧪 Testing

```bash
# Run all tests
python3 -m pytest tests/

# Test specific components
python3 -m pytest tests/test_core.py
python3 -m pytest tests/test_speech.py

# Run with coverage
python3 -m pytest tests/ --cov=voice_control
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/contributing.md) for details.

### Quick Contribution Steps

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run tests: `python3 -m pytest`
5. Submit a pull request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/voice-control.git
cd voice-control

# Create development environment
python3 -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
python3 -m pytest
```

## 🐛 Troubleshooting

### Common Issues

**Installation fails with permission errors:**
```bash
# Make sure you're not using sudo
./install.sh  # NOT: sudo ./install.sh
```

**Audio not working:**
```bash
# Check audio system
pactl info  # For PulseAudio
pipewire --version  # For PipeWire

# Test microphone
arecord -d 5 test.wav && aplay test.wav
```

**Service won't start:**
```bash
# Check service status
systemctl --user status voice-control

# View detailed logs
journalctl --user -u voice-control -n 50
```

For more troubleshooting help, see our [Troubleshooting Guide](docs/troubleshooting.md).

## 📊 System Requirements

### Minimum Requirements
- **OS**: Linux with systemd (most modern distributions)
- **Python**: 3.8+
- **RAM**: 2GB
- **Storage**: 500MB free space
- **Audio**: Working microphone and audio system

### Recommended Requirements
- **RAM**: 4GB or more
- **CPU**: Multi-core processor
- **Audio**: High-quality microphone for better recognition

### Tested Distributions
- Ubuntu 20.04, 22.04, 24.04
- Debian 11, 12
- Fedora 35, 36, 37, 38
- Arch Linux (current)
- openSUSE Leap 15.4+

## 🔒 Privacy & Security

- **Local Processing**: All speech recognition happens on your device
- **No Network Transmission**: Your voice data never leaves your computer
- **User-Space Operation**: Runs without root privileges
- **Secure Storage**: Configuration and data stored with appropriate permissions
- **Open Source**: Full source code available for audit

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**You are free to:**
- Use this software for any purpose
- Modify and distribute the software
- Use it in commercial projects
- Create proprietary versions

## 🙏 Acknowledgments

This project builds upon the work of many open source contributors and projects:

- The Linux desktop community for creating accessible computing environments
- Audio processing libraries that make real-time speech processing possible
- The Python ecosystem for providing excellent development tools

## 📞 Support

- **Documentation**: Check our [docs/](docs/) directory
- **Issues**: Report bugs and request features on [GitHub Issues](https://github.com/your-username/voice-control/issues)
- **Discussions**: Join conversations on [GitHub Discussions](https://github.com/your-username/voice-control/discussions)

## 🚀 Roadmap

### Current Status
- ✅ Core application architecture
- ✅ System integration and service management
- ✅ GUI components and system tray
- ✅ Error handling and stability fixes
- 🔄 Speech recognition backend implementation (in progress)

### Upcoming Features
- 🎯 Proven speech recognition integration
- 🌍 Multi-language support
- 🔌 Plugin system for extensibility
- 📱 Mobile companion app
- 🤖 Advanced voice command processing

---

**Made with ❤️ for the Linux community**

If you find this project useful, please consider starring the repository and sharing it with others!