# 🎤 VoiceWhisper Setup Guide - Debian 12 GNOME/Wayland

## ✅ Your System is Ready!

Your VoiceWhisper system is now installed and ready to use on Debian 12 with GNOME/Wayland.

## 🚀 How to Use

### Method 1: Command Line
```bash
# Single recording (5 seconds)
./voice_whisper.py

# Continuous listening mode
./voice_whisper.py --continuous

# Test audio devices
./voice_whisper.py --test-audio

# Use different model sizes
./voice_whisper.py --model small    # Better accuracy
./voice_whisper.py --model tiny     # Faster processing
```

### Method 2: Desktop Launcher
- Press `Super` key and search for "VoiceWhisper"
- Click the VoiceWhisper app to launch

### Method 3: Keyboard Shortcut (Recommended)
1. Open **Settings** → **Keyboard** → **Keyboard Shortcuts**
2. Click **"View and Customize Shortcuts"**
3. Click **"Custom Shortcuts"**
4. Click **"+"** to add new shortcut
5. Set:
   - **Name**: VoiceWhisper
   - **Command**: `/home/asim/Documents/voice-control/launch_voice_whisper.sh`
   - **Shortcut**: `Super+Alt+V` (or your preferred combination)

## 🎯 How It Works

1. **Press your keyboard shortcut** (e.g., Super+Alt+V)
2. **Speak clearly** into your microphone for 5 seconds
3. **Your speech is transcribed** using Whisper AI
4. **Text is automatically typed** at your cursor location

## 🔧 Troubleshooting

### No Audio Detected
```bash
# Test your microphone
arecord -l
arecord -D default -f cd -t wav -d 5 test.wav
aplay test.wav

# Check audio devices
./voice_whisper.py --test-audio
```

### Typing Not Working
- **On Wayland**: Make sure `wtype` is installed: `sudo apt install wtype`
- **On X11**: Make sure `xdotool` is installed: `sudo apt install xdotool`

### Model Loading Issues
```bash
# Try smaller model
./voice_whisper.py --model tiny

# Check available space (models need ~1-5GB)
df -h
```

## 🎛️ Advanced Usage

### Different Languages
The system auto-detects language, but you can modify the code to force a specific language:
```python
result = self.model.transcribe(audio_file, language="en")  # English
result = self.model.transcribe(audio_file, language="ar")  # Arabic
result = self.model.transcribe(audio_file, language="fr")  # French
```

### Continuous Mode
```bash
# Run in continuous listening mode
./voice_whisper.py --continuous
```

### Custom Recording Duration
```bash
# Record for 10 seconds
./voice_whisper.py --duration 10
```

## 📁 File Structure
```
voice-control/
├── voice_whisper.py           # Main VoiceWhisper script
├── launch_voice_whisper.sh    # Launcher script
├── voice-whisper.desktop      # Desktop entry
├── .venv/                     # Python virtual environment
└── voice_control/             # Core voice control modules
```

## 🎉 You're Ready!

Your VoiceWhisper system is now fully functional on Debian 12 GNOME/Wayland!

**Quick Test:**
1. Open any text editor (like gedit)
2. Press `Super+Alt+V` (if you set up the shortcut)
3. Speak clearly: "Hello, this is a test"
4. Watch the text appear!

## 🔒 Privacy Note
- All processing happens **locally** on your machine
- No data is sent to external servers
- Whisper models run completely offline

Enjoy your new voice-to-text system! 🎤✨