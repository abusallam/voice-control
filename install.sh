#!/bin/bash

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Move application files
mkdir -p ~/.local/bin
cp voice-control ~/.local/bin/
cp voice-control-ui ~/.local/bin/
cp commands.py ~/.local/bin/

# Move systemd service file
sudo cp voice-control.service /etc/systemd/system/
sudo systemctl enable voice-control.service

echo "Installation complete. Please reboot your system for the changes to take effect."
