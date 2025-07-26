#!/usr/bin/env python3
"""
Error Handler for Voice Control Application

Provides comprehensive error handling, recovery mechanisms, and graceful degradation
to prevent system hangs and crashes.
"""

import logging
import traceback
import functools
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union
from enum import Enum
import threading

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


class ErrorHandler:
    """Comprehensive error handling and recovery system"""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.last_errors: Dict[str, float] = {}
        self.recovery_handlers: Dict[Type[Exception], Callable] = {}
        self.fallback_handlers: Dict[str, Callable] = {}
        self.max_retries = 3
        self.retry_delay = 1.0
        self.error_threshold = 5
        self.time_window = 300  # 5 minutes
        self._lock = threading.Lock()
        
        # Register default recovery handlers
        self._register_default_handlers()
    
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
        return self._attempt_recovery(error, context)
    
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
    
    def reset_error_counts(self):
        """Reset error tracking"""
        with self._lock:
            self.error_counts.clear()
            self.last_errors.clear()
        logger.info("Error counts reset")


def safe_execute(error_handler: ErrorHandler, context: str = ""):
    """Decorator for safe execution with error handling"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if error_handler.handle_error(e, context or func.__name__):
                    # If error was handled successfully, return None or default value
                    return None
                else:
                    # If error handling failed, re-raise
                    raise
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
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler