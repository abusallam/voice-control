#!/usr/bin/env python3
"""
Health Monitor for Voice Control Application

Continuously monitors system health, audio devices, speech recognition,
memory usage, and implements automatic remediation for common issues.
"""

import logging
import threading
import time
import psutil
import subprocess
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """Types of components to monitor"""
    AUDIO_SYSTEM = "audio_system"
    SPEECH_RECOGNITION = "speech_recognition"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    DISK_USAGE = "disk_usage"
    NETWORK = "network"
    GUI_SYSTEM = "gui_system"
    INPUT_SYSTEM = "input_system"
    SERVICE_STATUS = "service_status"


@dataclass
class HealthCheck:
    """Individual health check result"""
    component: ComponentType
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    remediation_attempted: bool = False
    remediation_successful: bool = False


@dataclass
class HealthThresholds:
    """Configurable health thresholds"""
    memory_warning_mb: int = 400
    memory_critical_mb: int = 600
    cpu_warning_percent: float = 70.0
    cpu_critical_percent: float = 90.0
    disk_warning_percent: float = 85.0
    disk_critical_percent: float = 95.0
    audio_timeout_seconds: float = 5.0
    recognition_timeout_seconds: float = 10.0


class HealthMonitor:
    """Comprehensive health monitoring system"""
    
    def __init__(self, resource_manager=None, error_handler=None):
        self.resource_manager = resource_manager
        self.error_handler = error_handler
        self.thresholds = HealthThresholds()
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.check_interval = 30  # seconds
        
        # Health data
        self.current_health: Dict[ComponentType, HealthCheck] = {}
        self.health_history: List[HealthCheck] = []
        self.max_history_size = 1000
        
        # Remediation handlers
        self.remediation_handlers: Dict[ComponentType, Callable] = {}
        self.remediation_cooldown: Dict[ComponentType, float] = {}
        self.cooldown_period = 300  # 5 minutes
        
        # Statistics
        self.check_count = 0
        self.remediation_count = 0
        self.last_full_check = None
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
        # Register default remediation handlers
        self._register_default_remediations()
        
        logger.info("Health monitor initialized")
    
    def _register_default_remediations(self):
        """Register default remediation handlers"""
        self.register_remediation_handler(ComponentType.AUDIO_SYSTEM, self._remediate_audio_system)
        self.register_remediation_handler(ComponentType.SPEECH_RECOGNITION, self._remediate_speech_recognition)
        self.register_remediation_handler(ComponentType.MEMORY_USAGE, self._remediate_memory_usage)
        self.register_remediation_handler(ComponentType.GUI_SYSTEM, self._remediate_gui_system)
        self.register_remediation_handler(ComponentType.INPUT_SYSTEM, self._remediate_input_system)
    
    def register_remediation_handler(self, component: ComponentType, handler: Callable):
        """Register a remediation handler for a component"""
        self.remediation_handlers[component] = handler
        logger.debug(f"Registered remediation handler for {component.value}")
    
    def start_monitoring(self, interval: int = 30):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            logger.warning("Health monitoring already active")
            return
        
        self.check_interval = interval
        self.monitoring_active = True
        
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        
        logger.info(f"Started health monitoring (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        
        logger.info("Stopped health monitoring")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self.perform_health_check()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                time.sleep(self.check_interval)
    
    def perform_health_check(self) -> Dict[ComponentType, HealthCheck]:
        """Perform comprehensive health check"""
        logger.debug("Performing health check...")
        
        checks = {}
        
        # Perform individual component checks
        checks[ComponentType.MEMORY_USAGE] = self._check_memory_usage()
        checks[ComponentType.CPU_USAGE] = self._check_cpu_usage()
        checks[ComponentType.DISK_USAGE] = self._check_disk_usage()
        checks[ComponentType.AUDIO_SYSTEM] = self._check_audio_system()
        checks[ComponentType.SPEECH_RECOGNITION] = self._check_speech_recognition()
        checks[ComponentType.GUI_SYSTEM] = self._check_gui_system()
        checks[ComponentType.INPUT_SYSTEM] = self._check_input_system()
        checks[ComponentType.SERVICE_STATUS] = self._check_service_status()
        
        # Update current health status
        with self._lock:
            self.current_health.update(checks)
            self.check_count += 1
            self.last_full_check = datetime.now()
        
        # Add to history
        for check in checks.values():
            self._add_to_history(check)
        
        # Attempt remediation for unhealthy components
        self._attempt_remediations(checks)
        
        logger.debug(f"Health check completed. Status: {self._get_overall_status()}")
        return checks
    
    def _check_memory_usage(self) -> HealthCheck:
        """Check memory usage"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            if memory_mb >= self.thresholds.memory_critical_mb:
                status = HealthStatus.CRITICAL
                message = f"Critical memory usage: {memory_mb:.1f}MB"
            elif memory_mb >= self.thresholds.memory_warning_mb:
                status = HealthStatus.WARNING
                message = f"High memory usage: {memory_mb:.1f}MB"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal: {memory_mb:.1f}MB"
            
            return HealthCheck(
                component=ComponentType.MEMORY_USAGE,
                status=status,
                message=message,
                details={
                    "memory_mb": memory_mb,
                    "memory_percent": process.memory_percent(),
                    "threshold_warning": self.thresholds.memory_warning_mb,
                    "threshold_critical": self.thresholds.memory_critical_mb
                }
            )
            
        except Exception as e:
            logger.error(f"Memory check failed: {e}")
            return HealthCheck(
                component=ComponentType.MEMORY_USAGE,
                status=HealthStatus.UNKNOWN,
                message=f"Memory check failed: {e}"
            )
    
    def _check_cpu_usage(self) -> HealthCheck:
        """Check CPU usage"""
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent(interval=1)
            
            if cpu_percent >= self.thresholds.cpu_critical_percent:
                status = HealthStatus.CRITICAL
                message = f"Critical CPU usage: {cpu_percent:.1f}%"
            elif cpu_percent >= self.thresholds.cpu_warning_percent:
                status = HealthStatus.WARNING
                message = f"High CPU usage: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU usage normal: {cpu_percent:.1f}%"
            
            return HealthCheck(
                component=ComponentType.CPU_USAGE,
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "num_threads": process.num_threads(),
                    "threshold_warning": self.thresholds.cpu_warning_percent,
                    "threshold_critical": self.thresholds.cpu_critical_percent
                }
            )
            
        except Exception as e:
            logger.error(f"CPU check failed: {e}")
            return HealthCheck(
                component=ComponentType.CPU_USAGE,
                status=HealthStatus.UNKNOWN,
                message=f"CPU check failed: {e}"
            )
    
    def _check_disk_usage(self) -> HealthCheck:
        """Check disk usage"""
        try:
            # Check home directory disk usage
            home_path = Path.home()
            disk_usage = psutil.disk_usage(str(home_path))
            used_percent = (disk_usage.used / disk_usage.total) * 100
            
            if used_percent >= self.thresholds.disk_critical_percent:
                status = HealthStatus.CRITICAL
                message = f"Critical disk usage: {used_percent:.1f}%"
            elif used_percent >= self.thresholds.disk_warning_percent:
                status = HealthStatus.WARNING
                message = f"High disk usage: {used_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage normal: {used_percent:.1f}%"
            
            return HealthCheck(
                component=ComponentType.DISK_USAGE,
                status=status,
                message=message,
                details={
                    "used_percent": used_percent,
                    "free_gb": disk_usage.free / (1024**3),
                    "total_gb": disk_usage.total / (1024**3),
                    "threshold_warning": self.thresholds.disk_warning_percent,
                    "threshold_critical": self.thresholds.disk_critical_percent
                }
            )
            
        except Exception as e:
            logger.error(f"Disk check failed: {e}")
            return HealthCheck(
                component=ComponentType.DISK_USAGE,
                status=HealthStatus.UNKNOWN,
                message=f"Disk check failed: {e}"
            )
    
    def _check_audio_system(self) -> HealthCheck:
        """Check audio system health"""
        try:
            # Check for PulseAudio
            pulse_check = self._check_pulseaudio()
            if pulse_check:
                return pulse_check
            
            # Check for PipeWire
            pipewire_check = self._check_pipewire()
            if pipewire_check:
                return pipewire_check
            
            # Check for ALSA
            alsa_check = self._check_alsa()
            if alsa_check:
                return alsa_check
            
            return HealthCheck(
                component=ComponentType.AUDIO_SYSTEM,
                status=HealthStatus.CRITICAL,
                message="No audio system detected"
            )
            
        except Exception as e:
            logger.error(f"Audio system check failed: {e}")
            return HealthCheck(
                component=ComponentType.AUDIO_SYSTEM,
                status=HealthStatus.UNKNOWN,
                message=f"Audio check failed: {e}"
            )
    
    def _check_pulseaudio(self) -> Optional[HealthCheck]:
        """Check PulseAudio status"""
        try:
            result = subprocess.run(
                ["pulseaudio", "--check"],
                capture_output=True,
                timeout=self.thresholds.audio_timeout_seconds
            )
            
            if result.returncode == 0:
                # Get audio devices
                devices_result = subprocess.run(
                    ["pactl", "list", "short", "sources"],
                    capture_output=True,
                    text=True,
                    timeout=self.thresholds.audio_timeout_seconds
                )
                
                device_count = len(devices_result.stdout.strip().split('\n')) if devices_result.stdout.strip() else 0
                
                return HealthCheck(
                    component=ComponentType.AUDIO_SYSTEM,
                    status=HealthStatus.HEALTHY,
                    message=f"PulseAudio running with {device_count} input devices",
                    details={"audio_system": "pulseaudio", "device_count": device_count}
                )
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            pass
        
        return None
    
    def _check_pipewire(self) -> Optional[HealthCheck]:
        """Check PipeWire status"""
        try:
            result = subprocess.run(
                ["pipewire", "--version"],
                capture_output=True,
                timeout=self.thresholds.audio_timeout_seconds
            )
            
            if result.returncode == 0:
                return HealthCheck(
                    component=ComponentType.AUDIO_SYSTEM,
                    status=HealthStatus.HEALTHY,
                    message="PipeWire detected",
                    details={"audio_system": "pipewire"}
                )
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            pass
        
        return None
    
    def _check_alsa(self) -> Optional[HealthCheck]:
        """Check ALSA status"""
        try:
            result = subprocess.run(
                ["aplay", "-l"],
                capture_output=True,
                text=True,
                timeout=self.thresholds.audio_timeout_seconds
            )
            
            if result.returncode == 0 and "card" in result.stdout:
                card_count = result.stdout.count("card")
                return HealthCheck(
                    component=ComponentType.AUDIO_SYSTEM,
                    status=HealthStatus.HEALTHY,
                    message=f"ALSA detected with {card_count} cards",
                    details={"audio_system": "alsa", "card_count": card_count}
                )
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            pass
        
        return None
    
    def _check_speech_recognition(self) -> HealthCheck:
        """Check speech recognition system"""
        try:
            # This is a placeholder - would need to integrate with actual speech recognition
            # For now, just check if the recognition module can be imported
            
            details = {"engines_available": []}
            
            # Check for Whisper
            try:
                import whisper
                details["engines_available"].append("whisper")
            except ImportError:
                pass
            
            # Check for speech recognition engines (placeholder)
            try:
                # This would check for speech recognition availability
                # TODO: Add actual speech recognition engine checks
                pass
            except:
                pass
            
            if details["engines_available"]:
                return HealthCheck(
                    component=ComponentType.SPEECH_RECOGNITION,
                    status=HealthStatus.HEALTHY,
                    message=f"Speech recognition available: {', '.join(details['engines_available'])}",
                    details=details
                )
            else:
                return HealthCheck(
                    component=ComponentType.SPEECH_RECOGNITION,
                    status=HealthStatus.WARNING,
                    message="No speech recognition engines detected",
                    details=details
                )
                
        except Exception as e:
            logger.error(f"Speech recognition check failed: {e}")
            return HealthCheck(
                component=ComponentType.SPEECH_RECOGNITION,
                status=HealthStatus.UNKNOWN,
                message=f"Speech recognition check failed: {e}"
            )
    
    def _check_gui_system(self) -> HealthCheck:
        """Check GUI system health"""
        try:
            import os
            
            details = {}
            
            # Check display server
            if os.getenv("WAYLAND_DISPLAY"):
                details["display_server"] = "wayland"
                details["display"] = os.getenv("WAYLAND_DISPLAY")
            elif os.getenv("DISPLAY"):
                details["display_server"] = "x11"
                details["display"] = os.getenv("DISPLAY")
            else:
                return HealthCheck(
                    component=ComponentType.GUI_SYSTEM,
                    status=HealthStatus.CRITICAL,
                    message="No display server detected"
                )
            
            # Check for GUI framework availability
            gui_frameworks = []
            try:
                import PyQt5
                gui_frameworks.append("PyQt5")
            except ImportError:
                pass
            
            try:
                import tkinter
                gui_frameworks.append("tkinter")
            except ImportError:
                pass
            
            details["gui_frameworks"] = gui_frameworks
            
            if gui_frameworks:
                return HealthCheck(
                    component=ComponentType.GUI_SYSTEM,
                    status=HealthStatus.HEALTHY,
                    message=f"GUI system healthy: {details['display_server']} with {', '.join(gui_frameworks)}",
                    details=details
                )
            else:
                return HealthCheck(
                    component=ComponentType.GUI_SYSTEM,
                    status=HealthStatus.WARNING,
                    message="No GUI frameworks available",
                    details=details
                )
                
        except Exception as e:
            logger.error(f"GUI system check failed: {e}")
            return HealthCheck(
                component=ComponentType.GUI_SYSTEM,
                status=HealthStatus.UNKNOWN,
                message=f"GUI check failed: {e}"
            )
    
    def _check_input_system(self) -> HealthCheck:
        """Check input system health"""
        try:
            input_tools = []
            
            # Check for input simulation tools
            tools_to_check = ["xdotool", "ydotool", "wtype", "dotool"]
            
            for tool in tools_to_check:
                try:
                    result = subprocess.run(
                        [tool, "--help"],
                        capture_output=True,
                        timeout=2
                    )
                    if result.returncode == 0:
                        input_tools.append(tool)
                except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
                    pass
            
            if input_tools:
                return HealthCheck(
                    component=ComponentType.INPUT_SYSTEM,
                    status=HealthStatus.HEALTHY,
                    message=f"Input tools available: {', '.join(input_tools)}",
                    details={"input_tools": input_tools}
                )
            else:
                return HealthCheck(
                    component=ComponentType.INPUT_SYSTEM,
                    status=HealthStatus.WARNING,
                    message="No input simulation tools detected",
                    details={"input_tools": input_tools}
                )
                
        except Exception as e:
            logger.error(f"Input system check failed: {e}")
            return HealthCheck(
                component=ComponentType.INPUT_SYSTEM,
                status=HealthStatus.UNKNOWN,
                message=f"Input check failed: {e}"
            )
    
    def _check_service_status(self) -> HealthCheck:
        """Check voice control service status"""
        try:
            # Check systemd user service
            result = subprocess.run(
                ["systemctl", "--user", "is-active", "voice-control"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            service_active = result.stdout.strip() == "active"
            
            if service_active:
                return HealthCheck(
                    component=ComponentType.SERVICE_STATUS,
                    status=HealthStatus.HEALTHY,
                    message="Voice control service is active",
                    details={"service_active": True}
                )
            else:
                return HealthCheck(
                    component=ComponentType.SERVICE_STATUS,
                    status=HealthStatus.WARNING,
                    message="Voice control service is not active",
                    details={"service_active": False}
                )
                
        except Exception as e:
            logger.error(f"Service status check failed: {e}")
            return HealthCheck(
                component=ComponentType.SERVICE_STATUS,
                status=HealthStatus.UNKNOWN,
                message=f"Service check failed: {e}"
            )
    
    def _attempt_remediations(self, checks: Dict[ComponentType, HealthCheck]):
        """Attempt remediation for unhealthy components"""
        for component, check in checks.items():
            if check.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                if self._should_attempt_remediation(component):
                    logger.info(f"Attempting remediation for {component.value}")
                    success = self._attempt_remediation(component, check)
                    
                    check.remediation_attempted = True
                    check.remediation_successful = success
                    
                    if success:
                        logger.info(f"Remediation successful for {component.value}")
                        self.remediation_count += 1
                    else:
                        logger.warning(f"Remediation failed for {component.value}")
    
    def _should_attempt_remediation(self, component: ComponentType) -> bool:
        """Check if remediation should be attempted (considering cooldown)"""
        if component not in self.remediation_handlers:
            return False
        
        last_attempt = self.remediation_cooldown.get(component, 0)
        return time.time() - last_attempt > self.cooldown_period
    
    def _attempt_remediation(self, component: ComponentType, check: HealthCheck) -> bool:
        """Attempt remediation for a specific component"""
        try:
            self.remediation_cooldown[component] = time.time()
            
            if component in self.remediation_handlers:
                return self.remediation_handlers[component](check)
            else:
                logger.warning(f"No remediation handler for {component.value}")
                return False
                
        except Exception as e:
            logger.error(f"Remediation attempt failed for {component.value}: {e}")
            return False
    
    def _remediate_audio_system(self, check: HealthCheck) -> bool:
        """Attempt to remediate audio system issues"""
        try:
            # Try to restart PulseAudio
            subprocess.run(["pulseaudio", "--kill"], capture_output=True, timeout=5)
            time.sleep(2)
            subprocess.run(["pulseaudio", "--start"], capture_output=True, timeout=5)
            
            # Verify fix
            time.sleep(3)
            new_check = self._check_audio_system()
            return new_check.status == HealthStatus.HEALTHY
            
        except Exception as e:
            logger.error(f"Audio remediation failed: {e}")
            return False
    
    def _remediate_speech_recognition(self, check: HealthCheck) -> bool:
        """Attempt to remediate speech recognition issues"""
        # This would implement speech recognition remediation
        logger.info("Speech recognition remediation not yet implemented")
        return False
    
    def _remediate_memory_usage(self, check: HealthCheck) -> bool:
        """Attempt to remediate memory usage issues"""
        try:
            if self.resource_manager:
                # Trigger memory cleanup
                self.resource_manager._trigger_memory_cleanup()
                
                # Verify improvement
                time.sleep(2)
                new_check = self._check_memory_usage()
                return new_check.status != HealthStatus.CRITICAL
            
            return False
            
        except Exception as e:
            logger.error(f"Memory remediation failed: {e}")
            return False
    
    def _remediate_gui_system(self, check: HealthCheck) -> bool:
        """Attempt to remediate GUI system issues"""
        # This would implement GUI remediation
        logger.info("GUI system remediation not yet implemented")
        return False
    
    def _remediate_input_system(self, check: HealthCheck) -> bool:
        """Attempt to remediate input system issues"""
        # This would implement input system remediation
        logger.info("Input system remediation not yet implemented")
        return False
    
    def _add_to_history(self, check: HealthCheck):
        """Add health check to history"""
        with self._lock:
            self.health_history.append(check)
            
            # Trim history if too large
            if len(self.health_history) > self.max_history_size:
                self.health_history.pop(0)
    
    def _get_overall_status(self) -> HealthStatus:
        """Get overall system health status"""
        with self._lock:
            if not self.current_health:
                return HealthStatus.UNKNOWN
            
            statuses = [check.status for check in self.current_health.values()]
            
            if HealthStatus.CRITICAL in statuses:
                return HealthStatus.CRITICAL
            elif HealthStatus.WARNING in statuses:
                return HealthStatus.WARNING
            elif HealthStatus.UNKNOWN in statuses:
                return HealthStatus.UNKNOWN
            else:
                return HealthStatus.HEALTHY
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        with self._lock:
            overall_status = self._get_overall_status()
            
            component_status = {}
            for component, check in self.current_health.items():
                component_status[component.value] = {
                    "status": check.status.value,
                    "message": check.message,
                    "details": check.details,
                    "timestamp": check.timestamp.isoformat(),
                    "remediation_attempted": check.remediation_attempted,
                    "remediation_successful": check.remediation_successful
                }
            
            return {
                "overall_status": overall_status.value,
                "last_check": self.last_full_check.isoformat() if self.last_full_check else None,
                "check_count": self.check_count,
                "remediation_count": self.remediation_count,
                "components": component_status,
                "thresholds": {
                    "memory_warning_mb": self.thresholds.memory_warning_mb,
                    "memory_critical_mb": self.thresholds.memory_critical_mb,
                    "cpu_warning_percent": self.thresholds.cpu_warning_percent,
                    "cpu_critical_percent": self.thresholds.cpu_critical_percent
                }
            }
    
    def get_health_history(self, component: Optional[ComponentType] = None, 
                          hours: int = 24) -> List[Dict[str, Any]]:
        """Get health history for analysis"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            filtered_history = [
                check for check in self.health_history
                if check.timestamp >= cutoff_time and
                (component is None or check.component == component)
            ]
        
        return [
            {
                "component": check.component.value,
                "status": check.status.value,
                "message": check.message,
                "details": check.details,
                "timestamp": check.timestamp.isoformat(),
                "remediation_attempted": check.remediation_attempted,
                "remediation_successful": check.remediation_successful
            }
            for check in filtered_history
        ]


# Global health monitor instance
_global_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor(resource_manager=None, error_handler=None) -> HealthMonitor:
    """Get or create global health monitor instance"""
    global _global_health_monitor
    
    if _global_health_monitor is None:
        _global_health_monitor = HealthMonitor(resource_manager, error_handler)
    
    return _global_health_monitor


def main():
    """Test the health monitor"""
    logging.basicConfig(level=logging.DEBUG)
    
    # Import resource manager and error handler
    try:
        from voice_control.core.resource_manager import get_resource_manager
        from voice_control.core.error_handler import get_error_handler
        
        resource_manager = get_resource_manager()
        error_handler = get_error_handler()
    except ImportError:
        resource_manager = None
        error_handler = None
    
    health_monitor = HealthMonitor(resource_manager, error_handler)
    
    # Perform health check
    print("Performing health check...")
    checks = health_monitor.perform_health_check()
    
    # Print results
    for component, check in checks.items():
        status_emoji = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.WARNING: "⚠️",
            HealthStatus.CRITICAL: "❌",
            HealthStatus.UNKNOWN: "❓"
        }
        
        print(f"{status_emoji[check.status]} {component.value}: {check.message}")
    
    # Print overall report
    print("\nHealth Report:")
    report = health_monitor.get_health_report()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()