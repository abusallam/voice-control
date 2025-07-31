#!/bin/bash
set -e

echo "🎤 Setting up Voice Control System with System Tray"
echo "=================================================="

# Make scripts executable
chmod +x voice_control_tray.py
chmod +x voice_whisper.py
chmod +x launch_voice_whisper.sh

# Install system tray dependencies if needed
echo "📦 Checking system tray dependencies..."
if ! python3 -c "import gi; gi.require_version('AppIndicator3', '0.1')" 2>/dev/null; then
    echo "Installing AppIndicator3..."
    sudo apt install -y gir1.2-appindicator3-0.1
fi

# Create desktop entry for system tray
echo "🖥️  Creating desktop entries..."
cat > ~/.local/share/applications/voice-control-tray.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Voice Control Tray
Comment=Voice Control System Tray for Debian 12 GNOME/Wayland
Exec=/home/asim/Documents/voice-control/voice_control_tray.py
Icon=audio-input-microphone
Terminal=false
Categories=Utility;Audio;Accessibility;
Keywords=voice;speech;transcription;whisper;dictation;tray;
StartupNotify=true
NoDisplay=false
EOF

# Create autostart entry
echo "🚀 Setting up autostart..."
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/voice-control-tray.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Voice Control Tray
Comment=Voice Control System Tray
Exec=/home/asim/Documents/voice-control/voice_control_tray.py
Icon=audio-input-microphone
Terminal=false
Categories=Utility;Audio;
StartupNotify=true
X-GNOME-Autostart-enabled=true
EOF

echo "⌨️  Setting up keyboard shortcuts..."

# Create script for quick record
cat > ~/.local/bin/voice-quick-record << 'EOF'
#!/bin/bash
cd /home/asim/Documents/voice-control
source .venv/bin/activate
python3 voice_whisper.py --duration 5
EOF

chmod +x ~/.local/bin/voice-quick-record

# Instructions for manual keyboard shortcut setup
echo ""
echo "🎉 Setup Complete!"
echo ""
echo "📋 MANUAL SETUP REQUIRED:"
echo "========================"
echo ""
echo "1. 🎛️  START SYSTEM TRAY:"
echo "   ./voice_control_tray.py"
echo "   (Or search 'Voice Control Tray' in applications)"
echo ""
echo "2. ⌨️  SETUP KEYBOARD SHORTCUTS:"
echo "   Go to: Settings → Keyboard → Keyboard Shortcuts → Custom Shortcuts"
echo ""
echo "   Add these shortcuts:"
echo "   ┌─────────────────────────────────────────────────────────────┐"
echo "   │ Name: Quick Voice Record                                    │"
echo "   │ Command: /home/asim/.local/bin/voice-quick-record           │"
echo "   │ Shortcut: Ctrl+Alt+V                                       │"
echo "   └─────────────────────────────────────────────────────────────┘"
echo ""
echo "3. 🎤 USAGE:"
echo "   • System Tray: Click microphone icon in top bar"
echo "   • Quick Record: Press Ctrl+Alt+V"
echo "   • Continuous Mode: Use tray menu"
echo ""
echo "4. ✨ FEATURES:"
echo "   • 🎙️  Quick Record (5 seconds)"
echo "   • 🎧 Continuous Listening"
echo "   • 🤖 AI Agent Services"
echo "   • 🛡️  Error Handler Status"
echo "   • 🔧 System Diagnostics"
echo "   • ⚙️  Settings & About"
echo "   • 🚪 Proper Exit"
echo ""
echo "🚀 Ready to use! Start the system tray now:"
echo "   ./voice_control_tray.py"