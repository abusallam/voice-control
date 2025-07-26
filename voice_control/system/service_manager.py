#!/usr/bin/env python3
"""
Service Manager for Voice Control Application

Handles systemd user service installation, management, and monitoring.
This replaces the problematic system-wide service approach.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import time

logger = logging.getLogger(__name__)


class ServiceManager:
    """Manages systemd user service for voice control application"""
    
    def __init__(self):
        self.service_name = "voice-control"
        self.user_service_dir = Path.home() / ".config/systemd/user"
        self.service_file = self.user_service_dir / f"{self.service_name}.service"
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
    
    def install_user_service(self) -> bool:
        """Install voice control as a user systemd service"""
        try:
            logger.info("Installing voice control user service...")
            
            # Create user systemd directory
            self.user_service_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate and write service file
            service_content = self._generate_user_service_file()
            self.service_file.write_text(service_content)
            
            logger.info(f"Service file created at: {self.service_file}")
            
            # Reload systemd user daemon
            self._run_systemctl_command(["daemon-reload"])
            
            # Enable the service
            self._run_systemctl_command(["enable", self.service_name])
            
            logger.info("User service installed and enabled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install user service: {e}")
            return False
    
    def _generate_user_service_file(self) -> str:
        """Generate proper user service configuration"""
        return f"""[Unit]
Description=Voice Control Application
Documentation=https://github.com/your-repo/voice-control
After=graphical-session.target pulseaudio.service
Wants=graphical-session.target

[Service]
Type=simple
ExecStart={self.executable_path} --daemon
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
StartLimitInterval=60
StartLimitBurst=3

# Environment variables
Environment=DISPLAY=:0
Environment=HOME={Path.home()}
Environment=XDG_RUNTIME_DIR=/run/user/%i
Environment=PULSE_RUNTIME_PATH=/run/user/%i/pulse

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths={Path.home()}/.config/voice-control {Path.home()}/.local/share/voice-control

[Install]
WantedBy=default.target
"""
    
    def uninstall_user_service(self) -> bool:
        """Uninstall the user service"""
        try:
            logger.info("Uninstalling voice control user service...")
            
            # Stop the service if running
            self.stop_service()
            
            # Disable the service
            self._run_systemctl_command(["disable", self.service_name])
            
            # Remove service file
            if self.service_file.exists():
                self.service_file.unlink()
                logger.info("Service file removed")
            
            # Reload daemon
            self._run_systemctl_command(["daemon-reload"])
            
            logger.info("User service uninstalled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to uninstall user service: {e}")
            return False
    
    def start_service(self) -> bool:
        """Start the voice control service"""
        try:
            logger.info("Starting voice control service...")
            self._run_systemctl_command(["start", self.service_name])
            
            # Wait a moment and check if it started successfully
            time.sleep(2)
            if self.is_service_running():
                logger.info("Service started successfully")
                return True
            else:
                logger.error("Service failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            return False
    
    def stop_service(self) -> bool:
        """Stop the voice control service"""
        try:
            logger.info("Stopping voice control service...")
            self._run_systemctl_command(["stop", self.service_name])
            logger.info("Service stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop service: {e}")
            return False
    
    def restart_service(self) -> bool:
        """Restart the voice control service"""
        try:
            logger.info("Restarting voice control service...")
            self._run_systemctl_command(["restart", self.service_name])
            
            # Wait and verify restart
            time.sleep(2)
            if self.is_service_running():
                logger.info("Service restarted successfully")
                return True
            else:
                logger.error("Service failed to restart")
                return False
                
        except Exception as e:
            logger.error(f"Failed to restart service: {e}")
            return False
    
    def is_service_running(self) -> bool:
        """Check if the service is currently running"""
        try:
            result = self._run_systemctl_command(["is-active", self.service_name], capture_output=True)
            return result.stdout.strip() == "active"
        except Exception:
            return False
    
    def is_service_enabled(self) -> bool:
        """Check if the service is enabled"""
        try:
            result = self._run_systemctl_command(["is-enabled", self.service_name], capture_output=True)
            return result.stdout.strip() == "enabled"
        except Exception:
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get detailed service status information"""
        status = {
            "installed": self.service_file.exists(),
            "enabled": False,
            "running": False,
            "last_logs": [],
            "error": None
        }
        
        try:
            if status["installed"]:
                status["enabled"] = self.is_service_enabled()
                status["running"] = self.is_service_running()
                
                # Get recent logs
                try:
                    result = self._run_systemctl_command([
                        "status", self.service_name, "--no-pager", "-n", "10"
                    ], capture_output=True)
                    status["last_logs"] = result.stdout.split('\n')
                except Exception as e:
                    status["last_logs"] = [f"Could not retrieve logs: {e}"]
                    
        except Exception as e:
            status["error"] = str(e)
            
        return status
    
    def _run_systemctl_command(self, args: list, capture_output: bool = False) -> Optional[subprocess.CompletedProcess]:
        """Run a systemctl --user command"""
        cmd = ["systemctl", "--user"] + args
        
        try:
            if capture_output:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return result
            else:
                subprocess.run(cmd, check=True)
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"systemctl command failed: {' '.join(cmd)}")
            logger.error(f"Error: {e}")
            if capture_output and e.stdout:
                logger.error(f"stdout: {e.stdout}")
            if capture_output and e.stderr:
                logger.error(f"stderr: {e.stderr}")
            raise
    
    def enable_user_lingering(self) -> bool:
        """Enable user lingering so services start at boot without login"""
        try:
            # Check if already enabled
            linger_file = Path(f"/var/lib/systemd/linger/{os.getenv('USER')}")
            if linger_file.exists():
                logger.info("User lingering already enabled")
                return True
            
            # Enable lingering
            subprocess.run(["sudo", "loginctl", "enable-linger", os.getenv('USER')], check=True)
            logger.info("User lingering enabled - services will start at boot")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"Could not enable user lingering: {e}")
            logger.warning("Service may not start automatically at boot")
            return False
        except Exception as e:
            logger.error(f"Error enabling user lingering: {e}")
            return False
    
    def setup_complete_service(self) -> bool:
        """Complete service setup including installation and configuration"""
        try:
            logger.info("Setting up voice control service...")
            
            # Install the service
            if not self.install_user_service():
                logger.warning("Systemd service installation failed, trying desktop autostart fallback...")
                return self._setup_autostart_fallback()
            
            # Try to enable user lingering for boot startup
            self.enable_user_lingering()
            
            # Verify installation
            status = self.get_service_status()
            if status["installed"] and status["enabled"]:
                logger.info("Service setup completed successfully")
                logger.info("You can now start the service with: systemctl --user start voice-control")
                
                # Also setup autostart as backup
                self._setup_autostart_fallback()
                
                return True
            else:
                logger.error("Service setup verification failed, trying autostart fallback...")
                return self._setup_autostart_fallback()
                
        except Exception as e:
            logger.error(f"Service setup failed: {e}")
            logger.info("Trying desktop autostart fallback...")
            return self._setup_autostart_fallback()
    
    def _setup_autostart_fallback(self) -> bool:
        """Setup desktop autostart as fallback mechanism"""
        try:
            from voice_control.system.autostart_manager import AutostartManager
            
            autostart_mgr = AutostartManager()
            
            # Install and enable autostart
            if autostart_mgr.install_autostart():
                logger.info("Desktop autostart fallback installed successfully")
                
                # Verify startup conditions
                conditions = autostart_mgr.verify_startup_conditions()
                if not all(conditions.values()):
                    logger.warning("Some startup conditions not met:")
                    for condition, status in conditions.items():
                        if not status:
                            logger.warning(f"  - {condition.replace('_', ' ').title()}: {status}")
                    
                    # Try to repair
                    if autostart_mgr.repair_autostart():
                        logger.info("Autostart configuration repaired")
                
                return True
            else:
                logger.error("Desktop autostart fallback installation failed")
                return False
                
        except Exception as e:
            logger.error(f"Autostart fallback setup failed: {e}")
            return False


def main():
    """Command line interface for service management"""
    import argparse
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    parser = argparse.ArgumentParser(description="Voice Control Service Manager")
    parser.add_argument("action", choices=[
        "install", "uninstall", "start", "stop", "restart", 
        "status", "enable-lingering", "setup"
    ], help="Action to perform")
    
    args = parser.parse_args()
    service_mgr = ServiceManager()
    
    if args.action == "install":
        success = service_mgr.install_user_service()
    elif args.action == "uninstall":
        success = service_mgr.uninstall_user_service()
    elif args.action == "start":
        success = service_mgr.start_service()
    elif args.action == "stop":
        success = service_mgr.stop_service()
    elif args.action == "restart":
        success = service_mgr.restart_service()
    elif args.action == "status":
        status = service_mgr.get_service_status()
        print(f"Service Status:")
        print(f"  Installed: {status['installed']}")
        print(f"  Enabled: {status['enabled']}")
        print(f"  Running: {status['running']}")
        if status['error']:
            print(f"  Error: {status['error']}")
        if status['last_logs']:
            print("  Recent logs:")
            for log in status['last_logs'][-5:]:  # Show last 5 lines
                print(f"    {log}")
        success = True
    elif args.action == "enable-lingering":
        success = service_mgr.enable_user_lingering()
    elif args.action == "setup":
        success = service_mgr.setup_complete_service()
    
    exit(0 if success else 1)


if __name__ == "__main__":
    main()