#!/usr/bin/env python3
"""
Resource Manager for Voice Control Application

Manages system resources, prevents memory leaks, and handles cleanup
to prevent the system hangs and restart issues.
"""

import gc
import logging
import psutil
import threading
import time
import weakref
from typing import Any, Callable, Dict, List, Optional
from contextlib import contextmanager
import signal
import sys

logger = logging.getLogger(__name__)


class ResourceManager:
    """Manages system resources and prevents memory leaks"""
    
    def __init__(self, max_memory_mb: int = 500):
        self.max_memory_mb = max_memory_mb
        self.active_resources: Dict[str, Dict[str, Any]] = {}
        self.cleanup_handlers: List[Callable] = []
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        self.process = psutil.Process()
        self._lock = threading.Lock()
        
        # Register signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.cleanup_all()
            sys.exit(0)
            
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    def register_resource(self, name: str, resource: Any, cleanup_func: Callable[[Any], None]):
        """Register a resource for automatic cleanup"""
        with self._lock:
            self.active_resources[name] = {
                'resource': resource,
                'cleanup': cleanup_func,
                'created_at': time.time(),
                'last_accessed': time.time()
            }
            logger.debug(f"Registered resource: {name}")
    
    def unregister_resource(self, name: str) -> bool:
        """Unregister a resource"""
        with self._lock:
            if name in self.active_resources:
                del self.active_resources[name]
                logger.debug(f"Unregistered resource: {name}")
                return True
            return False
    
    def cleanup_resource(self, name: str) -> bool:
        """Clean up a specific resource"""
        with self._lock:
            if name not in self.active_resources:
                return False
                
            resource_info = self.active_resources[name]
            try:
                resource_info['cleanup'](resource_info['resource'])
                del self.active_resources[name]
                logger.debug(f"Cleaned up resource: {name}")
                return True
            except Exception as e:
                logger.error(f"Failed to cleanup resource {name}: {e}")
                # Remove it anyway to prevent accumulation
                del self.active_resources[name]
                return False
    
    def cleanup_all(self):
        """Clean up all registered resources"""
        logger.info("Cleaning up all resources...")
        
        with self._lock:
            resources_to_cleanup = list(self.active_resources.items())
        
        for name, resource_info in resources_to_cleanup:
            try:
                resource_info['cleanup'](resource_info['resource'])
                logger.debug(f"Cleaned up resource: {name}")
            except Exception as e:
                logger.error(f"Failed to cleanup resource {name}: {e}")
        
        with self._lock:
            self.active_resources.clear()
        
        # Run additional cleanup handlers
        for handler in self.cleanup_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Cleanup handler failed: {e}")
        
        # Force garbage collection
        gc.collect()
        logger.info("Resource cleanup completed")
    
    def add_cleanup_handler(self, handler: Callable[[], None]):
        """Add a cleanup handler to be called during shutdown"""
        self.cleanup_handlers.append(handler)
    
    def start_monitoring(self, interval: int = 30):
        """Start resource monitoring in a separate thread"""
        if self.monitoring_active:
            logger.warning("Resource monitoring already active")
            return
            
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"Started resource monitoring (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Stopped resource monitoring")
    
    def _monitoring_loop(self, interval: int):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._check_memory_usage()
                self._check_resource_age()
                self._check_system_health()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def _check_memory_usage(self):
        """Monitor and manage memory usage"""
        try:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            if memory_mb > self.max_memory_mb:
                logger.warning(f"High memory usage: {memory_mb:.1f}MB (limit: {self.max_memory_mb}MB)")
                self._trigger_memory_cleanup()
                
                # Check again after cleanup
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                logger.info(f"Memory usage after cleanup: {memory_mb:.1f}MB")
                
        except Exception as e:
            logger.error(f"Error checking memory usage: {e}")
    
    def _check_resource_age(self):
        """Check for old resources that might need cleanup"""
        current_time = time.time()
        old_resources = []
        
        with self._lock:
            for name, info in self.active_resources.items():
                age = current_time - info['created_at']
                last_access_age = current_time - info['last_accessed']
                
                # Flag resources older than 1 hour and not accessed in 30 minutes
                if age > 3600 and last_access_age > 1800:
                    old_resources.append(name)
        
        for name in old_resources:
            logger.info(f"Cleaning up old resource: {name}")
            self.cleanup_resource(name)
    
    def _check_system_health(self):
        """Check overall system health"""
        try:
            # Check CPU usage
            cpu_percent = self.process.cpu_percent()
            if cpu_percent > 80:
                logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
            
            # Check file descriptors
            num_fds = self.process.num_fds()
            if num_fds > 100:  # Arbitrary threshold
                logger.warning(f"High number of file descriptors: {num_fds}")
            
            # Check thread count
            num_threads = self.process.num_threads()
            if num_threads > 20:  # Arbitrary threshold
                logger.warning(f"High number of threads: {num_threads}")
                
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
    
    def _trigger_memory_cleanup(self):
        """Trigger memory cleanup procedures"""
        logger.info("Triggering memory cleanup...")
        
        # Force garbage collection
        collected = gc.collect()
        logger.debug(f"Garbage collection freed {collected} objects")
        
        # Clean up old resources
        self._cleanup_old_resources()
        
        # Additional cleanup can be added here
        
    def _cleanup_old_resources(self):
        """Clean up resources that haven't been accessed recently"""
        current_time = time.time()
        to_cleanup = []
        
        with self._lock:
            for name, info in self.active_resources.items():
                if current_time - info['last_accessed'] > 600:  # 10 minutes
                    to_cleanup.append(name)
        
        for name in to_cleanup:
            logger.debug(f"Cleaning up inactive resource: {name}")
            self.cleanup_resource(name)
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """Get current resource statistics"""
        try:
            memory_info = self.process.memory_info()
            
            with self._lock:
                active_count = len(self.active_resources)
                resource_names = list(self.active_resources.keys())
            
            return {
                'memory_mb': memory_info.rss / 1024 / 1024,
                'memory_limit_mb': self.max_memory_mb,
                'active_resources': active_count,
                'resource_names': resource_names,
                'cpu_percent': self.process.cpu_percent(),
                'num_threads': self.process.num_threads(),
                'num_fds': self.process.num_fds(),
            }
        except Exception as e:
            logger.error(f"Error getting resource stats: {e}")
            return {}
    
    @contextmanager
    def managed_resource(self, name: str, resource: Any, cleanup_func: Callable[[Any], None]):
        """Context manager for automatic resource management"""
        self.register_resource(name, resource, cleanup_func)
        try:
            yield resource
        finally:
            self.cleanup_resource(name)


class AudioResourceManager:
    """Specialized resource manager for audio components"""
    
    def __init__(self, resource_manager: ResourceManager):
        self.resource_manager = resource_manager
        self.audio_buffers: List[Any] = []
        self.audio_streams: List[Any] = []
        
    def register_audio_buffer(self, buffer: Any):
        """Register an audio buffer for cleanup"""
        self.audio_buffers.append(weakref.ref(buffer))
        self.resource_manager.register_resource(
            f"audio_buffer_{id(buffer)}", 
            buffer, 
            self._cleanup_buffer
        )
    
    def register_audio_stream(self, stream: Any):
        """Register an audio stream for cleanup"""
        self.audio_streams.append(weakref.ref(stream))
        self.resource_manager.register_resource(
            f"audio_stream_{id(stream)}", 
            stream, 
            self._cleanup_stream
        )
    
    def _cleanup_buffer(self, buffer: Any):
        """Clean up audio buffer"""
        try:
            if hasattr(buffer, 'close'):
                buffer.close()
            elif hasattr(buffer, 'clear'):
                buffer.clear()
        except Exception as e:
            logger.error(f"Error cleaning up audio buffer: {e}")
    
    def _cleanup_stream(self, stream: Any):
        """Clean up audio stream"""
        try:
            if hasattr(stream, 'stop'):
                stream.stop()
            if hasattr(stream, 'close'):
                stream.close()
        except Exception as e:
            logger.error(f"Error cleaning up audio stream: {e}")
    
    def clear_all_buffers(self):
        """Clear all audio buffers"""
        for buffer_ref in self.audio_buffers[:]:
            buffer = buffer_ref()
            if buffer is not None:
                self._cleanup_buffer(buffer)
        self.audio_buffers.clear()


# Global resource manager instance
_global_resource_manager: Optional[ResourceManager] = None


def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance"""
    global _global_resource_manager
    if _global_resource_manager is None:
        _global_resource_manager = ResourceManager()
        _global_resource_manager.start_monitoring()
    return _global_resource_manager


def cleanup_on_exit():
    """Cleanup function to be called on application exit"""
    global _global_resource_manager
    if _global_resource_manager:
        _global_resource_manager.stop_monitoring()
        _global_resource_manager.cleanup_all()


# Register cleanup on exit
import atexit
atexit.register(cleanup_on_exit)