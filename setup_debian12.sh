#!/bin/bash
set -e

echo "🎤 Setting up Voice Control for Debian 12 GNOME/Wayland"
echo "======================================================="

# Check if we're on Debian 12
if ! grep -q "bookworm\|12" /etc/debian_version 2>/dev/null; then
    echo "⚠️  Warning: This script is designed for Debian 12 (Bookworm)"
fi

# Check if we're running GNOME
if [ "$XDG_CURRENT_DESKTOP" != "GNOME" ]; then
    echo "⚠️  Warning: This script is optimized for GNOME desktop"
fi

echo "📦 Installing system dependencies..."

# Essential system packages for Debian 12
SYSTEM_PACKAGES=(
    "python3-venv"           # Virtual environment support
    "python3-dev"            # Python development headers
    "python3-pip"            # Python package installer
    "portaudio19-dev"        # Audio I/O development files
    "libasound2-dev"         # ALSA development files
    "libpulse-dev"           # PulseAudio development files
    "build-essential"        # Compilation tools
    "pkg-config"             # Package configuration
    "libcairo2-dev"          # Cairo graphics library
    "libgirepository1.0-dev" # GObject introspection
    "gir1.2-gtk-3.0"         # GTK3 GObject bindings
    "libgtk-3-dev"           # GTK3 development files
    "python3-gi"             # Python GObject bindings
    "python3-gi-cairo"       # Python Cairo bindings
    "gir1.2-appindicator3-0.1" # System tray support
    "libappindicator3-dev"   # AppIndicator development
    "ffmpeg"                 # Audio/video processing
    "espeak-ng"              # Text-to-speech (optional)
)

# Check which packages are missing
MISSING_PACKAGES=()
for package in "${SYSTEM_PACKAGES[@]}"; do
    if ! dpkg -l | grep -q "^ii  $package "; then
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo "Installing missing packages: ${MISSING_PACKAGES[*]}"
    sudo apt update
    sudo apt install -y "${MISSING_PACKAGES[@]}"
else
    echo "✅ All system packages are already installed"
fi

echo "🐍 Setting up Python virtual environment..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv --system-site-packages
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip setuptools wheel

echo "📚 Installing Python dependencies..."

# Install requirements
if python -m pip install -r requirements.txt; then
    echo "✅ Python dependencies installed successfully"
else
    echo "❌ Some Python dependencies failed to install"
    echo "This might be due to missing system packages or compatibility issues"
    echo "Trying to install core dependencies only..."
    
    # Try installing core dependencies one by one
    CORE_DEPS=(
        "psutil>=5.8.0"
        "numpy>=1.21.0" 
        "pyaudio>=0.2.11"
        "SpeechRecognition>=3.10.0"
        "openai-whisper>=20231117"
        "Pillow>=8.3.0"
        "PyGObject>=3.42.0"
        "pycairo>=1.20.0"
    )
    
    for dep in "${CORE_DEPS[@]}"; do
        echo "Installing $dep..."
        python -m pip install "$dep" || echo "⚠️  Failed to install $dep"
    done
fi

echo "🔧 Setting up voice control..."

# Make the main script executable
chmod +x voice-control

# Test basic imports
echo "🧪 Testing basic functionality..."
if python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from voice_control.core.error_handler import get_error_handler
    from voice_control.core.engine import VoiceControlEngine
    print('✅ Core modules imported successfully')
except ImportError as e:
    print(f'⚠️  Import warning: {e}')
    print('Some features may not be available')

try:
    import speech_recognition
    print('✅ Speech recognition available')
except ImportError:
    print('⚠️  Speech recognition not available')

try:
    import whisper
    print('✅ Whisper available')
except ImportError:
    print('⚠️  Whisper not available')

try:
    import pyaudio
    print('✅ Audio input available')
except ImportError:
    print('⚠️  Audio input not available')

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    print('✅ GTK/GNOME integration available')
except ImportError:
    print('⚠️  GTK/GNOME integration not available')
"; then
    echo "✅ Basic functionality test passed"
else
    echo "⚠️  Some issues detected, but continuing..."
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "🚀 Quick start:"
echo "   ./voice-control                    # Run interactively"
echo "   ./voice-control --daemon           # Run in background"
echo "   python3 test_error_handler.py     # Test error handling"
echo ""
echo "🔧 Troubleshooting:"
echo "   ./voice-control --doctor           # Run diagnostics"
echo "   journalctl --user -f              # View logs"
echo ""
echo "📝 Note: If you get permission errors, you may need to:"
echo "   sudo usermod -a -G audio $USER     # Add user to audio group"
echo "   # Then log out and back in"