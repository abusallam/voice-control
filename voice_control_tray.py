#!/usr/bin/env python3
"""
Voice Control System Tray - Complete solution for Debian 12 GNOME/Wayland
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')

from gi.repository import Gtk, AyatanaAppIndicator3 as AppIndicator3, GObject, GLib
import threading
import subprocess
import time
import os
import sys
import tempfile
from pathlib import Path

# Add our modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    import whisper
    import sounddevice as sd
    import numpy as np
    import soundfile as sf
    WHISPER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Whisper not available: {e}")
    WHISPER_AVAILABLE = False

class VoiceControlTray:
    def __init__(self):
        self.indicator = AppIndicator3.Indicator.new(
            "voice-control",
            "audio-input-microphone",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        
        # Voice recognition
        self.whisper_model = None
        self.is_recording = False
        self.is_listening = False
        
        # Load Whisper model in background
        if WHISPER_AVAILABLE:
            threading.Thread(target=self._load_whisper_model, daemon=True).start()
        
        # Create menu
        self.create_menu()
        
        print("🎤 Voice Control Tray started")
    
    def _load_whisper_model(self):
        """Load Whisper model in background"""
        try:
            print("🧠 Loading Whisper model...")
            self.whisper_model = whisper.load_model("base")
            print("✅ Whisper model loaded")
            
            # Update menu to show ready status
            GLib.idle_add(self.update_menu_status, "✅ Ready")
        except Exception as e:
            print(f"❌ Failed to load Whisper: {e}")
            GLib.idle_add(self.update_menu_status, "❌ Error")
    
    def create_menu(self):
        """Create the system tray menu"""
        menu = Gtk.Menu()
        
        # Status item
        self.status_item = Gtk.MenuItem(label="🧠 Loading...")
        self.status_item.set_sensitive(False)
        menu.append(self.status_item)
        
        # Separator
        separator1 = Gtk.SeparatorMenuItem()
        menu.append(separator1)
        
        # Quick Record (5 seconds)
        quick_record_item = Gtk.MenuItem(label="🎙️  Quick Record (5s)")
        quick_record_item.connect("activate", self.quick_record)
        menu.append(quick_record_item)
        
        # Start/Stop Continuous Listening
        self.listen_item = Gtk.MenuItem(label="🎧 Start Continuous Listening")
        self.listen_item.connect("activate", self.toggle_continuous_listening)
        menu.append(self.listen_item)
        
        # Separator
        separator2 = Gtk.SeparatorMenuItem()
        menu.append(separator2)
        
        # AI Agent Services submenu
        ai_services_item = Gtk.MenuItem(label="🤖 AI Agent Services")
        ai_services_menu = Gtk.Menu()
        
        # Voice Control Engine
        engine_item = Gtk.MenuItem(label="🎛️  Voice Control Engine")
        engine_item.connect("activate", self.start_voice_engine)
        ai_services_menu.append(engine_item)
        
        # Error Handler Status
        error_handler_item = Gtk.MenuItem(label="🛡️  Error Handler Status")
        error_handler_item.connect("activate", self.show_error_status)
        ai_services_menu.append(error_handler_item)
        
        # System Diagnostics
        diagnostics_item = Gtk.MenuItem(label="🔧 System Diagnostics")
        diagnostics_item.connect("activate", self.run_diagnostics)
        ai_services_menu.append(diagnostics_item)
        
        ai_services_item.set_submenu(ai_services_menu)
        menu.append(ai_services_item)
        
        # Separator
        separator3 = Gtk.SeparatorMenuItem()
        menu.append(separator3)
        
        # Settings
        settings_item = Gtk.MenuItem(label="⚙️  Settings")
        settings_item.connect("activate", self.show_settings)
        menu.append(settings_item)
        
        # About
        about_item = Gtk.MenuItem(label="ℹ️  About")
        about_item.connect("activate", self.show_about)
        menu.append(about_item)
        
        # Separator
        separator4 = Gtk.SeparatorMenuItem()
        menu.append(separator4)
        
        # Exit
        exit_item = Gtk.MenuItem(label="🚪 Exit")
        exit_item.connect("activate", self.quit_application)
        menu.append(exit_item)
        
        menu.show_all()
        self.indicator.set_menu(menu)
    
    def update_menu_status(self, status):
        """Update the status item in the menu"""
        self.status_item.set_label(status)
    
    def quick_record(self, widget):
        """Quick 5-second recording"""
        if not WHISPER_AVAILABLE or not self.whisper_model:
            self.show_notification("❌ Error", "Whisper not available")
            return
        
        if self.is_recording:
            self.show_notification("⚠️  Busy", "Already recording...")
            return
        
        # Start recording in background thread
        threading.Thread(target=self._do_quick_record, daemon=True).start()
    
    def _do_quick_record(self):
        """Perform the actual recording"""
        try:
            self.is_recording = True
            GLib.idle_add(self.update_menu_status, "🎙️  Recording...")
            
            # Show notification
            GLib.idle_add(self.show_notification, "🎙️  Recording", "Speak now for 5 seconds...")
            
            # Record audio
            duration = 5
            sample_rate = 16000
            
            print(f"🎙️  Recording for {duration} seconds...")
            audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.float32)
            sd.wait()  # Wait for recording to complete
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                sf.write(temp_file.name, audio_data, sample_rate)
                temp_filename = temp_file.name
            
            try:
                # Transcribe
                GLib.idle_add(self.update_menu_status, "🎯 Transcribing...")
                print("🎯 Transcribing audio...")
                
                result = self.whisper_model.transcribe(temp_filename, language=None)
                text = result['text'].strip()
                
                if text:
                    print(f"🗣️  Transcribed: {text}")
                    
                    # Type the text automatically
                    success = self._type_text_automatically(text)
                    
                    if success:
                        GLib.idle_add(self.show_notification, "✅ Success", f"Typed: {text[:50]}...")
                        GLib.idle_add(self.update_menu_status, "✅ Ready")
                    else:
                        # Fallback to clipboard
                        self._copy_to_clipboard(text)
                        GLib.idle_add(self.show_notification, "📋 Copied to Clipboard", f"Press Ctrl+V to paste: {text[:50]}...")
                        GLib.idle_add(self.update_menu_status, "✅ Ready")
                else:
                    print("🔇 No speech detected")
                    GLib.idle_add(self.show_notification, "🔇 No Speech", "No speech detected in recording")
                    GLib.idle_add(self.update_menu_status, "✅ Ready")
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_filename)
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Recording failed: {e}")
            GLib.idle_add(self.show_notification, "❌ Error", f"Recording failed: {str(e)[:50]}")
            GLib.idle_add(self.update_menu_status, "❌ Error")
        finally:
            self.is_recording = False
    
    def _type_text_automatically(self, text):
        """Try to type text automatically using multiple methods"""
        print(f"🖊️  Attempting to type: {text[:50]}...")
        
        # Method 1: Try wtype with clipboard paste (most reliable for Wayland)
        try:
            # Copy to clipboard first
            subprocess.run(['/usr/bin/wl-copy'], input=text.encode(), check=True, timeout=3)
            time.sleep(0.1)  # Small delay
            
            # Send Ctrl+V using wtype
            subprocess.run(['/usr/bin/wtype', '-M', 'ctrl', 'v'], check=True, timeout=3)
            print(f"✅ Typed via wtype+clipboard: {text[:50]}...")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Method 2: Try xdotool with clipboard paste
        try:
            subprocess.run(['/usr/bin/wl-copy'], input=text.encode(), check=True, timeout=3)
            time.sleep(0.1)
            subprocess.run(['/usr/bin/xdotool', 'key', 'ctrl+v'], check=True, timeout=3)
            print(f"✅ Typed via xdotool+clipboard: {text[:50]}...")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Method 3: Direct wtype
        try:
            subprocess.run(['/usr/bin/wtype', text], check=True, timeout=5)
            print(f"✅ Typed via wtype: {text[:50]}...")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        print("⚠️  Automatic typing failed, using clipboard fallback")
        return False
    
    def _copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        try:
            subprocess.run(['/usr/bin/wl-copy'], input=text.encode(), check=True, timeout=3)
            print(f"✅ Copied to clipboard: {text[:50]}...")
        except Exception as e:
            print(f"❌ Clipboard copy failed: {e}")
    
    def toggle_continuous_listening(self, widget):
        """Toggle continuous listening mode"""
        if not WHISPER_AVAILABLE or not self.whisper_model:
            self.show_notification("❌ Error", "Whisper not available")
            return
        
        if self.is_listening:
            self.stop_continuous_listening()
        else:
            self.start_continuous_listening()
    
    def start_continuous_listening(self):
        """Start continuous listening mode"""
        self.is_listening = True
        self.listen_item.set_label("🛑 Stop Continuous Listening")
        self.update_menu_status("🎧 Listening...")
        self.show_notification("🎧 Continuous Mode", "Listening continuously... Click to stop")
        
        # Start listening in background thread
        threading.Thread(target=self._continuous_listening_loop, daemon=True).start()
    
    def stop_continuous_listening(self):
        """Stop continuous listening mode"""
        self.is_listening = False
        self.listen_item.set_label("🎧 Start Continuous Listening")
        self.update_menu_status("✅ Ready")
        self.show_notification("🛑 Stopped", "Continuous listening stopped")
    
    def _continuous_listening_loop(self):
        """Continuous listening loop"""
        while self.is_listening:
            try:
                if not self.is_recording:  # Don't interfere with quick recording
                    self._do_quick_record()
                time.sleep(1)  # Short pause between recordings
            except Exception as e:
                print(f"❌ Continuous listening error: {e}")
                break
    
    def start_voice_engine(self, widget):
        """Start the voice control engine"""
        try:
            subprocess.Popen([
                sys.executable, 
                str(Path(__file__).parent / "voice_control" / "main.py"),
                "--daemon"
            ])
            self.show_notification("🎛️  Engine Started", "Voice Control Engine is now running")
        except Exception as e:
            self.show_notification("❌ Error", f"Failed to start engine: {str(e)[:50]}")
    
    def show_error_status(self, widget):
        """Show error handler status"""
        try:
            from voice_control.core.error_handler import get_error_handler
            error_handler = get_error_handler()
            stats = error_handler.get_error_statistics()
            
            message = f"Total Errors: {stats.get('total_errors', 0)}\nError Types: {stats.get('error_types', 0)}"
            self.show_notification("🛡️  Error Handler", message)
        except Exception as e:
            self.show_notification("❌ Error", f"Cannot get error status: {str(e)[:50]}")
    
    def run_diagnostics(self, widget):
        """Run system diagnostics"""
        try:
            subprocess.Popen([sys.executable, str(Path(__file__).parent / "test_error_handler.py")])
            self.show_notification("🔧 Diagnostics", "Running system diagnostics...")
        except Exception as e:
            self.show_notification("❌ Error", f"Cannot run diagnostics: {str(e)[:50]}")
    
    def show_settings(self, widget):
        """Show settings dialog"""
        dialog = Gtk.MessageDialog(
            transient_for=None,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Voice Control Settings"
        )
        dialog.format_secondary_text(
            "Settings:\n"
            "• Model: Whisper Base\n"
            "• Sample Rate: 16kHz\n"
            "• Recording Duration: 5s\n"
            "• Auto-typing: Enabled\n"
            "\nKeyboard Shortcuts:\n"
            "• Ctrl+Alt+V: Quick Record\n"
            "• Ctrl+Alt+L: Toggle Listening"
        )
        dialog.run()
        dialog.destroy()
    
    def show_about(self, widget):
        """Show about dialog"""
        dialog = Gtk.MessageDialog(
            transient_for=None,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Voice Control for Linux"
        )
        dialog.format_secondary_text(
            "Version: 1.0\n"
            "Platform: Debian 12 GNOME/Wayland\n"
            "Speech Engine: OpenAI Whisper\n"
            "\nFeatures:\n"
            "• Voice to text transcription\n"
            "• Automatic typing at cursor\n"
            "• System tray integration\n"
            "• Continuous listening mode\n"
            "• Error handling & recovery"
        )
        dialog.run()
        dialog.destroy()
    
    def show_notification(self, title, message):
        """Show desktop notification"""
        try:
            subprocess.run([
                'notify-send',
                title,
                message,
                '-t', '3000',
                '-i', 'audio-input-microphone'
            ], timeout=2)
        except:
            print(f"Notification: {title} - {message}")
    
    def quit_application(self, widget):
        """Quit the application properly"""
        print("🚪 Exiting Voice Control Tray...")
        self.is_listening = False
        self.is_recording = False
        Gtk.main_quit()
    
    def run(self):
        """Run the application"""
        try:
            Gtk.main()
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
            self.quit_application(None)

def main():
    """Main function"""
    print("🎤 Starting Voice Control System Tray...")
    
    # Check if required packages are available
    if not WHISPER_AVAILABLE:
        print("❌ Whisper not available. Please install with:")
        print("   pip install openai-whisper sounddevice soundfile")
        return 1
    
    try:
        app = VoiceControlTray()
        app.run()
        return 0
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())