#!/usr/bin/env python3
"""
VoiceWhisper for Linux - Debian 12 GNOME/Wayland
A voice-to-text system that transcribes speech and types it at cursor location
"""

import whisper
import sounddevice as sd
import numpy as np
import tempfile
import os
import subprocess
import threading
import time
import signal
import sys
from pathlib import Path

# Add our voice_control modules
sys.path.insert(0, str(Path(__file__).parent))
from voice_control.core.error_handler import get_error_handler, production_safe_execute

class VoiceWhisper:
    def __init__(self):
        self.error_handler = get_error_handler()
        self.model = None
        self.listening = False
        self.recording = False
        self.audio_data = []
        self.sample_rate = 16000
        self.channels = 1
        
        print("🎤 VoiceWhisper for Linux - Debian 12 GNOME/Wayland")
        print("=" * 50)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.stop_listening()
        sys.exit(0)
    
    @production_safe_execute(context="whisper_model_loading")
    def load_model(self, model_size="base"):
        """Load Whisper model"""
        print(f"🧠 Loading Whisper model '{model_size}'...")
        try:
            self.model = whisper.load_model(model_size)
            print(f"✅ Whisper model '{model_size}' loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to load Whisper model: {e}")
            return False
    
    @production_safe_execute(context="audio_device_check")
    def check_audio_devices(self):
        """Check available audio devices"""
        print("🔊 Checking audio devices...")
        try:
            devices = sd.query_devices()
            print("Available audio devices:")
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    print(f"  {i}: {device['name']} (Input: {device['max_input_channels']} channels)")
            return True
        except Exception as e:
            print(f"❌ Audio device check failed: {e}")
            return False
    
    @production_safe_execute(context="text_input")
    def type_text(self, text):
        """Copy text to clipboard and show notification - most reliable for GNOME/Wayland"""
        if not text.strip():
            return False
            
        # Clean up the text
        text = text.strip()
        
        print(f"🖊️  Processing transcribed text: {text}")
        
        try:
            # Copy text to clipboard
            subprocess.run(['/usr/bin/wl-copy'], input=text.encode(), check=True, timeout=5)
            
            # Show desktop notification with the transcribed text
            try:
                subprocess.run([
                    'notify-send', 
                    '🎤 VoiceWhisper - Text Ready!', 
                    f'Transcribed: "{text}"\n\n✅ Copied to clipboard\n💡 Press Ctrl+V to paste where you want it',
                    '-t', '8000',  # Show for 8 seconds
                    '-u', 'normal'
                ], check=True, timeout=3)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("⚠️  Notification failed (install libnotify-bin for notifications)")
            
            print(f"✅ Text copied to clipboard: {text}")
            print("🔔 Notification shown - Press Ctrl+V to paste!")
            print("💡 Click where you want the text, then press Ctrl+V")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Clipboard copy failed: {e}")
            
            # Fallback: try xclip
            try:
                subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode(), check=True, timeout=5)
                print(f"✅ Text copied to clipboard via xclip: {text}")
                print("💡 Press Ctrl+V to paste!")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("❌ Both wl-copy and xclip failed")
                
        except FileNotFoundError:
            print("❌ wl-copy not found. Install with: sudo apt install wl-clipboard")
        
        # Final fallback: just print the text
        print(f"📝 TRANSCRIBED TEXT: {text}")
        print("💡 Copy this text manually if needed")
        return False
    
    @production_safe_execute(context="speech_transcription")
    def transcribe_audio(self, audio_file):
        """Transcribe audio file using Whisper"""
        if not self.model:
            print("❌ Whisper model not loaded")
            return None
            
        try:
            print("🎯 Transcribing audio...")
            result = self.model.transcribe(audio_file, language=None)  # Auto-detect language
            text = result['text'].strip()
            
            if text:
                print(f"🗣️  Transcribed: {text}")
                return text
            else:
                print("🔇 No speech detected")
                return None
                
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            return None
    
    def audio_callback(self, indata, frames, time, status):
        """Audio input callback"""
        if status:
            print(f"⚠️  Audio status: {status}")
        
        if self.recording:
            # Convert to the right format and append
            audio_data = indata.copy().flatten()
            self.audio_data.extend(audio_data)
    
    @production_safe_execute(context="voice_recording")
    def record_and_transcribe(self, duration=5):
        """Record audio for specified duration and transcribe"""
        if not self.model:
            print("❌ Please load Whisper model first")
            return False
        
        print(f"🎙️  Recording for {duration} seconds... Speak now!")
        
        try:
            # Record audio
            self.audio_data = []
            self.recording = True
            
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=self.audio_callback,
                dtype=np.float32
            ):
                time.sleep(duration)
            
            self.recording = False
            
            if not self.audio_data:
                print("🔇 No audio recorded")
                return False
            
            # Save to temporary file
            audio_array = np.array(self.audio_data, dtype=np.float32)
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                # Write as WAV file
                import soundfile as sf
                sf.write(temp_file.name, audio_array, self.sample_rate)
                temp_filename = temp_file.name
            
            try:
                # Transcribe
                text = self.transcribe_audio(temp_filename)
                
                if text:
                    # Type the text
                    success = self.type_text(text)
                    return success
                else:
                    print("🔇 No speech detected in recording")
                    return False
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_filename)
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Recording failed: {e}")
            return False
    
    def start_continuous_listening(self):
        """Start continuous listening mode"""
        print("🎧 Starting continuous listening mode...")
        print("Press Ctrl+C to stop")
        print("Speak and pause for transcription...")
        
        self.listening = True
        
        try:
            while self.listening:
                print("\n🎙️  Listening... (speak now)")
                success = self.record_and_transcribe(duration=3)
                
                if success:
                    print("✅ Text typed successfully")
                else:
                    print("⚠️  No speech detected or typing failed")
                
                # Short pause between recordings
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping continuous listening...")
        finally:
            self.stop_listening()
    
    def stop_listening(self):
        """Stop listening"""
        self.listening = False
        self.recording = False
        print("🛑 Stopped listening")
    
    def run_once(self, duration=5):
        """Record once and transcribe"""
        if not self.load_model():
            return False
        
        return self.record_and_transcribe(duration)
    
    def run_continuous(self):
        """Run in continuous mode"""
        if not self.load_model():
            return False
        
        self.check_audio_devices()
        self.start_continuous_listening()


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VoiceWhisper - Voice to Text for Linux")
    parser.add_argument("--model", default="base", choices=["tiny", "base", "small", "medium", "large"],
                       help="Whisper model size (default: base)")
    parser.add_argument("--duration", type=int, default=5,
                       help="Recording duration in seconds (default: 5)")
    parser.add_argument("--continuous", action="store_true",
                       help="Run in continuous listening mode")
    parser.add_argument("--test-audio", action="store_true",
                       help="Test audio devices only")
    
    args = parser.parse_args()
    
    whisper_app = VoiceWhisper()
    
    if args.test_audio:
        whisper_app.check_audio_devices()
        return
    
    if args.continuous:
        whisper_app.run_continuous()
    else:
        print(f"🎙️  Single recording mode ({args.duration} seconds)")
        if whisper_app.load_model(args.model):
            whisper_app.record_and_transcribe(args.duration)


if __name__ == "__main__":
    main()