#!/usr/bin/env python3
"""
Production Error Handler for Voice Control Application

Provides comprehensive error handling, recovery mechanisms, and graceful degradation
to prevent system hangs and crashes. Enhanced for Debian 12 production readiness.
"""

import logging
import traceback
import functools
import time
import sys
import os
import json
import signal
import psutil
from typing import Any, Callable, Dict, List, Optional, Type, Union, Tuple
from enum import Enum
from pathlib import Path
import threading
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryAction(Enum):
    """Recovery actions for different error types"""
    RETRY = "retry"
    FALLBACK = "fallback"
    RESTART_COMPONENT = "restart_component"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    SHUTDOWN = "shutdown"


class VoiceControlError(Exception):
    """Base exception for voice control application"""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                 recovery_action: RecoveryAction = RecoveryAction.RETRY):
        super().__init__(message)
        self.severity = severity
        self.recovery_action = recovery_action
        self.timestamp = time.time()


class AudioError(VoiceControlError):
    """Audio-related errors"""
    pass


class RecognitionError(VoiceControlError):
    """Speech recognition errors"""
    pass


class SystemError(VoiceControlError):
    """System integration errors"""
    pass


class ConfigurationError(VoiceControlError):
    """Configuration-related errors"""
    pass


class SystemMonitor:
    """Monitor system resources and health"""
    
    def __init__(self):
        try:
            self.process = psutil.Process()
        except Exception:
            self.process = None
        self.memory_threshold = 500 * 1024 * 1024  # 500MB
        self.cpu_threshold = 80.0  # 80%
        
    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        try:
            if not self.process:
                return {}
                
            return {
                'memory_usage': self.process.memory_info().rss,
                'memory_percent': self.process.memory_percent(),
                'cpu_percent': self.process.cpu_percent(),
                'num_threads': self.process.num_threads(),
                'open_files': len(self.process.open_files()),
                'connections': len(self.process.connections()),
                'system_memory': psutil.virtual_memory()._asdict(),
                'system_cpu': psutil.cpu_percent(interval=1),
                'disk_usage': psutil.disk_usage('/')._asdict()
            }
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {}
    
    def check_resource_limits(self) -> List[str]:
        """Check if resource limits are exceeded"""
        warnings = []
        
        try:
            if not self.process:
                return warnings
                
            # Check memory usage
            memory_usage = self.process.memory_info().rss
            if memory_usage > self.memory_threshold:
                warnings.append(f"High memory usage: {memory_usage / 1024 / 1024:.1f}MB")
            
            # Check CPU usage
            cpu_percent = self.process.cpu_percent()
            if cpu_percent > self.cpu_threshold:
                warnings.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            # Check system memory
            system_memory = psutil.virtual_memory()
            if system_memory.percent > 90:
                warnings.append(f"System memory critical: {system_memory.percent:.1f}%")
            
            # Check disk space
            disk_usage = psutil.disk_usage('/')
            if disk_usage.percent > 95:
                warnings.append(f"Disk space critical: {disk_usage.percent:.1f}%")
                
        except Exception as e:
            warnings.append(f"Resource monitoring error: {e}")
        
        return warnings


class CrashDetector:
    """Detect and handle application crashes"""
    
    def __init__(self):
        self.crash_indicators = []
        self.last_crash_time = None
        
    def collect_crash_info(self, signum: int, frame) -> Dict[str, Any]:
        """Collect detailed crash information"""
        crash_info = {
            'timestamp': datetime.now().isoformat(),
            'signal': signum,
            'signal_name': signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else f"Signal-{signum}",
            'process_info': self._get_process_info(),
            'system_info': self._get_system_info(),
            'stack_trace': self._get_stack_trace(frame),
            'environment': dict(os.environ),
            'python_info': {
                'version': sys.version,
                'executable': sys.executable,
                'path': sys.path[:10]  # Limit path length
            }
        }
        
        return crash_info
    
    def _get_process_info(self) -> Dict[str, Any]:
        """Get current process information"""
        try:
            process = psutil.Process()
            return {
                'pid': process.pid,
                'ppid': process.ppid(),
                'name': process.name(),
                'cmdline': process.cmdline(),
                'memory_info': process.memory_info()._asdict(),
                'cpu_times': process.cpu_times()._asdict(),
                'num_threads': process.num_threads(),
                'open_files': [f.path for f in process.open_files()],
                'connections': len(process.connections())
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        try:
            return {
                'platform': sys.platform,
                'architecture': os.uname()._asdict() if hasattr(os, 'uname') else {},
                'memory': psutil.virtual_memory()._asdict(),
                'cpu_count': psutil.cpu_count(),
                'boot_time': psutil.boot_time(),
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_stack_trace(self, frame) -> List[str]:
        """Get stack trace from frame"""
        try:
            stack_trace = []
            current_frame = frame
            
            while current_frame and len(stack_trace) < 20:  # Limit stack depth
                filename = current_frame.f_code.co_filename
                line_number = current_frame.f_lineno
                function_name = current_frame.f_code.co_name
                
                stack_trace.append(f"{filename}:{line_number} in {function_name}")
                current_frame = current_frame.f_back
            
            return stack_trace
        except Exception as e:
            return [f"Stack trace error: {e}"]


class ProductionErrorHandler:
    """Production-ready comprehensive error handling and recovery system"""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.last_errors: Dict[str, float] = {}
        self.recovery_handlers: Dict[Type[Exception], Callable] = {}
        self.fallback_handlers: Dict[str, Callable] = {}
        self.component_states: Dict[str, str] = {}  # Track component health
        self.error_history: List[Dict[str, Any]] = []  # Detailed error history
        
        # Configuration
        self.max_retries = 3
        self.retry_delay = 1.0
        self.error_threshold = 5
        self.time_window = 300  # 5 minutes
        self.max_error_history = 1000
        
        # Threading
        self._lock = threading.Lock()
        self._shutdown_event = threading.Event()
        
        # System monitoring
        self.system_monitor = SystemMonitor()
        self.crash_detector = CrashDetector()
        
        # Error logging
        self.error_log_dir = Path.home() / ".local/share/voice-control/logs/errors"
        self.error_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self._setup_error_logging()
        self._register_default_handlers()
        self._setup_signal_handlers()
        
        logger.info("Production error handler initialized")
    
    def _setup_error_logging(self):
        """Setup detailed error logging"""
        try:
            # Create error-specific logger
            self.error_logger = logging.getLogger("voice_control.errors")
            
            # Create file handler for errors
            error_log_file = self.error_log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(error_log_file)
            file_handler.setLevel(logging.ERROR)
            
            # Create detailed formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            self.error_logger.addHandler(file_handler)
            self.error_logger.setLevel(logging.ERROR)
            
        except Exception as e:
            logger.warning(f"Failed to setup error logging: {e}")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for crash detection"""
        def signal_handler(signum, frame):
            self._handle_system_signal(signum, frame)
        
        # Handle critical signals
        for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGABRT]:
            try:
                signal.signal(sig, signal_handler)
            except (OSError, ValueError):
                # Some signals may not be available on all systems
                pass
    
    def _handle_system_signal(self, signum, frame):
        """Handle system signals that indicate crashes or shutdowns"""
        signal_name = signal.Signals(signum).name if signum in signal.Signals._value2member_map_ else f"Signal-{signum}"
        logger.critical(f"Received signal {signal_name} ({signum})")
        
        # Log crash information
        crash_info = self.crash_detector.collect_crash_info(signum, frame)
        self._log_crash_info(crash_info)
        
        # Attempt graceful shutdown
        self._emergency_shutdown()
    
    def _log_crash_info(self, crash_info: Dict[str, Any]):
        """Log detailed crash information"""
        try:
            crash_log_file = self.error_log_dir / f"crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(crash_log_file, 'w') as f:
                json.dump(crash_info, f, indent=2, default=str)
            
            logger.critical(f"Crash information saved to {crash_log_file}")
            
        except Exception as e:
            logger.error(f"Failed to save crash information: {e}")
    
    def _emergency_shutdown(self):
        """Emergency shutdown procedure"""
        logger.critical("Initiating emergency shutdown")
        
        try:
            # Set shutdown event
            self._shutdown_event.set()
            
            # Cleanup critical resources
            self._emergency_cleanup()
            
            # Exit gracefully
            sys.exit(1)
            
        except Exception as e:
            logger.critical(f"Emergency shutdown failed: {e}")
            os._exit(1)  # Force exit
    
    def _emergency_cleanup(self):
        """Emergency cleanup of critical resources"""
        try:
            # Cleanup audio resources
            self._cleanup_audio_resources()
            
            # Cleanup GUI resources
            self._cleanup_gui_resources()
            
            # Save error state
            self._save_error_state()
            
        except Exception as e:
            logger.error(f"Emergency cleanup failed: {e}")
    
    def _cleanup_audio_resources(self):
        """Emergency cleanup of audio resources"""
        try:
            # Try to release audio devices
            import subprocess
            subprocess.run(['pkill', '-f', 'voice-control'], timeout=5)
        except Exception:
            pass
    
    def _cleanup_gui_resources(self):
        """Emergency cleanup of GUI resources"""
        try:
            # Try to cleanup GUI resources
            if hasattr(self, 'system_tray') and self.system_tray:
                self.system_tray._exit_application()
        except Exception:
            pass
    
    def _save_error_state(self):
        """Save current error state for recovery"""
        try:
            state_file = self.error_log_dir / "last_error_state.json"
            state = {
                'timestamp': datetime.now().isoformat(),
                'error_counts': self.error_counts,
                'component_states': self.component_states,
                'recent_errors': self.error_history[-10:] if self.error_history else []
            }
            
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save error state: {e}")
    
    def _register_default_handlers(self):
        """Register default error recovery handlers"""
        self.register_recovery_handler(AudioError, self._handle_audio_error)
        self.register_recovery_handler(RecognitionError, self._handle_recognition_error)
        self.register_recovery_handler(SystemError, self._handle_system_error)
        self.register_recovery_handler(ConfigurationError, self._handle_config_error)
    
    def register_recovery_handler(self, error_type: Type[Exception], handler: Callable):
        """Register a recovery handler for a specific error type"""
        self.recovery_handlers[error_type] = handler
        logger.debug(f"Registered recovery handler for {error_type.__name__}")
    
    def register_fallback_handler(self, component: str, handler: Callable):
        """Register a fallback handler for a component"""
        self.fallback_handlers[component] = handler
        logger.debug(f"Registered fallback handler for {component}")
    
    def handle_error(self, error: Exception, context: str = "") -> bool:
        """Handle an error with appropriate recovery action"""
        error_key = f"{type(error).__name__}:{context}"
        
        with self._lock:
            # Track error frequency
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
            self.last_errors[error_key] = time.time()
            
            # Check if we're hitting too many errors
            if self._is_error_threshold_exceeded(error_key):
                logger.critical(f"Error threshold exceeded for {error_key}")
                return self._handle_critical_error(error, context)
        
        # Log the error
        self._log_error(error, context)
        
        # Try to recover
        recovery_success = self._attempt_recovery(error, context)
        
        # Add to error history
        self.add_error_to_history(error, context, recovery_success)
        
        return recovery_success
    
    def _is_error_threshold_exceeded(self, error_key: str) -> bool:
        """Check if error threshold is exceeded"""
        count = self.error_counts.get(error_key, 0)
        last_time = self.last_errors.get(error_key, 0)
        current_time = time.time()
        
        # Reset count if outside time window
        if current_time - last_time > self.time_window:
            self.error_counts[error_key] = 1
            return False
        
        return count >= self.error_threshold
    
    def _log_error(self, error: Exception, context: str):
        """Log error with appropriate level"""
        severity = getattr(error, 'severity', ErrorSeverity.MEDIUM)
        
        error_msg = f"Error in {context}: {str(error)}"
        
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(error_msg, exc_info=True)
        elif severity == ErrorSeverity.HIGH:
            logger.error(error_msg, exc_info=True)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(error_msg)
        else:
            logger.info(error_msg)
    
    def _attempt_recovery(self, error: Exception, context: str) -> bool:
        """Attempt to recover from an error"""
        error_type = type(error)
        
        # Try specific recovery handler
        if error_type in self.recovery_handlers:
            try:
                return self.recovery_handlers[error_type](error, context)
            except Exception as recovery_error:
                logger.error(f"Recovery handler failed: {recovery_error}")
        
        # Try generic recovery based on error attributes
        if hasattr(error, 'recovery_action'):
            return self._execute_recovery_action(error.recovery_action, error, context)
        
        # Default recovery
        logger.warning(f"No specific recovery handler for {error_type.__name__}, using default")
        return self._default_recovery(error, context)
    
    def _execute_recovery_action(self, action: RecoveryAction, error: Exception, context: str) -> bool:
        """Execute a specific recovery action"""
        try:
            if action == RecoveryAction.RETRY:
                return self._retry_operation(error, context)
            elif action == RecoveryAction.FALLBACK:
                return self._use_fallback(context)
            elif action == RecoveryAction.RESTART_COMPONENT:
                return self._restart_component(context)
            elif action == RecoveryAction.GRACEFUL_DEGRADATION:
                return self._graceful_degradation(context)
            elif action == RecoveryAction.SHUTDOWN:
                return self._graceful_shutdown(error, context)
            else:
                logger.warning(f"Unknown recovery action: {action}")
                return False
        except Exception as e:
            logger.error(f"Recovery action {action} failed: {e}")
            return False
    
    def _handle_audio_error(self, error: AudioError, context: str) -> bool:
        """Handle audio-related errors"""
        logger.info(f"Handling audio error: {error}")
        
        # Try to reinitialize audio system
        try:
            if hasattr(self, 'audio_manager'):
                self.audio_manager.reinitialize()
                return True
        except Exception as e:
            logger.error(f"Failed to reinitialize audio: {e}")
        
        # Use fallback audio handling
        return self._use_fallback("audio")
    
    def _handle_recognition_error(self, error: RecognitionError, context: str) -> bool:
        """Handle speech recognition errors"""
        logger.info(f"Handling recognition error: {error}")
        
        # Try fallback recognition engine
        return self._use_fallback("recognition")
    
    def _handle_system_error(self, error: SystemError, context: str) -> bool:
        """Handle system integration errors"""
        logger.info(f"Handling system error: {error}")
        
        # Try to recover system integration
        if "input" in context.lower():
            return self._use_fallback("input")
        elif "tray" in context.lower():
            return self._use_fallback("tray")
        
        return self._graceful_degradation(context)
    
    def _handle_config_error(self, error: ConfigurationError, context: str) -> bool:
        """Handle configuration errors"""
        logger.info(f"Handling configuration error: {error}")
        
        # Try to reset to default configuration
        try:
            if hasattr(self, 'config_manager'):
                self.config_manager.reset_to_defaults()
                return True
        except Exception as e:
            logger.error(f"Failed to reset configuration: {e}")
        
        return False
    
    def _handle_critical_error(self, error: Exception, context: str) -> bool:
        """Handle critical errors that exceed threshold"""
        logger.critical(f"Critical error situation in {context}: {error}")
        
        # Try graceful degradation first
        if self._graceful_degradation(context):
            return True
        
        # If that fails, initiate graceful shutdown
        return self._graceful_shutdown(error, context)
    
    def _retry_operation(self, error: Exception, context: str) -> bool:
        """Retry the failed operation"""
        # This would need to be implemented by the calling code
        # For now, just return False to indicate retry should be handled externally
        logger.info(f"Retry requested for {context}")
        return False
    
    def _use_fallback(self, component: str) -> bool:
        """Use fallback handler for a component"""
        if component in self.fallback_handlers:
            try:
                self.fallback_handlers[component]()
                logger.info(f"Successfully used fallback for {component}")
                return True
            except Exception as e:
                logger.error(f"Fallback handler for {component} failed: {e}")
        else:
            logger.warning(f"No fallback handler registered for {component}")
        
        return False
    
    def _restart_component(self, context: str) -> bool:
        """Restart a specific component"""
        logger.info(f"Restarting component: {context}")
        # This would need to be implemented by specific components
        return False
    
    def _graceful_degradation(self, context: str) -> bool:
        """Gracefully degrade functionality"""
        logger.info(f"Gracefully degrading functionality for {context}")
        
        # Disable non-essential features
        if hasattr(self, 'feature_manager'):
            self.feature_manager.disable_non_essential()
        
        return True
    
    def _graceful_shutdown(self, error: Exception, context: str) -> bool:
        """Initiate graceful shutdown"""
        logger.critical(f"Initiating graceful shutdown due to {context}: {error}")
        
        # Cleanup resources
        if hasattr(self, 'resource_manager'):
            self.resource_manager.cleanup_all()
        
        # This should trigger application shutdown
        return False
    
    def _default_recovery(self, error: Exception, context: str) -> bool:
        """Default recovery mechanism"""
        logger.info(f"Using default recovery for {context}")
        
        # Try graceful degradation as default
        return self._graceful_degradation(context)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        with self._lock:
            return {
                'error_counts': dict(self.error_counts),
                'recent_errors': {
                    k: v for k, v in self.last_errors.items()
                    if time.time() - v < self.time_window
                },
                'total_errors': sum(self.error_counts.values()),
                'error_types': len(self.error_counts)
            }
    
    def add_error_to_history(self, error: Exception, context: str, recovery_success: bool):
        """Add error to detailed history"""
        with self._lock:
            error_record = {
                'timestamp': datetime.now().isoformat(),
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context,
                'severity': getattr(error, 'severity', ErrorSeverity.MEDIUM).value,
                'recovery_action': getattr(error, 'recovery_action', RecoveryAction.RETRY).value,
                'recovery_success': recovery_success,
                'stack_trace': traceback.format_exc(),
                'system_stats': self.system_monitor.get_system_stats(),
                'resource_warnings': self.system_monitor.check_resource_limits()
            }
            
            self.error_history.append(error_record)
            
            # Limit history size
            if len(self.error_history) > self.max_error_history:
                self.error_history = self.error_history[-self.max_error_history:]
            
            # Log to error logger
            if hasattr(self, 'error_logger'):
                self.error_logger.error(json.dumps(error_record, indent=2, default=str))
    
    def get_component_health(self) -> Dict[str, str]:
        """Get health status of all components"""
        with self._lock:
            return dict(self.component_states)
    
    def set_component_state(self, component: str, state: str):
        """Set the health state of a component"""
        with self._lock:
            self.component_states[component] = state
            logger.debug(f"Component {component} state set to {state}")
    
    def get_detailed_error_report(self) -> Dict[str, Any]:
        """Get comprehensive error report for diagnostics"""
        with self._lock:
            recent_errors = [
                error for error in self.error_history
                if datetime.fromisoformat(error['timestamp']) > datetime.now() - timedelta(hours=24)
            ]
            
            return {
                'timestamp': datetime.now().isoformat(),
                'error_statistics': self.get_error_statistics(),
                'component_health': self.get_component_health(),
                'recent_errors': recent_errors[-50:],  # Last 50 errors
                'system_stats': self.system_monitor.get_system_stats(),
                'resource_warnings': self.system_monitor.check_resource_limits(),
                'configuration': {
                    'max_retries': self.max_retries,
                    'error_threshold': self.error_threshold,
                    'time_window': self.time_window
                }
            }
    
    def save_error_report(self, filename: Optional[str] = None) -> str:
        """Save detailed error report to file"""
        if filename is None:
            filename = f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_path = self.error_log_dir / filename
        
        try:
            report = self.get_detailed_error_report()
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Error report saved to {report_path}")
            return str(report_path)
            
        except Exception as e:
            logger.error(f"Failed to save error report: {e}")
            return ""
    
    def cleanup_old_error_logs(self, days: int = 30):
        """Clean up old error logs"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for log_file in self.error_log_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    logger.debug(f"Removed old error log: {log_file}")
            
            for json_file in self.error_log_dir.glob("*.json"):
                if json_file.stat().st_mtime < cutoff_date.timestamp():
                    json_file.unlink()
                    logger.debug(f"Removed old error report: {json_file}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup old error logs: {e}")
    
    def reset_error_counts(self):
        """Reset error tracking"""
        with self._lock:
            self.error_counts.clear()
            self.last_errors.clear()
        logger.info("Error counts reset")
    
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested"""
        return self._shutdown_event.is_set()


# Enhanced decorators for production error handling
def production_safe_execute(context: str = "", fallback_value: Any = None, 
                          log_errors: bool = True, raise_on_failure: bool = False):
    """Enhanced decorator for production-safe execution with comprehensive error handling"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = get_error_handler()
            
            try:
                result = func(*args, **kwargs)
                
                # Mark component as healthy if it was previously unhealthy
                component_context = context or func.__name__
                if error_handler.component_states.get(component_context) == "unhealthy":
                    error_handler.set_component_state(component_context, "healthy")
                
                return result
                
            except Exception as e:
                # Mark component as unhealthy
                component_context = context or func.__name__
                error_handler.set_component_state(component_context, "unhealthy")
                
                # Handle the error
                recovery_success = error_handler.handle_error(e, component_context)
                
                # Add to error history
                error_handler.add_error_to_history(e, component_context, recovery_success)
                
                if log_errors:
                    logger.error(f"Error in {component_context}: {e}", exc_info=True)
                
                if recovery_success:
                    return fallback_value
                elif raise_on_failure:
                    raise
                else:
                    return fallback_value
                    
        return wrapper
    return decorator


def critical_operation(context: str = "", max_retries: int = 3, 
                      retry_delay: float = 1.0):
    """Decorator for critical operations that must succeed or fail gracefully"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = get_error_handler()
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    # Mark as successful
                    component_context = context or func.__name__
                    error_handler.set_component_state(component_context, "healthy")
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    component_context = context or func.__name__
                    
                    if attempt < max_retries:
                        logger.warning(f"Critical operation {component_context} failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                        
                        # Handle error and check if we should retry
                        recovery_success = error_handler.handle_error(e, component_context)
                        error_handler.add_error_to_history(e, component_context, recovery_success)
                        
                        # Wait before retry with exponential backoff
                        time.sleep(retry_delay * (2 ** attempt))
                    else:
                        # Final attempt failed
                        logger.critical(f"Critical operation {component_context} failed after all retries: {e}")
                        error_handler.set_component_state(component_context, "critical")
                        error_handler.handle_error(e, component_context)
                        error_handler.add_error_to_history(e, component_context, False)
            
            # All retries exhausted
            raise last_exception
            
        return wrapper
    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, 
                    exceptions: tuple = (Exception,)):
    """Decorator for retrying operations on failure"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
            
            raise last_exception
        return wrapper
    return decorator


# Global error handler instance
_global_error_handler: Optional[ProductionErrorHandler] = None


def get_error_handler() -> ProductionErrorHandler:
    """Get the global production error handler instance"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ProductionErrorHandler()
    return _global_error_handler


def initialize_error_handling():
    """Initialize the production error handling system"""
    error_handler = get_error_handler()
    logger.info("Production error handling system initialized")
    return error_handler


# Compatibility alias for existing code
ErrorHandler = ProductionErrorHandler
safe_execute = production_safe_execute