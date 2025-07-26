#!/usr/bin/env python3
"""
Speech Recognition Router

Manages multiple speech recognition backends with automatic fallback
and performance monitoring.
"""

import logging
import time
from typing import Dict, List, Optional, Any
import numpy as np

from .base_backend import SpeechBackend
from ..core.error_handler import get_error_handler, RecognitionError

logger = logging.getLogger(__name__)


class SpeechRecognitionRouter:
    """Routes speech recognition requests to available backends with fallback"""
    
    def __init__(self):
        self.backends: Dict[str, SpeechBackend] = {}
        self.primary_backend: Optional[str] = None
        self.fallback_backends: List[str] = []
        self.current_backend: Optional[str] = None
        self.error_handler = get_error_handler()
        
        # Performance tracking
        self.recognition_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'backend_usage': {},
            'average_response_time': 0.0,
            'error_count': 0
        }
        
        # Register available backends
        self._register_backends()
    
    def _register_backends(self):
        """Register available speech recognition backends"""
        # Register working speech recognition backends
        # Currently no backends are registered - this needs to be implemented
        # with proven speech recognition libraries like Whisper or SpeechRecognition
        
        if len(self.backends) == 0:
            logger.warning("No speech recognition backends available")
            logger.warning("Speech recognition functionality is not yet implemented")
        else:
            logger.info(f"Registered {len(self.backends)} speech recognition backend(s)")
    
    def register_backend(self, name: str, backend: SpeechBackend, 
                        is_primary: bool = False, is_fallback: bool = False):
        """Register a speech recognition backend"""
        self.backends[name] = backend
        
        if is_primary:
            self.primary_backend = name
            logger.info(f"Registered {name} as primary backend")
        
        if is_fallback:
            self.fallback_backends.append(name)
            logger.info(f"Registered {name} as fallback backend")
        
        # Initialize stats tracking
        self.recognition_stats['backend_usage'][name] = {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'avg_response_time': 0.0
        }
    
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """Initialize speech recognition with fallback handling"""
        logger.info("Initializing speech recognition router...")
        
        config = config or {}
        
        # Currently no backends are available
        if len(self.backends) == 0:
            logger.error("No speech recognition backends available")
            logger.error("Speech recognition needs to be implemented with proven libraries")
            return False
        
        initialized_backends = []
        
        # Try to initialize primary backend first
        if self.primary_backend and self._initialize_backend(self.primary_backend, config):
            self.current_backend = self.primary_backend
            initialized_backends.append(self.primary_backend)
            logger.info(f"Primary backend {self.primary_backend} initialized successfully")
        
        # Initialize fallback backends
        for backend_name in self.fallback_backends:
            if self._initialize_backend(backend_name, config):
                initialized_backends.append(backend_name)
                if not self.current_backend:
                    self.current_backend = backend_name
                    logger.info(f"Using {backend_name} as current backend")
        
        if not initialized_backends:
            logger.error("No speech recognition backends could be initialized")
            return False
        
        logger.info(f"Speech recognition router initialized with {len(initialized_backends)} backends")
        return True
    
    def _initialize_backend(self, name: str, config: Dict[str, Any]) -> bool:
        """Initialize a specific backend"""
        if name not in self.backends:
            return False
        
        try:
            backend_config = config.get(name, {})
            return self.backends[name].initialize(backend_config)
        except Exception as e:
            logger.error(f"Failed to initialize {name} backend: {e}")
            return False
    
    def recognize_speech(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Optional[str]:
        """Recognize speech with automatic fallback"""
        if not self.current_backend:
            logger.error("No speech recognition backend available")
            return None
        
        self.recognition_stats['total_requests'] += 1
        start_time = time.time()
        
        # Try current backend
        result = self._try_recognition(self.current_backend, audio_data, sample_rate)
        
        if result is not None:
            self._update_stats(self.current_backend, True, time.time() - start_time)
            self.recognition_stats['successful_requests'] += 1
            return result
        
        # Try fallback backends
        for backend_name in self.fallback_backends:
            if backend_name != self.current_backend and backend_name in self.backends:
                logger.info(f"Trying fallback backend: {backend_name}")
                result = self._try_recognition(backend_name, audio_data, sample_rate)
                
                if result is not None:
                    self._update_stats(backend_name, True, time.time() - start_time)
                    self.recognition_stats['successful_requests'] += 1
                    
                    # Consider switching to this backend if it's working better
                    self._consider_backend_switch(backend_name)
                    return result
        
        # All backends failed
        self.recognition_stats['error_count'] += 1
        logger.error("All speech recognition backends failed")
        return None
    
    def _try_recognition(self, backend_name: str, audio_data: np.ndarray, 
                       sample_rate: int) -> Optional[str]:
        """Try recognition with a specific backend"""
        if backend_name not in self.backends:
            return None
        
        backend = self.backends[backend_name]
        if not backend.is_available():
            return None
        
        try:
            start_time = time.time()
            result = backend.recognize(audio_data, sample_rate)
            response_time = time.time() - start_time
            
            if result:
                logger.debug(f"{backend_name} recognition successful in {response_time:.2f}s")
                self._update_stats(backend_name, True, response_time)
                return result
            else:
                logger.debug(f"{backend_name} recognition returned empty result")
                self._update_stats(backend_name, False, response_time)
                return None
                
        except Exception as e:
            logger.error(f"{backend_name} recognition failed: {e}")
            self._update_stats(backend_name, False, 0)
            
            # Handle the error through error handler
            error = RecognitionError(f"{backend_name} recognition failed: {e}")
            self.error_handler.handle_error(error, f"speech_recognition_{backend_name}")
            
            return None
    
    def _update_stats(self, backend_name: str, success: bool, response_time: float):
        """Update performance statistics"""
        if backend_name not in self.recognition_stats['backend_usage']:
            return
        
        stats = self.recognition_stats['backend_usage'][backend_name]
        stats['requests'] += 1
        
        if success:
            stats['successes'] += 1
        else:
            stats['failures'] += 1
        
        # Update average response time
        if stats['requests'] > 1:
            stats['avg_response_time'] = (
                (stats['avg_response_time'] * (stats['requests'] - 1) + response_time) 
                / stats['requests']
            )
        else:
            stats['avg_response_time'] = response_time
    
    def _consider_backend_switch(self, backend_name: str):
        """Consider switching to a better performing backend"""
        if backend_name == self.current_backend:
            return
        
        current_stats = self.recognition_stats['backend_usage'].get(self.current_backend, {})
        new_stats = self.recognition_stats['backend_usage'].get(backend_name, {})
        
        # Simple heuristic: switch if the new backend has better success rate
        current_success_rate = (
            current_stats.get('successes', 0) / max(current_stats.get('requests', 1), 1)
        )
        new_success_rate = (
            new_stats.get('successes', 0) / max(new_stats.get('requests', 1), 1)
        )
        
        if new_success_rate > current_success_rate + 0.1:  # 10% better
            logger.info(f"Switching primary backend from {self.current_backend} to {backend_name}")
            self.current_backend = backend_name
    
    def switch_backend(self, backend_name: str) -> bool:
        """Manually switch to a specific backend"""
        if backend_name not in self.backends:
            logger.error(f"Backend {backend_name} not available")
            return False
        
        if not self.backends[backend_name].is_available():
            logger.error(f"Backend {backend_name} not initialized")
            return False
        
        self.current_backend = backend_name
        logger.info(f"Switched to {backend_name} backend")
        return True
    
    def get_available_backends(self) -> List[str]:
        """Get list of available backends"""
        return [
            name for name, backend in self.backends.items() 
            if backend.is_available()
        ]
    
    def get_backend_info(self, backend_name: str = None) -> Dict[str, Any]:
        """Get information about backends"""
        if backend_name:
            if backend_name in self.backends:
                return self.backends[backend_name].get_info()
            else:
                return {}
        
        # Return info for all backends
        return {
            name: backend.get_info() 
            for name, backend in self.backends.items()
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = self.recognition_stats.copy()
        stats['current_backend'] = self.current_backend
        stats['available_backends'] = self.get_available_backends()
        
        # Calculate overall success rate
        if stats['total_requests'] > 0:
            stats['success_rate'] = stats['successful_requests'] / stats['total_requests']
        else:
            stats['success_rate'] = 0.0
        
        return stats
    
    def cleanup(self):
        """Clean up all backends"""
        logger.info("Cleaning up speech recognition router...")
        
        for name, backend in self.backends.items():
            try:
                backend.cleanup()
                logger.debug(f"Cleaned up {name} backend")
            except Exception as e:
                logger.error(f"Error cleaning up {name} backend: {e}")
        
        self.backends.clear()
        self.current_backend = None
        logger.info("Speech recognition router cleanup complete")