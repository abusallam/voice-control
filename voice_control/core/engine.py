#!/usr/bin/env python3
"""
Voice Control Engine

Main engine that orchestrates all voice control components including
speech recognition, input handling, system tray, and health monitoring.
"""

import logging
import threading
import time
import signal
import sys
from typing import Optional, Dict, Any, Callable
from pathlib import Path

# Import core components
from voice_control.core.resource_manager import get_resource_manager
from voice_control.core.error_handler import get_error_handler, safe_execute
from voice_control.core.health_monitor import get_health_monitor
from voice_control.core.diagnostics import get_logging_manager

# Import system components
from voice_control.system.service_manager import ServiceManager
from voice_control.system.clipboard_manager import get_clipboard_manager
from voice_control.system.input_handler import get_input_handler

# Import GUI components
try:
    from voice_control.gui.system_tray import VoiceControlTray
    from voice_control.gui.notification_manager import get_notification_manager
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

logger = logging.getLogger(__name__)


class VoiceControlEngine:
    """Main voice control engine that orchestrates all components"""
    
    def __init__(self, resource_manager=None, error_handler=None, daemon_mode=False):
        self.daemon_mode = daemon_mode
        self.running = False
        self.shutdown_requested = False
        
        # Core components
        self.resource_manager = resource_manager or get_resource_manager()
        self.error_handler = error_handler or get_error_handler()
        self.health_monitor = get_health_monitor(self.resource_manager, self.error_handler)
        self.logging_manager = get_logging_manager()
        
        # System components
        self.service_manager = ServiceManager()
        self.clipboard_manager = get_clipboard_manager()
        self.input_handler = get_input_handler()
        
        # GUI components
        self.system_tray = None
        self.notification_manager = None
        
        # Voice recognition components (placeholder for now)
        self.speech_recognition = None
        self.voice_processor = None
        
        # Configuration
        self.config = self._load_configuration()
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        logger.info("Voice control engine initialized")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            self.shutdown()
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration from file"""
        config_dir = Path.home() / ".config/voice-control"
        config_file = config_dir / "settings.json"
        
        # Default configuration
        default_config = {
            "speech_recognition": {
                "engine": "whisper",
                "model_size": "base",
                "language": "en",
                "timeout": 10
            },
            "input": {
                "typing_delay": 0.01,
                "verify_input": True
            },
            "gui": {
                "show_tray": True,
                "show_notifications": True,
                "minimize_to_tray": True
            },
            "health_monitoring": {
                "enabled": True,
                "check_interval": 30,
                "auto_remediation": True
            },
            "logging": {
                "level": "INFO",
                "performance_logging": True,
                "log_retention_days": 30
            }
        }
        
        try:
            if config_file.exists():
                import json
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                
                # Merge with defaults
                config = default_config.copy()
                config.update(user_config)
                
                logger.info(f"Configuration loaded from {config_file}")
                return config
            else:
                # Create default config file
                config_dir.mkdir(parents=True, exist_ok=True)
                import json
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
                
                logger.info(f"Created default configuration at {config_file}")
                return default_config
                
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return default_config
    
    @safe_execute(get_error_handler(), "engine_start")
    def start(self):
        """Start the voice control engine"""
        if self.running:
            logger.warning("Engine already running")
            return
        
        logger.info("Starting voice control engine...")
        
        try:
            # Start core components
            self._start_core_components()
            
            # Start GUI components if not in daemon mode
            if not self.daemon_mode and GUI_AVAILABLE:
                self._start_gui_components()
            
            # Start voice recognition
            self._start_voice_recognition()
            
            # Mark as running
            self.running = True
            
            logger.info("Voice control engine started successfully")
            
            # Show startup notification
            if self.notification_manager:
                self.notification_manager.show_success(
                    "Voice Control Started",
                    "Voice control system is now active"
                )
            
        except Exception as e:
            logger.error(f"Failed to start voice control engine: {e}")
            self.shutdown()
            raise
    
    def _start_core_components(self):
        """Start core system components"""
        logger.debug("Starting core components...")
        
        # Start health monitoring if enabled
        if self.config.get("health_monitoring", {}).get("enabled", True):
            interval = self.config.get("health_monitoring", {}).get("check_interval", 30)
            self.health_monitor.start_monitoring(interval)
        
        # Register cleanup handlers
        self.resource_manager.add_cleanup_handler(self._cleanup_components)
        
        # Log resource usage
        self.logging_manager.performance_logger.log_resource_usage(component="engine_start")
        
        logger.debug("Core components started")
    
    def _start_gui_components(self):
        """Start GUI components"""
        if not GUI_AVAILABLE:
            logger.warning("GUI components not available")
            return
        
        logger.debug("Starting GUI components...")
        
        try:
            # Start system tray
            if self.config.get("gui", {}).get("show_tray", True):
                self.system_tray = VoiceControlTray()
                self.resource_manager.register_resource(
                    "system_tray", 
                    self.system_tray, 
                    lambda tray: tray._exit_application()
                )
            
            # Get notification manager
            if self.config.get("gui", {}).get("show_notifications", True):
                tray_icon = self.system_tray.tray_icon if self.system_tray else None
                self.notification_manager = get_notification_manager(tray_icon)
            
            logger.debug("GUI components started")
            
        except Exception as e:
            logger.error(f"Failed to start GUI components: {e}")
            # Continue without GUI
    
    def _start_voice_recognition(self):
        """Start voice recognition components"""
        logger.debug("Starting voice recognition...")
        
        # This is a placeholder for voice recognition initialization
        # In a full implementation, this would:
        # 1. Initialize the speech recognition engine
        # 2. Setup audio input handling
        # 3. Start the recognition loop
        
        try:
            # Placeholder: Initialize speech recognition
            self._initialize_speech_recognition()
            
            # Placeholder: Start recognition loop
            self._start_recognition_loop()
            
            logger.debug("Voice recognition started")
            
        except Exception as e:
            logger.error(f"Failed to start voice recognition: {e}")
            # Continue without voice recognition for now
    
    def _initialize_speech_recognition(self):
        """Initialize speech recognition engine"""
        engine = self.config.get("speech_recognition", {}).get("engine", "whisper")
        
        if engine == "whisper":
            self._initialize_whisper()
        else:
            logger.warning(f"Unknown speech recognition engine: {engine}")
            logger.warning("Currently only placeholder speech recognition is available")
    
    def _initialize_whisper(self):
        """Initialize Whisper speech recognition"""
        try:
            import whisper
            model_size = self.config.get("speech_recognition", {}).get("model_size", "base")
            
            logger.info(f"Loading Whisper model: {model_size}")
            self.speech_recognition = whisper.load_model(model_size)
            
            self.resource_manager.register_resource(
                "whisper_model",
                self.speech_recognition,
                lambda model: None  # Whisper models don't need explicit cleanup
            )
            
            logger.info("Whisper model loaded successfully")
            
        except ImportError:
            logger.warning("Whisper not available, voice recognition disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Whisper: {e}")
    

    
    def _start_recognition_loop(self):
        """Start the voice recognition loop"""
        if not self.speech_recognition:
            logger.warning("No speech recognition engine available")
            return
        
        # Start recognition in a separate thread
        recognition_thread = threading.Thread(
            target=self._recognition_loop,
            daemon=True
        )
        recognition_thread.start()
        
        self.resource_manager.register_resource(
            "recognition_thread",
            recognition_thread,
            lambda thread: None  # Threads clean up automatically
        )
    
    def _recognition_loop(self):
        """Main voice recognition loop"""
        logger.info("Voice recognition loop started")
        
        while self.running and not self.shutdown_requested:
            try:
                # This is a placeholder for the actual recognition loop
                # In a full implementation, this would:
                # 1. Capture audio from microphone
                # 2. Process audio with speech recognition
                # 3. Execute voice commands
                # 4. Handle errors gracefully
                
                time.sleep(1)  # Placeholder delay
                
            except Exception as e:
                logger.error(f"Error in recognition loop: {e}")
                if self.error_handler.handle_error(e, "recognition_loop"):
                    continue
                else:
                    break
        
        logger.info("Voice recognition loop stopped")
    
    def process_voice_command(self, text: str) -> bool:
        """Process a recognized voice command"""
        try:
            logger.info(f"Processing voice command: {text}")
            
            # Log performance metric
            start_time = time.time()
            
            # Process the command
            result = self._execute_voice_command(text)
            
            # Log timing
            duration = time.time() - start_time
            self.logging_manager.log_performance(
                "voice_command_processing",
                duration,
                command=text[:50],  # Truncate for privacy
                success=result
            )
            
            # Show notification
            if self.notification_manager and result:
                self.notification_manager.show_voice_command_feedback(
                    text[:50], "Executed" if result else "Failed"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing voice command: {e}")
            return False
    
    def _execute_voice_command(self, text: str) -> bool:
        """Execute a specific voice command"""
        # This is a placeholder for command execution
        # In a full implementation, this would:
        # 1. Parse the command
        # 2. Determine the action (typing, system command, etc.)
        # 3. Execute the action using appropriate handlers
        
        # For now, just type the text
        return self.input_handler.type_text_at_cursor(text)
    
    def run_daemon(self):
        """Run in daemon mode"""
        logger.info("Running in daemon mode...")
        
        try:
            while self.running and not self.shutdown_requested:
                # Perform periodic tasks
                self._perform_periodic_tasks()
                
                # Sleep for a short interval
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt in daemon mode")
        except Exception as e:
            logger.error(f"Error in daemon mode: {e}")
        finally:
            self.shutdown()
    
    def run_interactive(self):
        """Run in interactive mode with GUI"""
        if not GUI_AVAILABLE or not self.system_tray:
            logger.error("Interactive mode requires GUI components")
            return
        
        logger.info("Running in interactive mode...")
        
        try:
            # Run the GUI event loop
            return self.system_tray.run()
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}")
        finally:
            self.shutdown()
    
    def _perform_periodic_tasks(self):
        """Perform periodic maintenance tasks"""
        # Log resource usage periodically
        self.logging_manager.performance_logger.log_resource_usage(
            component="periodic_check"
        )
        
        # Clean up old logs if configured
        if self.config.get("logging", {}).get("log_retention_days"):
            retention_days = self.config["logging"]["log_retention_days"]
            self.logging_manager.cleanup_old_logs(retention_days)
    
    def _cleanup_components(self):
        """Clean up all components"""
        logger.info("Cleaning up voice control components...")
        
        try:
            # Stop health monitoring
            if self.health_monitor:
                self.health_monitor.stop_monitoring()
            
            # Clean up GUI components
            if self.system_tray:
                self.system_tray._exit_application()
            
            # Additional cleanup can be added here
            
        except Exception as e:
            logger.error(f"Error during component cleanup: {e}")
    
    def shutdown(self):
        """Shutdown the voice control engine"""
        if self.shutdown_requested:
            return
        
        logger.info("Shutting down voice control engine...")
        self.shutdown_requested = True
        self.running = False
        
        try:
            # Create final diagnostic report
            report_path = self.logging_manager.save_diagnostic_report("shutdown_report.json")
            logger.info(f"Shutdown diagnostic report saved to: {report_path}")
            
            # Cleanup all resources
            self.resource_manager.cleanup_all()
            
            logger.info("Voice control engine shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current engine status"""
        return {
            "running": self.running,
            "daemon_mode": self.daemon_mode,
            "components": {
                "resource_manager": self.resource_manager is not None,
                "error_handler": self.error_handler is not None,
                "health_monitor": self.health_monitor is not None,
                "system_tray": self.system_tray is not None,
                "speech_recognition": self.speech_recognition is not None,
                "gui_available": GUI_AVAILABLE
            },
            "health": self.health_monitor.get_health_report() if self.health_monitor else None,
            "resource_stats": self.resource_manager.get_resource_stats() if self.resource_manager else None
        }


def main():
    """Test the voice control engine"""
    logging.basicConfig(level=logging.INFO)
    
    # Create and start engine
    engine = VoiceControlEngine(daemon_mode=False)
    
    try:
        engine.start()
        
        # Test status
        status = engine.get_status()
        print(f"Engine status: {status}")
        
        # Run for a short time
        if GUI_AVAILABLE:
            engine.run_interactive()
        else:
            print("Running in daemon mode for 10 seconds...")
            time.sleep(10)
        
    finally:
        engine.shutdown()


if __name__ == "__main__":
    main()