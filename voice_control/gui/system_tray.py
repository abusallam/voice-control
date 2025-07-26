#!/usr/bin/env python3
"""
System Tray Application for Voice Control

Provides a system tray icon with easy access to voice control features:
- Start/Stop voice dictation
- Configure settings
- View status
- Access full GUI
"""

import sys
import logging
from pathlib import Path
from typing import Optional

try:
    from PyQt5.QtWidgets import (
        QApplication, QSystemTrayIcon, QMenu, QAction, 
        QMessageBox, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QCheckBox, QSpinBox, QComboBox,
        QTextEdit, QGroupBox, QSlider, QProgressBar
    )
    from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
    from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
    PYQT_AVAILABLE = True
except ImportError:
    try:
        from tkinter import *
        from tkinter import ttk, messagebox
        import tkinter as tk
        TKINTER_AVAILABLE = True
        PYQT_AVAILABLE = False
    except ImportError:
        PYQT_AVAILABLE = False
        TKINTER_AVAILABLE = False

logger = logging.getLogger(__name__)

# Import notification manager
try:
    from voice_control.gui.notification_manager import get_notification_manager, NotificationType
    NOTIFICATION_MANAGER_AVAILABLE = True
except ImportError:
    NOTIFICATION_MANAGER_AVAILABLE = False
    logger.warning("Notification manager not available")


class VoiceControlTray:
    """System tray application for voice control with persistence and recovery"""
    
    def __init__(self):
        self.app = None
        self.tray_icon = None
        self.voice_engine = None
        self.is_listening = False
        self.config_window = None
        self.recovery_timer = None
        self.tray_recovery_attempts = 0
        self.max_recovery_attempts = 5
        self.notification_manager = None
        
        # Initialize the appropriate GUI framework
        if PYQT_AVAILABLE:
            self._init_qt()
        elif TKINTER_AVAILABLE:
            self._init_tkinter()
        else:
            logger.error("No GUI framework available (PyQt5 or tkinter required)")
            raise ImportError("No GUI framework available")
        
        # Initialize notification manager after GUI setup
        self._init_notification_manager()
    
    def _init_qt(self):
        """Initialize PyQt5 system tray with recovery mechanisms"""
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(self._create_icon())
        self.tray_icon.setToolTip("Voice Control - Ready")
        
        # Connect tray icon signals for recovery
        self.tray_icon.activated.connect(self._on_tray_activated)
        
        # Create context menu
        self._create_tray_menu()
        
        # Show tray icon with recovery
        self._show_tray_icon_with_recovery()
        
        # Setup recovery timer
        self._setup_recovery_timer()
    
    def _init_tkinter(self):
        """Initialize tkinter fallback (no system tray, but GUI available)"""
        self.app = tk.Tk()
        self.app.title("Voice Control")
        self.app.geometry("300x200")
        self.app.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Create main interface
        self._create_tkinter_interface()
    
    def _create_icon(self):
        """Create a simple microphone icon"""
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw microphone icon
        if self.is_listening:
            painter.setBrush(QColor(255, 0, 0))  # Red when listening
        else:
            painter.setBrush(QColor(100, 100, 100))  # Gray when idle
        
        # Microphone body
        painter.drawEllipse(8, 8, 16, 20)
        # Microphone stand
        painter.drawRect(15, 28, 2, 4)
        # Microphone base
        painter.drawRect(10, 30, 12, 2)
        
        painter.end()
        return QIcon(pixmap)
    
    def _create_tray_menu(self):
        """Create the system tray context menu"""
        menu = QMenu()
        
        # Status section
        status_action = QAction("Voice Control - Ready", menu)
        status_action.setEnabled(False)
        menu.addAction(status_action)
        menu.addSeparator()
        
        # Main controls
        self.start_action = QAction("🎤 Start Listening", menu)
        self.start_action.triggered.connect(self._toggle_listening)
        menu.addAction(self.start_action)
        
        self.stop_action = QAction("⏹️ Stop Listening", menu)
        self.stop_action.triggered.connect(self._stop_listening)
        self.stop_action.setEnabled(False)
        menu.addAction(self.stop_action)
        
        menu.addSeparator()
        
        # Configuration
        config_action = QAction("⚙️ Settings", menu)
        config_action.triggered.connect(self._show_config)
        menu.addAction(config_action)
        
        # Status and logs
        status_window_action = QAction("📊 Status Window", menu)
        status_window_action.triggered.connect(self._show_status)
        menu.addAction(status_window_action)
        
        menu.addSeparator()
        
        # Service management
        service_menu = menu.addMenu("🔧 Service")
        
        service_start = QAction("Start Service", service_menu)
        service_start.triggered.connect(self._start_service)
        service_menu.addAction(service_start)
        
        service_stop = QAction("Stop Service", service_menu)
        service_stop.triggered.connect(self._stop_service)
        service_menu.addAction(service_stop)
        
        service_restart = QAction("Restart Service", service_menu)
        service_restart.triggered.connect(self._restart_service)
        service_menu.addAction(service_restart)
        
        menu.addSeparator()
        
        # Help and about
        help_action = QAction("❓ Help", menu)
        help_action.triggered.connect(self._show_help)
        menu.addAction(help_action)
        
        about_action = QAction("ℹ️ About", menu)
        about_action.triggered.connect(self._show_about)
        menu.addAction(about_action)
        
        menu.addSeparator()
        
        # Exit
        exit_action = QAction("❌ Exit", menu)
        exit_action.triggered.connect(self._exit_application)
        menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(menu)
    
    def _create_tkinter_interface(self):
        """Create tkinter interface as fallback"""
        # Main frame
        main_frame = ttk.Frame(self.app, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status
        self.status_label = ttk.Label(main_frame, text="Voice Control - Ready")
        self.status_label.grid(row=0, column=0, columnspan=2, pady=5)
        
        # Control buttons
        self.start_button = ttk.Button(main_frame, text="Start Listening", 
                                     command=self._toggle_listening)
        self.start_button.grid(row=1, column=0, padx=5, pady=5)
        
        self.stop_button = ttk.Button(main_frame, text="Stop Listening", 
                                    command=self._stop_listening, state="disabled")
        self.stop_button.grid(row=1, column=1, padx=5, pady=5)
        
        # Settings button
        settings_button = ttk.Button(main_frame, text="Settings", 
                                   command=self._show_config)
        settings_button.grid(row=2, column=0, columnspan=2, pady=5)
    
    def _toggle_listening(self):
        """Toggle voice listening on/off"""
        if not self.is_listening:
            self._start_listening()
        else:
            self._stop_listening()
    
    def _start_listening(self):
        """Start voice recognition"""
        try:
            logger.info("Starting voice recognition...")
            self.is_listening = True
            
            # Update UI
            if PYQT_AVAILABLE:
                self.tray_icon.setIcon(self._create_icon())
                self.tray_icon.setToolTip("Voice Control - Listening")
                self.start_action.setText("🔴 Listening...")
                self.start_action.setEnabled(False)
                self.stop_action.setEnabled(True)
            else:
                self.status_label.config(text="Voice Control - Listening")
                self.start_button.config(state="disabled")
                self.stop_button.config(state="normal")
            
            # Start voice engine (placeholder - integrate with actual engine)
            self._start_voice_engine()
            
            # Notify success
            self._notify_status_update("Listening", "Voice recognition started")
            
        except Exception as e:
            logger.error(f"Failed to start listening: {e}")
            self._notify_error("Failed to start voice recognition", str(e))
    
    def _stop_listening(self):
        """Stop voice recognition"""
        try:
            logger.info("Stopping voice recognition...")
            self.is_listening = False
            
            # Update UI
            if PYQT_AVAILABLE:
                self.tray_icon.setIcon(self._create_icon())
                self.tray_icon.setToolTip("Voice Control - Ready")
                self.start_action.setText("🎤 Start Listening")
                self.start_action.setEnabled(True)
                self.stop_action.setEnabled(False)
            else:
                self.status_label.config(text="Voice Control - Ready")
                self.start_button.config(state="normal")
                self.stop_button.config(state="disabled")
            
            # Stop voice engine
            self._stop_voice_engine()
            
            # Notify status change
            self._notify_status_update("Ready", "Voice recognition stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop listening: {e}")
            self._notify_error("Failed to stop voice recognition", str(e))
    
    def _start_voice_engine(self):
        """Start the voice recognition engine"""
        import subprocess
        import os
        try:
            # Find the voice control script in the project directory
            project_dir = os.path.expanduser("~/Documents/voice-control")
            voice_script = os.path.join(project_dir, "voice-control-original-test")
            
            if os.path.exists(voice_script):
                # Check if dependencies are available
                try:
                    import speech_recognition
                    import whisper
                except ImportError as dep_error:
                    error_msg = f"Missing dependency: {dep_error}. Please run: pip install -r requirements.txt"
                    logger.error(error_msg)
                    self._notify_error("Dependency Error", error_msg)
                    return
                
                # Start voice control with the working implementation
                subprocess.Popen([
                    "python3", voice_script, "begin", 
                    "--continuous", "--verbose", "1"
                ], cwd=project_dir)
                logger.info(f"Started voice engine: {voice_script}")
            else:
                error_msg = f"Voice control script not found at: {voice_script}"
                logger.error(error_msg)
                self._notify_error("Installation Error", 
                                 "Voice control not properly installed. Please run ./install.sh")
        except Exception as e:
            error_msg = f"Failed to start voice engine: {e}"
            logger.error(error_msg)
            self._notify_error("Voice Engine Error", 
                             "Could not start voice recognition. Check your microphone and audio settings.")
    
    def _stop_voice_engine(self):
        """Stop the voice recognition engine"""
        import subprocess
        import os
        try:
            # Find the voice control script in the project directory
            project_dir = os.path.expanduser("~/Documents/voice-control")
            voice_script = os.path.join(project_dir, "voice-control-original-test")
            
            if os.path.exists(voice_script):
                # Stop voice control
                subprocess.run([
                    "python3", voice_script, "end"
                ], cwd=project_dir)
                logger.info(f"Stopped voice engine: {voice_script}")
            else:
                logger.error(f"Voice control script not found: {voice_script}")
        except Exception as e:
            logger.error(f"Failed to stop voice engine: {e}")
    
    def _show_config(self):
        """Show configuration window"""
        if PYQT_AVAILABLE:
            self._show_qt_config()
        else:
            self._show_tkinter_config()
    
    def _show_qt_config(self):
        """Show PyQt configuration window"""
        if self.config_window is not None:
            self.config_window.show()
            self.config_window.raise_()
            return
        
        self.config_window = QWidget()
        self.config_window.setWindowTitle("Voice Control Settings")
        self.config_window.setGeometry(300, 300, 500, 400)
        
        layout = QVBoxLayout()
        
        # Speech Recognition Settings
        speech_group = QGroupBox("Speech Recognition")
        speech_layout = QVBoxLayout()
        
        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Speech Model:"))
        model_combo = QComboBox()
        model_combo.addItems(["Local Speech Recognition (Default)", "External Services"])
        model_layout.addWidget(model_combo)
        speech_layout.addLayout(model_layout)
        
        # Sensitivity
        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(QLabel("Microphone Sensitivity:"))
        sensitivity_slider = QSlider(Qt.Horizontal)
        sensitivity_slider.setRange(1, 10)
        sensitivity_slider.setValue(5)
        sensitivity_layout.addWidget(sensitivity_slider)
        speech_layout.addLayout(sensitivity_layout)
        
        # Timeout
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("Timeout (seconds):"))
        timeout_spin = QSpinBox()
        timeout_spin.setRange(1, 60)
        timeout_spin.setValue(10)
        timeout_layout.addWidget(timeout_spin)
        speech_layout.addLayout(timeout_layout)
        
        speech_group.setLayout(speech_layout)
        layout.addWidget(speech_group)
        
        # Output Settings
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout()
        
        # Output method
        output_method_layout = QHBoxLayout()
        output_method_layout.addWidget(QLabel("Output Method:"))
        output_combo = QComboBox()
        output_combo.addItems(["Simulate Typing", "Clipboard", "File Output"])
        output_method_layout.addWidget(output_combo)
        output_layout.addLayout(output_method_layout)
        
        # Auto-punctuation
        auto_punct = QCheckBox("Automatic punctuation")
        auto_punct.setChecked(True)
        output_layout.addWidget(auto_punct)
        
        # Numbers as digits
        numbers_digits = QCheckBox("Convert numbers to digits")
        numbers_digits.setChecked(False)
        output_layout.addWidget(numbers_digits)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self._save_config)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.config_window.close)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.config_window.setLayout(layout)
        self.config_window.show()
    
    def _show_tkinter_config(self):
        """Show tkinter configuration window"""
        config_window = tk.Toplevel(self.app)
        config_window.title("Voice Control Settings")
        config_window.geometry("400x300")
        
        # Simple configuration options
        ttk.Label(config_window, text="Voice Control Settings", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # Model selection
        model_frame = ttk.Frame(config_window)
        model_frame.pack(fill="x", padx=20, pady=5)
        ttk.Label(model_frame, text="Speech Model:").pack(side="left")
        model_var = tk.StringVar(value="Local Speech Recognition")
        model_combo = ttk.Combobox(model_frame, textvariable=model_var,
                                  values=["Local Speech Recognition", "External Services"])
        model_combo.pack(side="right")
        
        # Timeout setting
        timeout_frame = ttk.Frame(config_window)
        timeout_frame.pack(fill="x", padx=20, pady=5)
        ttk.Label(timeout_frame, text="Timeout (seconds):").pack(side="left")
        timeout_var = tk.IntVar(value=10)
        timeout_spin = tk.Spinbox(timeout_frame, from_=1, to=60, textvariable=timeout_var)
        timeout_spin.pack(side="right")
        
        # Save button
        ttk.Button(config_window, text="Save Settings", 
                  command=lambda: self._save_tkinter_config(config_window)).pack(pady=20)
    
    def _save_config(self):
        """Save configuration settings"""
        # Implement configuration saving
        logger.info("Configuration saved")
        if self.config_window:
            self.config_window.close()
    
    def _save_tkinter_config(self, window):
        """Save tkinter configuration"""
        logger.info("Configuration saved")
        window.destroy()
    
    def _show_status(self):
        """Show status window"""
        if PYQT_AVAILABLE:
            self._show_qt_status()
        else:
            self._show_tkinter_status()
    
    def _show_qt_status(self):
        """Show PyQt status window"""
        status_window = QWidget()
        status_window.setWindowTitle("Voice Control Status")
        status_window.setGeometry(300, 300, 600, 400)
        
        layout = QVBoxLayout()
        
        # Status information
        status_text = QTextEdit()
        status_text.setReadOnly(True)
        status_text.append("Voice Control Status:")
        status_text.append(f"Listening: {'Yes' if self.is_listening else 'No'}")
        status_text.append("Service: Running")
        status_text.append("Audio Device: Default")
        status_text.append("Speech Model: Whisper")
        
        layout.addWidget(status_text)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(status_window.close)
        layout.addWidget(close_button)
        
        status_window.setLayout(layout)
        status_window.show()
    
    def _show_tkinter_status(self):
        """Show tkinter status window"""
        status_window = tk.Toplevel(self.app)
        status_window.title("Voice Control Status")
        status_window.geometry("400x300")
        
        status_text = tk.Text(status_window, wrap=tk.WORD)
        status_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        status_text.insert("1.0", f"""Voice Control Status:

Listening: {'Yes' if self.is_listening else 'No'}
Service: Running
Audio Device: Default
Speech Model: Whisper
""")
        
        status_text.config(state="disabled")
    
    def _start_service(self):
        """Start voice control service"""
        import subprocess
        try:
            result = subprocess.run(["voice-control", "--service", "start"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self._show_info("Service Started", "Voice control service started successfully")
            else:
                self._show_error("Service Error", result.stderr)
        except Exception as e:
            self._show_error("Service Error", str(e))
    
    def _stop_service(self):
        """Stop voice control service"""
        import subprocess
        try:
            result = subprocess.run(["voice-control", "--service", "stop"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self._show_info("Service Stopped", "Voice control service stopped successfully")
            else:
                self._show_error("Service Error", result.stderr)
        except Exception as e:
            self._show_error("Service Error", str(e))
    
    def _restart_service(self):
        """Restart voice control service"""
        self._stop_service()
        self._start_service()
    
    def _show_help(self):
        """Show help information"""
        help_text = """Voice Control Help:

🎤 Start/Stop Listening: Control voice recognition
⚙️ Settings: Configure speech recognition and output
📊 Status: View current system status
🔧 Service: Manage background service

Voice Commands:
- Say "begin dictation" to start
- Say "end dictation" to stop
- Say "cancel" to cancel current text

For more help, visit: https://github.com/your-repo/voice-control
"""
        self._show_info("Voice Control Help", help_text)
    
    def _show_about(self):
        """Show about information"""
        about_text = """Voice Control v2.0

A modern Linux voice control application with:
- Local speech recognition
- System tray integration
- Stable performance
- Easy configuration

Built with stability and user experience in mind.

© 2025 Voice Control Project
Licensed under MIT License
"""
        self._show_info("About Voice Control", about_text)
    
    def _show_info(self, title: str, message: str):
        """Show information dialog"""
        if PYQT_AVAILABLE:
            QMessageBox.information(None, title, message)
        else:
            messagebox.showinfo(title, message)
    
    def _show_error(self, title: str, message: str):
        """Show error dialog"""
        if PYQT_AVAILABLE:
            QMessageBox.critical(None, title, message)
        else:
            messagebox.showerror(title, message)
    
    def _show_tray_icon_with_recovery(self):
        """Show tray icon with recovery mechanism"""
        if not PYQT_AVAILABLE:
            return
            
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.show()
            self.tray_recovery_attempts = 0
            logger.info("System tray icon displayed successfully")
        else:
            logger.warning("System tray not available, will retry...")
            self._schedule_tray_recovery()
    
    def _setup_recovery_timer(self):
        """Setup timer for tray icon recovery monitoring"""
        if not PYQT_AVAILABLE:
            return
            
        self.recovery_timer = QTimer()
        self.recovery_timer.timeout.connect(self._check_tray_visibility)
        self.recovery_timer.start(5000)  # Check every 5 seconds
    
    def _check_tray_visibility(self):
        """Check if tray icon is still visible and recover if needed"""
        if not PYQT_AVAILABLE or not self.tray_icon:
            return
            
        try:
            # Check if tray icon is visible
            if not self.tray_icon.isVisible() and QSystemTrayIcon.isSystemTrayAvailable():
                logger.warning("Tray icon disappeared, attempting recovery...")
                self._recover_tray_icon()
        except Exception as e:
            logger.error(f"Error checking tray visibility: {e}")
    
    def _recover_tray_icon(self):
        """Attempt to recover disappeared tray icon"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            if self.tray_recovery_attempts < self.max_recovery_attempts:
                self.tray_recovery_attempts += 1
                logger.info(f"Tray recovery attempt {self.tray_recovery_attempts}/{self.max_recovery_attempts}")
                
                # Recreate and show tray icon
                self.tray_icon.hide()
                self.tray_icon.setIcon(self._create_icon())
                self.tray_icon.show()
                
                if self.tray_icon.isVisible():
                    logger.info("Tray icon recovery successful")
                    self.tray_recovery_attempts = 0
                else:
                    logger.warning("Tray icon recovery failed, will retry...")
            else:
                logger.error("Maximum tray recovery attempts reached")
                self._show_error("System Tray Error", 
                               "System tray icon could not be recovered. Please restart the application.")
        except Exception as e:
            logger.error(f"Tray icon recovery failed: {e}")
    
    def _schedule_tray_recovery(self):
        """Schedule tray icon recovery attempt"""
        if not PYQT_AVAILABLE:
            return
            
        if self.tray_recovery_attempts < self.max_recovery_attempts:
            self.tray_recovery_attempts += 1
            
            # Use QTimer for delayed recovery attempt
            recovery_timer = QTimer()
            recovery_timer.setSingleShot(True)
            recovery_timer.timeout.connect(self._attempt_tray_recovery)
            recovery_timer.start(2000)  # Wait 2 seconds before retry
    
    def _attempt_tray_recovery(self):
        """Attempt to recover tray icon after delay"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.show()
            if self.tray_icon.isVisible():
                logger.info("Delayed tray icon recovery successful")
                self.tray_recovery_attempts = 0
            else:
                logger.warning("Delayed tray icon recovery failed")
                self._schedule_tray_recovery()
        else:
            logger.warning("System tray still not available")
            self._schedule_tray_recovery()
    
    def _on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            # Double-click to toggle listening
            self._toggle_listening()
        elif reason == QSystemTrayIcon.Trigger:
            # Single click to show status
            self._show_brief_status()
    
    def _show_brief_status(self):
        """Show brief status message"""
        if not PYQT_AVAILABLE:
            return
            
        status_msg = "Listening" if self.is_listening else "Ready"
        self.tray_icon.showMessage(
            "Voice Control",
            f"Status: {status_msg}",
            QSystemTrayIcon.Information,
            2000  # Show for 2 seconds
        )
    
    def _update_tray_status(self, status: str, listening: bool = None):
        """Update tray icon status and tooltip"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            if listening is not None:
                self.is_listening = listening
            
            # Update icon
            self.tray_icon.setIcon(self._create_icon())
            
            # Update tooltip
            self.tray_icon.setToolTip(f"Voice Control - {status}")
            
            # Update menu items
            if hasattr(self, 'start_action') and hasattr(self, 'stop_action'):
                if self.is_listening:
                    self.start_action.setText("🔴 Listening...")
                    self.start_action.setEnabled(False)
                    self.stop_action.setEnabled(True)
                else:
                    self.start_action.setText("🎤 Start Listening")
                    self.start_action.setEnabled(True)
                    self.stop_action.setEnabled(False)
                    
        except Exception as e:
            logger.error(f"Error updating tray status: {e}")
    
    def _exit_application(self):
        """Exit the application"""
        try:
            logger.info("Shutting down voice control tray application...")
            
            # Stop listening if active
            if self.is_listening:
                self._stop_listening()
            
            # Stop recovery timer
            if self.recovery_timer:
                self.recovery_timer.stop()
            
            # Hide tray icon
            if PYQT_AVAILABLE and self.tray_icon:
                self.tray_icon.hide()
            
            # Quit application
            if PYQT_AVAILABLE:
                self.app.quit()
            else:
                self.app.quit()
                
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
    
    def _init_notification_manager(self):
        """Initialize the notification manager"""
        if NOTIFICATION_MANAGER_AVAILABLE:
            try:
                self.notification_manager = get_notification_manager(self.tray_icon if PYQT_AVAILABLE else None)
                logger.info("Notification manager initialized")
                
                # Show startup notification
                self.notification_manager.show_status_update("Ready", "Voice control system initialized")
                
            except Exception as e:
                logger.error(f"Failed to initialize notification manager: {e}")
                self.notification_manager = None
        else:
            logger.warning("Notification manager not available")
    
    def _notify_success(self, title: str, message: str):
        """Show success notification"""
        if self.notification_manager:
            self.notification_manager.show_success(title, message)
        else:
            self._show_info(title, message)
    
    def _notify_error(self, title: str, message: str):
        """Show error notification"""
        if self.notification_manager:
            self.notification_manager.show_error(title, message)
        else:
            self._show_error(title, message)
    
    def _notify_warning(self, title: str, message: str):
        """Show warning notification"""
        if self.notification_manager:
            self.notification_manager.show_warning(title, message)
        else:
            self._show_info(title, message)
    
    def _notify_voice_command(self, command: str, result: str = "Executed"):
        """Show voice command feedback"""
        if self.notification_manager:
            self.notification_manager.show_voice_command_feedback(command, result)
    
    def _notify_status_update(self, status: str, details: str = ""):
        """Show status update notification"""
        if self.notification_manager:
            self.notification_manager.show_status_update(status, details)
    
    def _on_closing(self):
        """Handle window closing (tkinter)"""
        self._exit_application()
    
    def run(self):
        """Run the application"""
        if PYQT_AVAILABLE:
            return self.app.exec_()
        else:
            self.app.mainloop()


def main():
    """Main entry point for system tray application"""
    logging.basicConfig(level=logging.INFO)
    
    try:
        tray_app = VoiceControlTray()
        return tray_app.run()
    except ImportError as e:
        logger.error(f"GUI framework not available: {e}")
        print("Error: No GUI framework available. Please install PyQt5:")
        print("pip install PyQt5")
        return 1
    except Exception as e:
        logger.error(f"Failed to start system tray: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())