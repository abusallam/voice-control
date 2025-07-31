#!/usr/bin/env python3
import subprocess

text = "Hello from VoiceWhisper test!"

print(f"Testing clipboard with text: {text}")

try:
    # Copy text to clipboard
    result = subprocess.run(['/usr/bin/wl-copy'], input=text.encode(), check=True, timeout=5)
    print(f"✅ wl-copy succeeded with return code: {result.returncode}")
    
    # Test paste
    paste_result = subprocess.run(['/usr/bin/wl-paste'], capture_output=True, text=True, timeout=5)
    print(f"✅ Clipboard contains: {paste_result.stdout}")
    
    # Show notification
    subprocess.run([
        'notify-send', 
        '🎤 VoiceWhisper Test', 
        f'Text copied to clipboard: "{text}"\n\nPress Ctrl+V to paste!',
        '-t', '5000'
    ], timeout=3)
    
    print("✅ Notification sent!")
    print("💡 Now try pressing Ctrl+V in a text editor!")
    
except subprocess.CalledProcessError as e:
    print(f"❌ CalledProcessError: {e}")
    print(f"Return code: {e.returncode}")
except FileNotFoundError as e:
    print(f"❌ FileNotFoundError: {e}")
except Exception as e:
    print(f"❌ Other error: {e}")
    print(f"Type: {type(e)}")