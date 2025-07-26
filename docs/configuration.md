# Configuration Guide

Voice Control for Linux can be customized through configuration files and command-line options.

## Configuration Files

### User Configuration

The main configuration file is located at:
```
~/.config/voice-control/voice-control.py
```

This file contains a Python function that processes recognized speech text:

```python
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
```

### System Configuration

System-wide configuration (optional) can be placed at:
```
/etc/voice-control/voice-control.py
```

User configuration takes precedence over system configuration.

## Configuration Options

### Basic Settings

```json
{
    "audio": {
        "sample_rate": 16000,
        "chunk_size": 1024,
        "channels": 1
    },
    "speech_recognition": {
        "backend": "local",
        "language": "en",
        "timeout": 5.0
    },
    "gui": {
        "show_notifications": true,
        "system_tray": true,
        "minimize_to_tray": true
    }
}
```

### Audio Configuration

Configure audio input settings:

```python
# Audio processing settings
AUDIO_CONFIG = {
    'sample_rate': 16000,      # Sample rate in Hz
    'chunk_size': 1024,        # Audio chunk size
    'channels': 1,             # Mono audio
    'format': 'int16',         # Audio format
    'device_index': None,      # Auto-select device
}
```

### Speech Recognition Settings

```python
# Speech recognition configuration
SPEECH_CONFIG = {
    'language': 'en-US',       # Language code
    'timeout': 5.0,            # Recognition timeout
    'phrase_timeout': 1.0,     # Phrase timeout
    'energy_threshold': 300,   # Voice detection threshold
}
```

### GUI Configuration

```python
# GUI settings
GUI_CONFIG = {
    'show_notifications': True,    # Show desktop notifications
    'system_tray': True,          # Enable system tray
    'minimize_to_tray': True,     # Minimize to tray instead of taskbar
    'start_minimized': False,     # Start minimized
}
```

## Performance Tuning

### CPU Optimization

For systems with limited CPU resources:

```json
{
    "performance": {
        "low_cpu_mode": true,
        "processing_threads": 1,
        "audio_buffer_size": 2048
    }
}
```

### Memory Optimization

For systems with limited memory:

```json
{
    "performance": {
        "low_memory_mode": true,
        "cache_size": 100,
        "cleanup_interval": 60
    }
}
```

## Text Processing Examples

### Automatic Capitalization

```python
def voice_control_process(text):
    """Automatically capitalize sentences"""
    sentences = text.split('. ')
    capitalized = [s.capitalize() for s in sentences]
    return '. '.join(capitalized)
```

### Custom Commands

```python
def voice_control_process(text):
    """Process custom voice commands"""
    # Handle special commands
    if text.startswith("new line"):
        return text.replace("new line", "\n")
    
    if text.startswith("tab"):
        return text.replace("tab", "\t")
    
    # Handle punctuation commands
    text = text.replace(" comma ", ", ")
    text = text.replace(" period ", ". ")
    text = text.replace(" question mark ", "? ")
    text = text.replace(" exclamation point ", "! ")
    
    return text
```

### Programming Mode

```python
def voice_control_process(text):
    """Special processing for programming"""
    # Convert common programming phrases
    replacements = {
        "open paren": "(",
        "close paren": ")",
        "open bracket": "[",
        "close bracket": "]",
        "open brace": "{",
        "close brace": "}",
        "equals": "=",
        "plus equals": "+=",
        "arrow": "->",
        "dot": ".",
    }
    
    for phrase, symbol in replacements.items():
        text = text.replace(phrase, symbol)
    
    return text
```

## Service Configuration

### Systemd Service

The systemd user service is configured at:
```
~/.config/systemd/user/voice-control.service
```

### Environment Variables

Set environment variables for the service:

```bash
# In ~/.config/systemd/user/voice-control.service
[Service]
Environment=VOICE_CONTROL_CONFIG=/path/to/config
Environment=VOICE_CONTROL_LOG_LEVEL=INFO
Environment=VOICE_CONTROL_AUDIO_DEVICE=default
```

### Service Management

```bash
# Enable service
systemctl --user enable voice-control

# Start service
systemctl --user start voice-control

# Check status
systemctl --user status voice-control

# View logs
journalctl --user -u voice-control -f
```

## Troubleshooting Configuration

### Configuration Validation

Test your configuration:

```bash
# Validate configuration syntax
python3 -c "exec(open('~/.config/voice-control/voice-control.py').read())"

# Test configuration function
python3 -c "
exec(open('~/.config/voice-control/voice-control.py').read())
print(voice_control_process('hello world'))
"
```

### Common Issues

**Configuration not loading:**
- Check file permissions
- Verify Python syntax
- Check file location

**Function not working:**
- Ensure function name is `voice_control_process`
- Check function signature
- Test with simple return statement

**Service not starting:**
- Check systemd service file
- Verify executable paths
- Check environment variables

## Advanced Configuration

### Multiple Profiles

Create different configuration profiles:

```bash
# Development profile
~/.config/voice-control/profiles/development.py

# Gaming profile
~/.config/voice-control/profiles/gaming.py

# Work profile
~/.config/voice-control/profiles/work.py
```

Switch profiles with:
```bash
voice-control --profile development
```

### Plugin System (Future)

Configuration for future plugin system:

```json
{
    "plugins": {
        "enabled": ["text_expander", "custom_commands"],
        "text_expander": {
            "shortcuts": {
                "addr": "123 Main Street, City, State 12345",
                "email": "user@example.com"
            }
        }
    }
}
```

This configuration system provides flexibility while maintaining simplicity for basic use cases.