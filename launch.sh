#!/bin/bash
# VoiceWhisper Launcher - Simple way to start the application

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}🎤 VoiceWhisper Launcher${NC}"
echo "=========================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}Virtual environment not found. Running installer...${NC}"
    ./install.sh
fi

# Activate virtual environment
source .venv/bin/activate

# Check what the user wants to do
if [ "$1" = "tray" ] || [ "$1" = "" ]; then
    echo -e "${GREEN}🖥️  Starting System Tray...${NC}"
    python3 voice_control_tray.py
elif [ "$1" = "quick" ]; then
    echo -e "${GREEN}🎙️  Quick Recording (5 seconds)...${NC}"
    python3 voice_whisper.py --duration 5
elif [ "$1" = "continuous" ]; then
    echo -e "${GREEN}🎧 Starting Continuous Listening...${NC}"
    python3 voice_whisper.py --continuous
elif [ "$1" = "test" ]; then
    echo -e "${GREEN}🔧 Testing Audio Devices...${NC}"
    python3 voice_whisper.py --test-audio
elif [ "$1" = "help" ]; then
    echo "Usage: ./launch.sh [option]"
    echo ""
    echo "Options:"
    echo "  tray        Start system tray (default)"
    echo "  quick       Quick 5-second recording"
    echo "  continuous  Continuous listening mode"
    echo "  test        Test audio devices"
    echo "  help        Show this help message"
else
    echo "Unknown option: $1"
    echo "Use './launch.sh help' for available options"
    exit 1
fi