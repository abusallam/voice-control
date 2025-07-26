#!/usr/bin/env python3
"""
Desktop Autostart Manager for Voice Control Application

Provides desktop autostart functionality as a fallback mechanism
when systemd user services are not available or fail.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import subprocess
import time

logger = logging.getLogger(__name__)


class AutostartManager:
    """Manages desktop autostart configuration for voice control"""
    
    def __init__(self):
        self.autostart_dir = Path.home() / ".config/autostart"
        self.desktop_file = self.autostart_dir / "voice-control.desktop"
        self.executable_path = self._find_executable_path()
        
    def _find_executable_path(self) -> Path:
        """Find the voice-control executable path"""
        # Try different possible locations
        possible_paths = [
            Path.home() / ".local/bin/voice-control",
            Path(__file__).parent.parent.parent / "voice-control",
            Path("/usr/local/bin/voice-control"),
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_file():
                return path
                
        # Default to the project root voice-control
        return Path(__file__).parent.parent.parent / "voice-control"
    
    def install_autostart(self) -> bool:
        """Install desktop autostart entry"""
        try:
            logger.info("Installing desktop autostart entry...")
            
            # Create autostart directory
            self.autostart_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate and write desktop file
            desktop_content = self._generate_desktop_file()
            self.desktop_file.write_text(desktop_content)
            
            # Make sure the file has correct permissions
            self.desktop_file.chmod(0o644)
            
            logger.info(f"Desktop autostart file created at: {self.desktop_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install desktop autostart: {e}")
            return False
    
    def _generate_desktop_file(self) -> str:
        """Generate desktop autostart file content"""
        return f"""[Desktop Entry]
Type=Application
Name=Voice Control
Comment=Voice Control Application for Linux
Exec={self.executable_path} --daemon
Icon=audio-input-microphone
Terminal=false
NoDisplay=true
StartupNotify=false
X-GNOME-Autostart-enabled=true
X-KDE-autostart-after=panel
X-MATE-Autostart-enabled=true
Categories=Utility;Accessibility;
Keywords=voice;speech;recognition;dictation;accessibility;
"""
    
    def uninstall_autostart(self) -> bool:
        """Remove desktop autostart entry"""
        try:
            logger.info("Removing desktop autostart entry...")
            
            if self.desktop_file.exists():
                self.desktop_file.unlink()
                logger.info("Desktop autostart file removed")
            else:
                logger.info("Desktop autostart file not found")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove desktop autostart: {e}")
            return False
    
    def is_autostart_installed(self) -> bool:
        """Check if desktop autostart is installed"""
        return self.desktop_file.exists()
    
    def is_autostart_enabled(self) -> bool:
        """Check if desktop autostart is enabled"""
        if not self.is_autostart_installed():
            return False
            
        try:
            content = self.desktop_file.read_text()
            # Check if explicitly disabled
            if "X-GNOME-Autostart-enabled=false" in content:
                return False
            if "Hidden=true" in content:
                return False
            return True
        except Exception:
            return False
    
    def enable_autostart(self) -> bool:
        """Enable desktop autostart"""
        try:
            if not self.is_autostart_installed():
                return self.install_autostart()
            
            # Read current content and modify
            content = self.desktop_file.read_text()
            
            # Remove disable flags
            content = content.replace("X-GNOME-Autostart-enabled=false", "X-GNOME-Autostart-enabled=true")
            content = content.replace("Hidden=true", "Hidden=false")
            
            # Add enable flag if not present
            if "X-GNOME-Autostart-enabled=" not in content:
                content += "\nX-GNOME-Autostart-enabled=true"
            
            self.desktop_file.write_text(content)
            logger.info("Desktop autostart enabled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable desktop autostart: {e}")
            return False
    
    def disable_autostart(self) -> bool:
        """Disable desktop autostart without removing the file"""
        try:
            if not self.is_autostart_installed():
                logger.info("Desktop autostart not installed")
                return True
            
            # Read current content and modify
            content = self.desktop_file.read_text()
            
            # Add disable flag
            content = content.replace("X-GNOME-Autostart-enabled=true", "X-GNOME-Autostart-enabled=false")
            
            # Add disable flag if not present
            if "X-GNOME-Autostart-enabled=" not in content:
                content += "\nX-GNOME-Autostart-enabled=false"
            
            self.desktop_file.write_text(content)
            logger.info("Desktop autostart disabled")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable desktop autostart: {e}")
            return False
    
    def verify_startup_conditions(self) -> Dict[str, bool]:
        """Verify that startup conditions are met"""
        conditions = {
            "display_server_ready": False,
            "audio_available": False,
            "executable_exists": False,
            "permissions_ok": False
        }
        
        try:
            # Check display server
            if os.getenv("DISPLAY") or os.getenv("WAYLAND_DISPLAY"):
                conditions["display_server_ready"] = True
            
            # Check audio system
            conditions["audio_available"] = self._check_audio_system()
            
            # Check executable
            conditions["executable_exists"] = self.executable_path.exists()
            
            # Check permissions
            if conditions["executable_exists"]:
                conditions["permissions_ok"] = os.access(self.executable_path, os.X_OK)
                
        except Exception as e:
            logger.error(f"Error checking startup conditions: {e}")
        
        return conditions
    
    def _check_audio_system(self) -> bool:
        """Check if audio system is available"""
        try:
            # Check for PulseAudio
            result = subprocess.run(["pulseaudio", "--check"], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                return True
            
            # Check for PipeWire
            result = subprocess.run(["pipewire", "--version"], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                return True
            
            # Check for ALSA
            result = subprocess.run(["aplay", "-l"], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                return True
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return False
    
    def get_autostart_status(self) -> Dict[str, Any]:
        """Get detailed autostart status information"""
        status = {
            "installed": self.is_autostart_installed(),
            "enabled": self.is_autostart_enabled(),
            "executable_path": str(self.executable_path),
            "desktop_file_path": str(self.desktop_file),
            "startup_conditions": self.verify_startup_conditions(),
            "desktop_environment": self._detect_desktop_environment(),
            "error": None
        }
        
        return status
    
    def _detect_desktop_environment(self) -> str:
        """Detect the current desktop environment"""
        desktop_env = os.getenv("XDG_CURRENT_DESKTOP", "").lower()
        
        if "gnome" in desktop_env:
            return "GNOME"
        elif "kde" in desktop_env or "plasma" in desktop_env:
            return "KDE"
        elif "xfce" in desktop_env:
            return "XFCE"
        elif "mate" in desktop_env:
            return "MATE"
        elif "cinnamon" in desktop_env:
            return "Cinnamon"
        elif "lxde" in desktop_env or "lxqt" in desktop_env:
            return "LXDE/LXQt"
        else:
            return desktop_env or "Unknown"
    
    def create_diagnostic_report(self) -> str:
        """Create a diagnostic report for troubleshooting"""
        status = self.get_autostart_status()
        conditions = status["startup_conditions"]
        
        report = f"""Voice Control Autostart Diagnostic Report
==============================================

Desktop Environment: {status['desktop_environment']}
Autostart Installed: {status['installed']}
Autostart Enabled: {status['enabled']}

Executable Path: {status['executable_path']}
Desktop File: {status['desktop_file_path']}

Startup Conditions:
  Display Server Ready: {conditions['display_server_ready']}
  Audio Available: {conditions['audio_available']}
  Executable Exists: {conditions['executable_exists']}
  Permissions OK: {conditions['permissions_ok']}

Environment Variables:
  DISPLAY: {os.getenv('DISPLAY', 'Not set')}
  WAYLAND_DISPLAY: {os.getenv('WAYLAND_DISPLAY', 'Not set')}
  XDG_CURRENT_DESKTOP: {os.getenv('XDG_CURRENT_DESKTOP', 'Not set')}
  XDG_SESSION_TYPE: {os.getenv('XDG_SESSION_TYPE', 'Not set')}

Recommendations:
"""
        
        # Add recommendations based on conditions
        if not conditions["display_server_ready"]:
            report += "  - Display server not ready. Check DISPLAY or WAYLAND_DISPLAY variables.\n"
        
        if not conditions["audio_available"]:
            report += "  - Audio system not available. Check PulseAudio/PipeWire/ALSA installation.\n"
        
        if not conditions["executable_exists"]:
            report += f"  - Executable not found at {status['executable_path']}. Check installation.\n"
        
        if not conditions["permissions_ok"]:
            report += "  - Executable permissions issue. Run: chmod +x voice-control\n"
        
        if not status["installed"]:
            report += "  - Install autostart with: voice-control --autostart install\n"
        
        if not status["enabled"]:
            report += "  - Enable autostart with: voice-control --autostart enable\n"
        
        return report
    
    def repair_autostart(self) -> bool:
        """Attempt to repair autostart configuration"""
        try:
            logger.info("Attempting to repair autostart configuration...")
            
            # Remove existing broken configuration
            if self.desktop_file.exists():
                self.desktop_file.unlink()
            
            # Reinstall with current settings
            if not self.install_autostart():
                return False
            
            # Verify conditions
            conditions = self.verify_startup_conditions()
            
            if not conditions["executable_exists"]:
                logger.error("Cannot repair: executable not found")
                return False
            
            if not conditions["permissions_ok"]:
                logger.info("Fixing executable permissions...")
                self.executable_path.chmod(0o755)
            
            logger.info("Autostart configuration repaired successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to repair autostart: {e}")
            return False


def main():
    """Command line interface for autostart management"""
    import argparse
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    parser = argparse.ArgumentParser(description="Voice Control Autostart Manager")
    parser.add_argument("action", choices=[
        "install", "uninstall", "enable", "disable", 
        "status", "verify", "repair", "diagnostic"
    ], help="Action to perform")
    
    args = parser.parse_args()
    autostart_mgr = AutostartManager()
    
    if args.action == "install":
        success = autostart_mgr.install_autostart()
    elif args.action == "uninstall":
        success = autostart_mgr.uninstall_autostart()
    elif args.action == "enable":
        success = autostart_mgr.enable_autostart()
    elif args.action == "disable":
        success = autostart_mgr.disable_autostart()
    elif args.action == "status":
        status = autostart_mgr.get_autostart_status()
        print(f"Autostart Status:")
        print(f"  Installed: {status['installed']}")
        print(f"  Enabled: {status['enabled']}")
        print(f"  Desktop Environment: {status['desktop_environment']}")
        print(f"  Executable: {status['executable_path']}")
        success = True
    elif args.action == "verify":
        conditions = autostart_mgr.verify_startup_conditions()
        print("Startup Conditions:")
        for condition, status in conditions.items():
            print(f"  {condition.replace('_', ' ').title()}: {status}")
        success = all(conditions.values())
    elif args.action == "repair":
        success = autostart_mgr.repair_autostart()
    elif args.action == "diagnostic":
        report = autostart_mgr.create_diagnostic_report()
        print(report)
        success = True
    
    exit(0 if success else 1)


if __name__ == "__main__":
    main()