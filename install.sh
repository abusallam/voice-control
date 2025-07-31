#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Project info
PROJECT_NAME="VoiceWhisper - Voice Control for Linux"
VERSION="1.0.0"
PLATFORM="Debian 12 GNOME/Wayland"

echo -e "${PURPLE}🎤 ${PROJECT_NAME}${NC}"
echo -e "${BLUE}Version: ${VERSION}${NC}"
echo -e "${BLUE}Platform: ${PLATFORM}${NC}"
echo "=" * 60

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

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if we're on Debian 12
check_system() {
    print_status "Checking system compatibility..."
    
    if [ -f /etc/debian_version ]; then
        DEBIAN_VERSION=$(cat /etc/debian_version)
        if [[ "$DEBIAN_VERSION" == *"12"* ]] || [[ "$DEBIAN_VERSION" == *"bookworm"* ]]; then
            print_success "Debian 12 (Bookworm) detected"
        else
            print_warning "This installer is optimized for Debian 12, but continuing..."
        fi
    else
        print_warning "Non-Debian system detected, some features may not work properly"
    fi
    
    if [ "$XDG_CURRENT_DESKTOP" = "GNOME" ]; then
        print_success "GNOME desktop environment detected"
    else
        print_warning "Non-GNOME desktop detected, system tray may not work properly"
    fi
}

# Install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    # Core dependencies
    CORE_PACKAGES=(
        "python3-venv" "python3-dev" "python3-pip"
        "portaudio19-dev" "libasound2-dev" "libpulse-dev"
        "build-essential" "pkg-config"
    )
    
    # GUI dependencies
    GUI_PACKAGES=(
        "libcairo2-dev" "libgirepository1.0-dev"
        "gir1.2-gtk-3.0" "libgtk-3-dev"
        "python3-gi" "python3-gi-cairo"
        "gir1.2-ayatanaappindicator3-0.1"
    )
    
    # Input/Output tools
    IO_PACKAGES=(
        "wtype" "xdotool" "wl-clipboard" "xclip"
        "libnotify-bin"
    )
    
    ALL_PACKAGES=("${CORE_PACKAGES[@]}" "${GUI_PACKAGES[@]}" "${IO_PACKAGES[@]}")
    
    # Check which packages are missing
    MISSING_PACKAGES=()
    for package in "${ALL_PACKAGES[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            MISSING_PACKAGES+=("$package")
        fi
    done
    
    if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
        print_status "Installing missing packages: ${MISSING_PACKAGES[*]}"
        sudo apt update
        sudo apt install -y "${MISSING_PACKAGES[@]}"
        print_success "System dependencies installed"
    else
        print_success "All system dependencies already installed"
    fi
}

# Setup Python environment
setup_python_env() {
    print_status "Setting up Python virtual environment..."
    
    # Check Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        print_error "Python 3.8 or higher is required (found: $PYTHON_VERSION)"
        exit 1
    fi
    print_success "Python $PYTHON_VERSION found"
    
    # Create virtual environment
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv --system-site-packages
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate and upgrade pip
    source .venv/bin/activate
    python -m pip install --upgrade pip setuptools wheel
    
    # Install Python dependencies
    print_status "Installing Python dependencies..."
    if python -m pip install -r requirements.txt; then
        print_success "Python dependencies installed"
    else
        print_error "Failed to install some Python dependencies"
        print_warning "Some features may not work properly"
    fi
}

# Verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    source .venv/bin/activate
    
    # Test core imports
    python3 -c "
import sys
sys.path.insert(0, '.')

success_count = 0
total_tests = 6

try:
    from voice_control.core.error_handler import get_error_handler
    print('✅ Error handler')
    success_count += 1
except ImportError as e:
    print(f'❌ Error handler: {e}')

try:
    import speech_recognition
    print('✅ Speech recognition')
    success_count += 1
except ImportError as e:
    print(f'❌ Speech recognition: {e}')

try:
    import whisper
    print('✅ Whisper AI')
    success_count += 1
except ImportError as e:
    print(f'❌ Whisper AI: {e}')

try:
    import pyaudio
    print('✅ Audio input')
    success_count += 1
except ImportError as e:
    print(f'❌ Audio input: {e}')

try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import Gtk, AyatanaAppIndicator3
    print('✅ System tray support')
    success_count += 1
except ImportError as e:
    print(f'❌ System tray support: {e}')

try:
    import sounddevice as sd
    import soundfile as sf
    print('✅ Audio processing')
    success_count += 1
except ImportError as e:
    print(f'❌ Audio processing: {e}')

print(f'\\n📊 Installation Status: {success_count}/{total_tests} components working')

if success_count >= 4:
    print('🎉 Installation successful! Core features available.')
    exit(0)
else:
    print('⚠️  Installation incomplete. Some features may not work.')
    exit(1)
"
    
    if [ $? -eq 0 ]; then
        print_success "Installation verification passed"
    else
        print_warning "Installation verification had issues"
    fi
}

# Setup executables and shortcuts
setup_executables() {
    print_status "Setting up executables and shortcuts..."
    
    # Make scripts executable
    chmod +x voice_control_tray.py
    chmod +x voice_whisper.py
    
    # Create local bin directory
    mkdir -p ~/.local/bin
    
    # Create quick record script
    cat > ~/.local/bin/voice-quick-record << EOF
#!/bin/bash
cd "$(dirname "$(readlink -f "\$0")")/../share/voice-control" 2>/dev/null || cd "$PWD"
source .venv/bin/activate 2>/dev/null || true
python3 voice_whisper.py --duration 5
EOF
    chmod +x ~/.local/bin/voice-quick-record
    
    # Create desktop entries
    mkdir -p ~/.local/share/applications
    
    # System tray desktop entry
    cat > ~/.local/share/applications/voice-control-tray.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=VoiceWhisper System Tray
Comment=Voice Control System Tray for Linux
Exec=$PWD/voice_control_tray.py
Icon=audio-input-microphone
Terminal=false
Categories=Utility;Audio;Accessibility;
Keywords=voice;speech;transcription;whisper;dictation;
StartupNotify=true
EOF
    
    # Quick launcher desktop entry
    cat > ~/.local/share/applications/voice-whisper.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=VoiceWhisper Quick Record
Comment=Quick voice recording and transcription
Exec=$HOME/.local/bin/voice-quick-record
Icon=audio-input-microphone
Terminal=false
Categories=Utility;Audio;
Keywords=voice;speech;transcription;whisper;
StartupNotify=true
EOF
    
    print_success "Executables and desktop entries created"
}

# Main installation function
main() {
    echo
    print_status "Starting installation process..."
    echo
    
    check_system
    install_system_deps
    setup_python_env
    verify_installation
    setup_executables
    
    echo
    print_success "🎉 Installation completed successfully!"
    echo
    echo -e "${PURPLE}🚀 Quick Start:${NC}"
    echo -e "1. ${BLUE}Start System Tray:${NC} ./voice_control_tray.py"
    echo -e "2. ${BLUE}Quick Record:${NC} ./voice_whisper.py"
    echo -e "3. ${BLUE}Set Keyboard Shortcut:${NC}"
    echo -e "   Settings → Keyboard → Custom Shortcuts"
    echo -e "   Command: $HOME/.local/bin/voice-quick-record"
    echo -e "   Shortcut: Ctrl+Alt+V"
    echo
    echo -e "${PURPLE}📖 Documentation:${NC}"
    echo -e "• ${BLUE}README.md${NC} - Complete usage guide"
    echo -e "• ${BLUE}VOICE_WHISPER_SETUP.md${NC} - Detailed setup instructions"
    echo
    echo -e "${GREEN}🎤 Ready to transform your voice into text!${NC}"
    echo
}

# Run main installation
main "$@"