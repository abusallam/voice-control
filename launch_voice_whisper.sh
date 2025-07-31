#!/bin/bash
# VoiceWhisper Launcher for GNOME

cd "$(dirname "$0")"
source .venv/bin/activate

# Show notification
notify-send "🎤 VoiceWhisper" "Starting voice recognition..." -t 2000

# Run VoiceWhisper
python3 voice_whisper.py --duration 5

# Show completion notification
notify-send "🎤 VoiceWhisper" "Voice recognition complete" -t 2000