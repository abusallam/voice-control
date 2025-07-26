#!/usr/bin/env python3
"""
Comprehensive Logging and Diagnostics System for Voice Control Application

Provides structured logging, performance metrics, diagnostic tools,
and log rotation to prevent disk space issues.
"""

import logging
import logging.handlers
import json
import time
import threading
import psutil
import platform
import subprocess
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
import traceback
import sys
import os

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Enhanced log levels"""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    PERFORMANCE = 25
    DIAGNOSTIC = 15


class MetricType(Enum):
    """Types of performance metrics"""
    TIMING = "timing"
    COUNTER = "counter"
    GAUGE = "gauge"
    ACCURACY = "accuracy"
    RESOURCE_USAGE = "resource_usage"


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    metric_type: MetricType
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "type": self.metric_type.value,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context
        }


@dataclass
class DiagnosticInfo:
    """System diagnostic information"""
    timestamp: datetime = field(default_factory=datetime.now)
    system_info: Dict[str, Any] = field(default_factory=dict)
    process_info: Dict[str, Any] = field(default_factory=dict)
    voice_control_info: Dict[str, Any] = field(default_factory=dict)
    environment_info: Dict[str, Any] = field(default_factory=dict)
    error_summary: Dict[str, Any] = field(default_factory=dict)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def format(self, record):
        # Create structured log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "levelname", "levelno", "pathname",
                          "filename", "module", "lineno", "funcName", "created",
                          "msecs", "relativeCreated", "thread", "threadName",
                          "processName", "process", "getMessage", "exc_info",
                          "exc_text", "stack_info"]:
                log_entry[key] = value
        
        return json.dumps(log_entry)


class PerformanceLogger:
    """Performance metrics logging and analysis"""
    
    def __init__(self, max_metrics: int = 10000):
        self.metrics: List[PerformanceMetric] = []
        self.max_metrics = max_metrics
        self._lock = threading.Lock()
        
        # Performance counters
        self.counters: Dict[str, int] = {}
        self.timers: Dict[str, float] = {}
        
    def log_timing(self, name: str, duration: float, unit: str = "seconds", **context):
        """Log timing metric"""
        metric = PerformanceMetric(
            name=name,
            metric_type=MetricType.TIMING,
            value=duration,
            unit=unit,
            context=context
        )
        self._add_metric(metric)
    
    def log_counter(self, name: str, value: int = 1, **context):
        """Log counter metric"""
        with self._lock:
            self.counters[name] = self.counters.get(name, 0) + value
        
        metric = PerformanceMetric(
            name=name,
            metric_type=MetricType.COUNTER,
            value=value,
            unit="count",
            context=context
        )
        self._add_metric(metric)
    
    def log_gauge(self, name: str, value: float, unit: str, **context):
        """Log gauge metric"""
        metric = PerformanceMetric(
            name=name,
            metric_type=MetricType.GAUGE,
            value=value,
            unit=unit,
            context=context
        )
        self._add_metric(metric)
    
    def log_accuracy(self, name: str, accuracy: float, **context):
        """Log accuracy metric"""
        metric = PerformanceMetric(
            name=name,
            metric_type=MetricType.ACCURACY,
            value=accuracy,
            unit="percent",
            context=context
        )
        self._add_metric(metric)
    
    def log_resource_usage(self, **context):
        """Log current resource usage"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            self.log_gauge("memory_usage", memory_info.rss / 1024 / 1024, "MB", **context)
            self.log_gauge("cpu_usage", process.cpu_percent(), "percent", **context)
            self.log_gauge("thread_count", process.num_threads(), "count", **context)
            self.log_gauge("fd_count", process.num_fds(), "count", **context)
            
        except Exception as e:
            logger.error(f"Failed to log resource usage: {e}")
    
    def _add_metric(self, metric: PerformanceMetric):
        """Add metric to collection"""
        with self._lock:
            self.metrics.append(metric)
            
            # Trim if too many metrics
            if len(self.metrics) > self.max_metrics:
                self.metrics.pop(0)
    
    def get_metrics(self, name_pattern: Optional[str] = None, 
                   hours: int = 24) -> List[PerformanceMetric]:
        """Get metrics matching criteria"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            filtered_metrics = [
                metric for metric in self.metrics
                if metric.timestamp >= cutoff_time and
                (name_pattern is None or name_pattern in metric.name)
            ]
        
        return filtered_metrics
    
    def get_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary"""
        metrics = self.get_metrics(hours=hours)
        
        summary = {
            "total_metrics": len(metrics),
            "time_range_hours": hours,
            "by_type": {},
            "top_timings": [],
            "counters": dict(self.counters),
            "resource_usage": {}
        }
        
        # Group by type
        for metric in metrics:
            metric_type = metric.metric_type.value
            if metric_type not in summary["by_type"]:
                summary["by_type"][metric_type] = []
            summary["by_type"][metric_type].append(metric.to_dict())
        
        # Get top timings
        timing_metrics = [m for m in metrics if m.metric_type == MetricType.TIMING]
        timing_metrics.sort(key=lambda x: x.value, reverse=True)
        summary["top_timings"] = [m.to_dict() for m in timing_metrics[:10]]
        
        # Get latest resource usage
        resource_metrics = [m for m in metrics if m.metric_type == MetricType.GAUGE]
        for metric in resource_metrics:
            if metric.name.endswith("_usage") or metric.name.endswith("_count"):
                summary["resource_usage"][metric.name] = {
                    "value": metric.value,
                    "unit": metric.unit,
                    "timestamp": metric.timestamp.isoformat()
                }
        
        return summary


class DiagnosticCollector:
    """Collects comprehensive diagnostic information"""
    
    def __init__(self):
        self.collectors: Dict[str, Callable] = {}
        self._register_default_collectors()
    
    def _register_default_collectors(self):
        """Register default diagnostic collectors"""
        self.collectors["system"] = self._collect_system_info
        self.collectors["process"] = self._collect_process_info
        self.collectors["environment"] = self._collect_environment_info
        self.collectors["voice_control"] = self._collect_voice_control_info
        self.collectors["audio"] = self._collect_audio_info
        self.collectors["gui"] = self._collect_gui_info
        self.collectors["network"] = self._collect_network_info
    
    def register_collector(self, name: str, collector: Callable):
        """Register custom diagnostic collector"""
        self.collectors[name] = collector
    
    def collect_diagnostics(self) -> DiagnosticInfo:
        """Collect comprehensive diagnostic information"""
        diagnostic_info = DiagnosticInfo()
        
        for name, collector in self.collectors.items():
            try:
                data = collector()
                setattr(diagnostic_info, f"{name}_info", data)
            except Exception as e:
                logger.error(f"Diagnostic collector '{name}' failed: {e}")
                setattr(diagnostic_info, f"{name}_info", {"error": str(e)})
        
        return diagnostic_info
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect system information"""
        return {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "disk_usage": {
                path: {
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free
                }
                for path, usage in [
                    ("/", psutil.disk_usage("/")),
                    (str(Path.home()), psutil.disk_usage(str(Path.home())))
                ]
            }
        }
    
    def _collect_process_info(self) -> Dict[str, Any]:
        """Collect process information"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                "pid": process.pid,
                "ppid": process.ppid(),
                "name": process.name(),
                "status": process.status(),
                "create_time": process.create_time(),
                "cpu_percent": process.cpu_percent(),
                "memory_info": {
                    "rss": memory_info.rss,
                    "vms": memory_info.vms,
                    "percent": process.memory_percent()
                },
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds(),
                "connections": len(process.connections()),
                "cmdline": process.cmdline()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _collect_environment_info(self) -> Dict[str, Any]:
        """Collect environment information"""
        return {
            "user": os.getenv("USER"),
            "home": os.getenv("HOME"),
            "display": os.getenv("DISPLAY"),
            "wayland_display": os.getenv("WAYLAND_DISPLAY"),
            "xdg_session_type": os.getenv("XDG_SESSION_TYPE"),
            "xdg_current_desktop": os.getenv("XDG_CURRENT_DESKTOP"),
            "lang": os.getenv("LANG"),
            "path": os.getenv("PATH"),
            "python_path": sys.path,
            "working_directory": os.getcwd()
        }
    
    def _collect_voice_control_info(self) -> Dict[str, Any]:
        """Collect voice control specific information"""
        info = {
            "version": "2.0.0",  # Would be read from version file
            "config_dir": str(Path.home() / ".config/voice-control"),
            "data_dir": str(Path.home() / ".local/share/voice-control"),
            "log_dir": str(Path.home() / ".local/share/voice-control/logs")
        }
        
        # Check if directories exist
        for key, path in info.items():
            if key.endswith("_dir"):
                info[f"{key}_exists"] = Path(path).exists()
        
        # Check service status
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-active", "voice-control"],
                capture_output=True,
                text=True,
                timeout=5
            )
            info["service_active"] = result.stdout.strip() == "active"
        except Exception:
            info["service_active"] = False
        
        return info
    
    def _collect_audio_info(self) -> Dict[str, Any]:
        """Collect audio system information"""
        info = {"audio_systems": []}
        
        # Check PulseAudio
        try:
            result = subprocess.run(
                ["pulseaudio", "--check"],
                capture_output=True,
                timeout=3
            )
            if result.returncode == 0:
                info["audio_systems"].append("pulseaudio")
                
                # Get audio devices
                try:
                    devices_result = subprocess.run(
                        ["pactl", "list", "short", "sources"],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    info["pulseaudio_sources"] = devices_result.stdout.strip().split('\n')
                except Exception:
                    pass
        except Exception:
            pass
        
        # Check PipeWire
        try:
            result = subprocess.run(
                ["pipewire", "--version"],
                capture_output=True,
                timeout=3
            )
            if result.returncode == 0:
                info["audio_systems"].append("pipewire")
        except Exception:
            pass
        
        # Check ALSA
        try:
            result = subprocess.run(
                ["aplay", "-l"],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode == 0:
                info["audio_systems"].append("alsa")
                info["alsa_devices"] = result.stdout.strip().split('\n')
        except Exception:
            pass
        
        return info
    
    def _collect_gui_info(self) -> Dict[str, Any]:
        """Collect GUI system information"""
        info = {
            "display_server": "none",
            "gui_frameworks": []
        }
        
        # Detect display server
        if os.getenv("WAYLAND_DISPLAY"):
            info["display_server"] = "wayland"
        elif os.getenv("DISPLAY"):
            info["display_server"] = "x11"
        
        # Check GUI frameworks
        try:
            import PyQt5
            info["gui_frameworks"].append("PyQt5")
        except ImportError:
            pass
        
        try:
            import tkinter
            info["gui_frameworks"].append("tkinter")
        except ImportError:
            pass
        
        # Check input tools
        info["input_tools"] = []
        for tool in ["xdotool", "ydotool", "wtype", "dotool"]:
            try:
                result = subprocess.run(
                    [tool, "--help"],
                    capture_output=True,
                    timeout=2
                )
                if result.returncode == 0:
                    info["input_tools"].append(tool)
            except Exception:
                pass
        
        return info
    
    def _collect_network_info(self) -> Dict[str, Any]:
        """Collect network information"""
        try:
            return {
                "hostname": platform.node(),
                "network_interfaces": [
                    {
                        "name": interface,
                        "addresses": [addr.address for addr in addresses]
                    }
                    for interface, addresses in psutil.net_if_addrs().items()
                ],
                "network_stats": {
                    interface: {
                        "bytes_sent": stats.bytes_sent,
                        "bytes_recv": stats.bytes_recv,
                        "packets_sent": stats.packets_sent,
                        "packets_recv": stats.packets_recv
                    }
                    for interface, stats in psutil.net_io_counters(pernic=True).items()
                }
            }
        except Exception as e:
            return {"error": str(e)}


class LoggingManager:
    """Comprehensive logging management system"""
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path.home() / ".local/share/voice-control/logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.performance_logger = PerformanceLogger()
        self.diagnostic_collector = DiagnosticCollector()
        
        # Setup logging
        self._setup_logging()
        
        # Add custom log level
        logging.addLevelName(LogLevel.TRACE.value, "TRACE")
        logging.addLevelName(LogLevel.PERFORMANCE.value, "PERFORMANCE")
        logging.addLevelName(LogLevel.DIAGNOSTIC.value, "DIAGNOSTIC")
    
    def _setup_logging(self):
        """Setup comprehensive logging configuration"""
        # Main application log
        main_log = self.log_dir / "voice-control.log"
        main_handler = logging.handlers.RotatingFileHandler(
            main_log,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        main_handler.setFormatter(StructuredFormatter())
        
        # Error log
        error_log = self.log_dir / "error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        
        # Performance log
        perf_log = self.log_dir / "performance.log"
        perf_handler = logging.handlers.RotatingFileHandler(
            perf_log,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3
        )
        perf_handler.setLevel(LogLevel.PERFORMANCE.value)
        perf_handler.setFormatter(StructuredFormatter())
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(main_handler)
        root_logger.addHandler(error_handler)
        root_logger.addHandler(perf_handler)
        root_logger.addHandler(console_handler)
        
        logger.info("Logging system initialized")
    
    def log_performance(self, name: str, duration: float, **context):
        """Log performance metric"""
        self.performance_logger.log_timing(name, duration, **context)
        
        # Also log to performance logger
        perf_logger = logging.getLogger("performance")
        perf_logger.log(LogLevel.PERFORMANCE.value, 
                       f"TIMING {name}: {duration:.3f}s", 
                       extra={"metric_name": name, "duration": duration, **context})
    
    def log_diagnostic(self, message: str, **context):
        """Log diagnostic information"""
        diag_logger = logging.getLogger("diagnostic")
        diag_logger.log(LogLevel.DIAGNOSTIC.value, message, extra=context)
    
    def create_diagnostic_report(self) -> str:
        """Create comprehensive diagnostic report"""
        diagnostic_info = self.diagnostic_collector.collect_diagnostics()
        performance_summary = self.performance_logger.get_summary()
        
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "diagnostics": asdict(diagnostic_info),
            "performance": performance_summary,
            "log_files": [
                {
                    "name": log_file.name,
                    "size": log_file.stat().st_size,
                    "modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                }
                for log_file in self.log_dir.glob("*.log")
            ]
        }
        
        return json.dumps(report, indent=2)
    
    def save_diagnostic_report(self, filename: Optional[str] = None) -> Path:
        """Save diagnostic report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"diagnostic_report_{timestamp}.json"
        
        report_path = self.log_dir / filename
        report_content = self.create_diagnostic_report()
        
        report_path.write_text(report_content)
        logger.info(f"Diagnostic report saved to: {report_path}")
        
        return report_path
    
    def cleanup_old_logs(self, days: int = 30):
        """Clean up old log files"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        cleaned_count = 0
        for log_file in self.log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    cleaned_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete old log file {log_file}: {e}")
        
        logger.info(f"Cleaned up {cleaned_count} old log files")
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get logging statistics"""
        log_files = list(self.log_dir.glob("*.log*"))
        total_size = sum(f.stat().st_size for f in log_files)
        
        return {
            "log_directory": str(self.log_dir),
            "log_files_count": len(log_files),
            "total_size_mb": total_size / (1024 * 1024),
            "performance_metrics_count": len(self.performance_logger.metrics),
            "log_files": [
                {
                    "name": f.name,
                    "size_mb": f.stat().st_size / (1024 * 1024),
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                }
                for f in log_files
            ]
        }


# Global logging manager instance
_global_logging_manager: Optional[LoggingManager] = None


def get_logging_manager() -> LoggingManager:
    """Get or create global logging manager instance"""
    global _global_logging_manager
    
    if _global_logging_manager is None:
        _global_logging_manager = LoggingManager()
    
    return _global_logging_manager


def performance_timer(name: str, **context):
    """Decorator for timing function execution"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                get_logging_manager().log_performance(name, duration, **context)
                return result
            except Exception as e:
                duration = time.time() - start_time
                get_logging_manager().log_performance(
                    name, duration, error=str(e), **context
                )
                raise
        return wrapper
    return decorator


def main():
    """Test the logging and diagnostics system"""
    logging_manager = LoggingManager()
    
    # Test performance logging
    with performance_timer("test_operation"):
        time.sleep(0.1)
    
    # Test diagnostic collection
    print("Creating diagnostic report...")
    report_path = logging_manager.save_diagnostic_report()
    print(f"Report saved to: {report_path}")
    
    # Test log statistics
    stats = logging_manager.get_log_statistics()
    print(f"Log statistics: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    main()