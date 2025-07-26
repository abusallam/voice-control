# Troubleshooting Guide

This guide helps you diagnose and fix common issues with Voice Control for Linux.

## Quick Diagnostics

### 1. Run Verification Script

```bash
python3 verify_installation.py
python3 test_stability.py
```

### 2. Check Service Status

```bash
# Check if service is running
systemctl --user status voice-control

# View recent logs
journalctl --user -u voice-control -n 20

# Follow logs in real-time
journalctl --user -u voice-control -f
```

### 3. Test Basic Functionality

```bash
# Test in debug mode
voice-control --log-level DEBUG

# Test service management
voice-control --service status
```

## Installation Issues

### Python Version Problems

**Issue: "Python 3.8+ required"**

```bash
# Check Python version
python3 --version

# Install newer Python (Ubuntu/Debian)
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-pip

# Install newer Python (Fedora)
sudo dnf install python3.10

# Install newer Python (Arch)
sudo pacman -S python
```

### Dependency Installation Failures

**Issue: "Failed to install requirements"**

```bash
# Update pip first
python3 -m pip install --upgrade pip

# Install system dependencies (Ubuntu/Debian)
sudo apt install python3-dev portaudio19-dev libasound2-dev

# Install system dependencies (Fedora)
sudo dnf install python3-devel portaudio-devel alsa-lib-devel

# Install system dependencies (Arch)
sudo pacman -S python-pip portaudio alsa-lib

# Retry installation
pip install -r requirements.txt
```

### Permission Errors

**Issue: "Permission denied" during installation**

```bash
# Don't use sudo with the installer
./install.sh  # NOT: sudo ./install.sh

# Fix permissions if needed
chmod +x install.sh
chmod +x voice-control
```

## Audio Issues

### No Audio Input Detected

**Issue: "No microphone detected"**

```bash
# Check audio system
pactl info  # For PulseAudio
pipewire --version  # For PipeWire

# List audio devices
pactl list sources short  # PulseAudio
pw-cli list-objects | grep -A5 -B5 "media.class.*Audio/Source"  # PipeWire

# Test microphone
arecord -d 5 test.wav && aplay test.wav
```

**Solution:**
1. Ensure microphone is connected and working
2. Check audio system is running
3. Verify microphone permissions
4. Test with other audio applications

### Audio System Not Running

**Issue: "PulseAudio/PipeWire not available"**

```bash
# Start PulseAudio
pulseaudio --start

# Check PulseAudio status
systemctl --user status pulseaudio

# For PipeWire
systemctl --user status pipewire
systemctl --user status pipewire-pulse
```

### Audio Permissions

**Issue: "Access denied to audio device"**

```bash
# Add user to audio group
sudo usermod -a -G audio $USER

# Logout and login again, then check
groups | grep audio
```

## Service Issues

### Service Won't Start

**Issue: "Failed to start voice-control.service"**

```bash
# Check service status
systemctl --user status voice-control

# Check service file
cat ~/.config/systemd/user/voice-control.service

# Reload systemd
systemctl --user daemon-reload

# Check executable exists
ls -la ~/.local/bin/voice-control
```

### Service Crashes

**Issue: "Service keeps restarting"**

```bash
# View crash logs
journalctl --user -u voice-control --since "1 hour ago"

# Run in foreground to see errors
voice-control --log-level DEBUG

# Check resource usage
systemctl --user show voice-control --property=MemoryCurrent
```

### Auto-start Issues

**Issue: "Service doesn't start at boot"**

```bash
# Enable user lingering
sudo loginctl enable-linger $USER

# Check if enabled
systemctl --user is-enabled voice-control

# Enable if needed
systemctl --user enable voice-control
```

## GUI Issues

### System Tray Not Showing

**Issue: "System tray icon missing"**

**GNOME:**
```bash
# Install GNOME Shell extension for system tray
# Search for "AppIndicator and KStatusNotifierItem Support"
```

**KDE:**
```bash
# System tray should work by default
# Check system tray settings in System Settings
```

**XFCE:**
```bash
# Add "Notification Area" to panel
# Right-click panel → Panel → Add New Items → Notification Area
```

### GUI Crashes

**Issue: "GUI application crashes"**

```bash
# Check display server
echo $XDG_SESSION_TYPE  # Should show x11 or wayland

# Test GUI dependencies
python3 -c "import tkinter; print('Tkinter OK')"

# Run with debug output
voice-control-ui --debug
```

## Speech Recognition Issues

### No Speech Recognition

**Issue: "Speech recognition not working"**

Currently, speech recognition backends need to be implemented. This is a known limitation.

**Temporary workaround:**
- The application framework is ready
- Speech recognition backends need to be added
- Check the contributing guide for implementation details

### High CPU Usage

**Issue: "Voice control uses too much CPU"**

```bash
# Monitor resource usage
top -p $(pgrep -f voice-control)

# Check configuration
cat ~/.config/voice-control/voice-control.py

# Use low-resource configuration
# Edit config to reduce processing intensity
```

## System Integration Issues

### Input Simulation Not Working

**Issue: "Text not being typed"**

**X11:**
```bash
# Check if xdotool is installed
which xdotool || sudo apt install xdotool

# Test xdotool
xdotool type "test"
```

**Wayland:**
```bash
# Check if ydotool is installed
which ydotool || sudo apt install ydotool

# Test ydotool (may need setup)
echo "test" | ydotool type --file -
```

### Desktop Environment Compatibility

**Issue: "Not working on [desktop environment]"**

**GNOME (Wayland):**
- Some features may be limited due to Wayland security
- Consider using X11 session for full functionality

**KDE:**
- Should work with both X11 and Wayland
- Check KDE system settings for accessibility

**XFCE:**
- Lightweight environment, should work well
- Ensure all dependencies are installed

## Performance Issues

### High Memory Usage

**Issue: "Application uses too much memory"**

```bash
# Check memory usage
ps aux | grep voice-control

# Monitor memory over time
watch -n 5 'ps aux | grep voice-control'

# Check for memory leaks
valgrind --tool=memcheck voice-control
```

### Slow Startup

**Issue: "Application takes long to start"**

```bash
# Profile startup time
time voice-control --help

# Check what's loading slowly
strace -tt voice-control 2>&1 | grep -E "(open|stat|access)"
```

## Network and Security Issues

### Firewall Blocking

**Issue: "Connection issues" (if using network features)**

```bash
# Check firewall status
sudo ufw status  # Ubuntu
sudo firewall-cmd --state  # Fedora

# Voice Control should work without network access
# All processing is local
```

### SELinux Issues (Fedora/RHEL)

**Issue: "SELinux denying access"**

```bash
# Check SELinux status
sestatus

# Check for denials
sudo ausearch -m avc -ts recent | grep voice-control

# If needed, create custom policy (advanced)
```

## Debugging Tools

### Enable Debug Logging

```bash
# Run with maximum verbosity
voice-control --log-level DEBUG

# Save debug output
voice-control --log-level DEBUG 2>&1 | tee debug.log
```

### System Information Collection

```bash
# Collect system info for bug reports
echo "=== System Information ===" > system-info.txt
uname -a >> system-info.txt
lsb_release -a >> system-info.txt
python3 --version >> system-info.txt
echo "=== Audio System ===" >> system-info.txt
pactl info >> system-info.txt 2>&1
echo "=== Service Status ===" >> system-info.txt
systemctl --user status voice-control >> system-info.txt 2>&1
```

### Check Dependencies

```bash
# Check dependencies
python3 -c "
try:
    import numpy
    import librosa
    import soundfile
    print('Dependencies OK')
    print(f'NumPy: {numpy.__version__}')
    print(f'Librosa: {librosa.__version__}')
    print(f'SoundFile: {soundfile.__version__}')
except ImportError as e:
    print(f'Missing dependency: {e}')

try:
    import psutil
    print(f'PSUtil: {psutil.__version__}')
except ImportError:
    print('PSUtil: Not installed')
"
```

## Getting Help

### Before Asking for Help

1. **Check this troubleshooting guide**
2. **Run the verification script**: `python3 verify_installation.py`
3. **Check existing issues** on GitHub
4. **Collect system information** using the debug tools above

### Where to Get Help

- **GitHub Issues**: For bugs and technical problems
- **GitHub Discussions**: For questions and general help
- **Documentation**: Check all files in the `docs/` directory

### Information to Include

When asking for help, include:

1. **System Information**:
   - Linux distribution and version
   - Desktop environment
   - Python version
   - Voice Control version

2. **Problem Description**:
   - What you were trying to do
   - What happened instead
   - Error messages (full text)

3. **Logs**:
   - Service logs: `journalctl --user -u voice-control -n 50`
   - Debug output: `voice-control --log-level DEBUG`

4. **Steps to Reproduce**:
   - Exact steps that cause the problem
   - Whether it happens consistently

### Emergency Recovery

If Voice Control is causing system issues:

```bash
# Stop the service immediately
systemctl --user stop voice-control

# Disable auto-start
systemctl --user disable voice-control

# Remove from startup (if needed)
rm ~/.config/autostart/voice-control.desktop

# Uninstall completely
rm -rf ~/.local/share/voice-control
rm -rf ~/.config/voice-control
rm ~/.local/bin/voice-control*
```

This troubleshooting guide covers the most common issues. If you encounter a problem not covered here, please create an issue on GitHub with detailed information about your system and the problem.