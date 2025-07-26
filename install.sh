#!/bin/bash

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation directories
INSTALL_DIR="$HOME/.local/share/voice-control"
BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/voice-control"

echo -e "${GREEN}Voice Control for Linux - Community Edition${NC}"
echo "Installing to user space (no sudo required)..."
echo

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    elif [ -f /etc/debian_version ]; then
        echo "debian"
    elif [ -f /etc/redhat-release ]; then
        echo "rhel"
    elif [ -f /etc/arch-release ]; then
        echo "arch"
    else
        echo "unknown"
    fi
}

# Check system requirements
print_status "Checking system requirements..."

# Check Python version
if ! command_exists python3; then
    print_error "Python 3 is required but not installed"
    DISTRO=$(detect_distro)
    case $DISTRO in
        ubuntu|debian)
            print_error "Install with: sudo apt install python3 python3-pip python3-venv"
            ;;
        fedora)
            print_error "Install with: sudo dnf install python3 python3-pip"
            ;;
        arch)
            print_error "Install with: sudo pacman -S python python-pip"
            ;;
        *)
            print_error "Please install Python 3.8+ and pip3"
            ;;
    esac
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_error "Python 3.8 or higher is required (found: $PYTHON_VERSION)"
    exit 1
fi

print_status "Python $PYTHON_VERSION found - OK"

# Check for audio system
print_status "Checking audio system..."
AUDIO_SYSTEM=""
if command_exists pactl; then
    AUDIO_SYSTEM="PulseAudio"
    print_status "PulseAudio detected"
elif command_exists pipewire; then
    AUDIO_SYSTEM="PipeWire"
    print_status "PipeWire detected"
else
    print_warning "No audio system detected (PulseAudio/PipeWire)"
    print_warning "Audio functionality may not work properly"
fi

# Check for systemd
if ! command_exists systemctl; then
    print_warning "systemd not found - service management may not work"
fi

# Create directories
print_status "Creating directories..."
mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$CONFIG_DIR"

# Copy application files
print_status "Installing application files..."
if [ -d "voice_control" ]; then
    cp -r voice_control "$INSTALL_DIR/"
    print_status "Voice control modules installed"
else
    print_error "voice_control directory not found"
    exit 1
fi

if [ -f "voice-control" ]; then
    cp voice-control "$BIN_DIR/"
    chmod +x "$BIN_DIR/voice-control"
    print_status "Main executable installed"
else
    print_error "voice-control executable not found"
    exit 1
fi

if [ -f "voice-control-ui" ]; then
    cp voice-control-ui "$BIN_DIR/"
    chmod +x "$BIN_DIR/voice-control-ui"
    print_status "GUI executable installed"
fi

# Install desktop entry
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
if [ -f "voice-control.desktop" ]; then
    cp voice-control.desktop "$DESKTOP_DIR/"
    print_status "Desktop entry installed"
fi

# Install Python dependencies
print_status "Installing Python dependencies..."

if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found"
    exit 1
fi

# Create virtual environment (required for Debian 12+)
if [ ! -d ".venv" ]; then
    print_status "Creating virtual environment..."
    /usr/bin/python3 -m venv .venv
fi

print_status "Installing dependencies in virtual environment..."
source .venv/bin/activate

# Upgrade pip in virtual environment
python -m pip install --upgrade pip

# Install requirements in virtual environment
if ! python -m pip install -r requirements.txt; then
    print_error "Failed to install Python dependencies"
    print_error "This might be due to missing system packages"
    DISTRO=$(detect_distro)
    case $DISTRO in
        ubuntu|debian)
            print_error "Try installing system packages: sudo apt install python3-dev portaudio19-dev"
            ;;
        fedora)
            print_error "Try installing system packages: sudo dnf install python3-devel portaudio-devel"
            ;;
        arch)
            print_error "Try installing system packages: sudo pacman -S python-dev portaudio"
            ;;
    esac
    exit 1
fi

# Verify critical dependencies
print_status "Verifying dependencies..."
if ! python -c "import speech_recognition; import whisper; import pyaudio" 2>/dev/null; then
    print_warning "Some dependencies may not be fully functional"
    print_warning "Run 'python3 verify_installation.py' after installation to check"
fi

# Install user systemd service
if command_exists systemctl; then
    print_status "Installing user systemd service..."
    mkdir -p "$HOME/.config/systemd/user"

    # Create proper user service file
    cat > "$HOME/.config/systemd/user/voice-control.service" << EOF
[Unit]
Description=Voice Control for Linux
Documentation=https://github.com/your-username/voice-control
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
ExecStart=$BIN_DIR/voice-control --daemon
ExecReload=/bin/kill -HUP \$MAINPID
Restart=on-failure
RestartSec=5
StartLimitInterval=60
StartLimitBurst=3

# Environment variables
Environment=DISPLAY=:0
Environment=HOME=$HOME
Environment=XDG_RUNTIME_DIR=/run/user/%i

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=$HOME/.config/voice-control $HOME/.local/share/voice-control

[Install]
WantedBy=default.target
EOF

    # Reload systemd user daemon
    systemctl --user daemon-reload
    print_status "Systemd user service installed"
fi

# Create basic configuration if it doesn't exist
if [ ! -f "$CONFIG_DIR/voice-control.py" ]; then
    print_status "Creating default configuration..."
    cat > "$CONFIG_DIR/voice-control.py" << 'EOF'
#!/usr/bin/env python3
"""
Voice Control Configuration

This function is called to process recognized text before it's typed.
You can modify the text here to add custom processing.
"""

def voice_control_process(text):
    """Process recognized text before typing"""
    # Example: Convert to lowercase
    # return text.lower()
    
    # Example: Add punctuation
    # if not text.endswith('.'):
    #     text += '.'
    
    # Return text as-is by default
    return text
EOF
fi

# Add to PATH if needed
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    print_warning "$BIN_DIR is not in your PATH"
    
    # Try to add to common shell config files
    for shell_config in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
        if [ -f "$shell_config" ]; then
            if ! grep -q "$BIN_DIR" "$shell_config"; then
                echo "export PATH=\"\$PATH:$BIN_DIR\"" >> "$shell_config"
                print_status "Added to PATH in $shell_config"
                break
            fi
        fi
    done
    
    print_warning "Please restart your terminal or run: export PATH=\"\$PATH:$BIN_DIR\""
fi

print_status "Installation completed successfully!"
echo
echo -e "${GREEN}🎉 Voice Control for Linux is now installed!${NC}"
echo
echo -e "${GREEN}Next Steps:${NC}"
echo -e "1. ${BLUE}Verify installation:${NC} python3 verify_installation.py"
echo -e "2. ${BLUE}Start voice control:${NC} voice-control"
echo -e "3. ${BLUE}Install as service:${NC} voice-control --service install"
echo -e "4. ${BLUE}Enable autostart:${NC} systemctl --user enable voice-control"
echo
echo -e "${GREEN}Usage:${NC}"
echo -e "• ${BLUE}Interactive mode:${NC} voice-control"
echo -e "• ${BLUE}Background service:${NC} voice-control --daemon"
echo -e "• ${BLUE}Service management:${NC} voice-control --service [start|stop|status]"
echo -e "• ${BLUE}GUI configuration:${NC} voice-control-ui"
echo
echo -e "${GREEN}Configuration:${NC}"
echo -e "• Config file: ${BLUE}$CONFIG_DIR/voice-control.py${NC}"
echo -e "• Logs: ${BLUE}journalctl --user -u voice-control -f${NC}"
echo
echo -e "${YELLOW}Note:${NC} This installation uses user-space services (no sudo required)"
echo -e "${YELLOW}Note:${NC} Speech recognition backends need to be implemented"
echo
echo -e "${GREEN}For help and documentation:${NC}"
echo -e "• README: ${BLUE}cat README.md${NC}"
echo -e "• Troubleshooting: ${BLUE}docs/troubleshooting.md${NC}"
echo -e "• Contributing: ${BLUE}docs/contributing.md${NC}"