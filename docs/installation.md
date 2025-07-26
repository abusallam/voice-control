# Installation Guide

## Quick Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/voice-control.git
cd voice-control
```

### 2. Run the Installer
```bash
./install.sh
```

### 3. Verify Installation
```bash
python3 verify_installation.py
python3 test_stability.py
```

## Manual Installation

### Prerequisites
- Linux (Ubuntu 20.04+, Debian 11+, Fedora 35+, Arch Linux)
- Python 3.9 or higher
- pip3 package manager

### Step-by-Step Installation

1. **Install Python Dependencies**
   ```bash
   pip3 install --user -r requirements.txt
   ```

2. **Install System Dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt install python3-dev portaudio19-dev

   # Fedora
   sudo dnf install python3-devel portaudio-devel

   # Arch Linux
   sudo pacman -S python portaudio
   ```

3. **Install Application**
   ```bash
   mkdir -p ~/.local/bin ~/.local/share/voice-control
   cp voice-control ~/.local/bin/
   cp -r voice_control ~/.local/share/voice-control/
   chmod +x ~/.local/bin/voice-control
   ```

4. **Install User Service**
   ```bash
   python3 -m voice_control.system.service_manager install
   ```

## Troubleshooting

### Common Issues

**Python Version Error**
```bash
# Check Python version
python3 --version
# Should be 3.9 or higher
```

**Permission Errors**
```bash
# Use user installation
pip3 install --user package_name
```

**Audio Issues**
```bash
# Test audio system
arecord -l  # List audio devices
pulseaudio --check -v  # Check PulseAudio
```

### Getting Help

If you encounter issues:
1. Run `python3 verify_installation.py`
2. Check logs: `journalctl --user -u voice-control`
3. Open an issue on GitHub with the error details