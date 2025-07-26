#!/usr/bin/env python3
"""
Notification Manager for Voice Control Application

Provides comprehensive notification system for status updates, errors,
and user feedback through system tray notifications.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import threading
import time

try:
    from PyQt5.QtWidgets import QSystemTrayIcon, QApplication
    from PyQt5.QtCore import QTimer, QObject, pyqtSignal
    from PyQt5.QtGui import QIcon
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    # Create dummy classes for type hints when PyQt5 is not available
    class QSystemTrayIcon:
        pass
    class QObject:
        pass

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    VOICE_COMMAND = "voice_command"
    STATUS_UPDATE = "status_update"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class Notification:
    """Individual notification object"""
    
    def __init__(self, title: str, message: str, 
                 notification_type: NotificationType = NotificationType.INFO,
                 priority: NotificationPriority = NotificationPriority.NORMAL,
                 duration: int = 3000, persistent: bool = False):
        self.id = id(self)
        self.title = title
        self.message = message
        self.type = notification_type
        self.priority = priority
        self.duration = duration
        self.persistent = persistent
        self.timestamp = datetime.now()
        self.shown = False
        self.dismissed = False
    
    def __str__(self):
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {self.title}: {self.message}"


class NotificationManager(QObject if PYQT_AVAILABLE else object):
    """Manages system tray notifications with history and queuing"""
    
    # PyQt signals for notification events
    if PYQT_AVAILABLE:
        notification_shown = pyqtSignal(object)
        notification_dismissed = pyqtSignal(object)
    
    def __init__(self, tray_icon: Optional[QSystemTrayIcon] = None):
        if PYQT_AVAILABLE:
            super().__init__()
        
        self.tray_icon = tray_icon
        self.notification_queue: List[Notification] = []
        self.notification_history: List[Notification] = []
        self.max_history_size = 100
        self.is_showing_notification = False
        self.current_notification = None
        
        # Configuration
        self.notifications_enabled = True
        self.max_queue_size = 10
        self.rate_limit_window = timedelta(seconds=5)
        self.max_notifications_per_window = 3
        self.recent_notifications = []
        
        # Setup processing timer
        if PYQT_AVAILABLE:
            self.process_timer = QTimer()
            self.process_timer.timeout.connect(self._process_queue)
            self.process_timer.start(500)  # Process every 500ms
        else:
            # Fallback for non-Qt environments
            self._start_background_processor()
    
    def _start_background_processor(self):
        """Start background thread for processing notifications (non-Qt fallback)"""
        def processor():
            while True:
                try:
                    self._process_queue()
                    time.sleep(0.5)
                except Exception as e:
                    logger.error(f"Notification processor error: {e}")
        
        processor_thread = threading.Thread(target=processor, daemon=True)
        processor_thread.start()
    
    def show_notification(self, title: str, message: str,
                         notification_type: NotificationType = NotificationType.INFO,
                         priority: NotificationPriority = NotificationPriority.NORMAL,
                         duration: int = 3000, persistent: bool = False) -> bool:
        """Show a notification (queued if necessary)"""
        try:
            # Check if notifications are enabled
            if not self.notifications_enabled:
                logger.debug(f"Notifications disabled, skipping: {title}")
                return False
            
            # Check rate limiting
            if not self._check_rate_limit():
                logger.warning("Notification rate limit exceeded, skipping")
                return False
            
            # Create notification
            notification = Notification(
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                duration=duration,
                persistent=persistent
            )
            
            # Add to queue
            self._add_to_queue(notification)
            
            logger.debug(f"Notification queued: {notification}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to show notification: {e}")
            return False
    
    def show_success(self, title: str, message: str, duration: int = 2000):
        """Show success notification"""
        return self.show_notification(
            title, message, 
            NotificationType.SUCCESS, 
            NotificationPriority.NORMAL,
            duration
        )
    
    def show_error(self, title: str, message: str, duration: int = 5000):
        """Show error notification"""
        return self.show_notification(
            title, message,
            NotificationType.ERROR,
            NotificationPriority.HIGH,
            duration
        )
    
    def show_warning(self, title: str, message: str, duration: int = 4000):
        """Show warning notification"""
        return self.show_notification(
            title, message,
            NotificationType.WARNING,
            NotificationPriority.NORMAL,
            duration
        )
    
    def show_voice_command_feedback(self, command: str, result: str = "Executed"):
        """Show feedback for voice commands"""
        return self.show_notification(
            "Voice Command",
            f"'{command}' - {result}",
            NotificationType.VOICE_COMMAND,
            NotificationPriority.LOW,
            duration=1500
        )
    
    def show_status_update(self, status: str, details: str = ""):
        """Show status update notification"""
        message = f"{status}"
        if details:
            message += f" - {details}"
        
        return self.show_notification(
            "Voice Control",
            message,
            NotificationType.STATUS_UPDATE,
            NotificationPriority.LOW,
            duration=2000
        )
    
    def _add_to_queue(self, notification: Notification):
        """Add notification to queue with priority handling"""
        # Remove old notifications if queue is full
        if len(self.notification_queue) >= self.max_queue_size:
            # Remove lowest priority notifications first
            self.notification_queue.sort(key=lambda n: n.priority.value, reverse=True)
            removed = self.notification_queue.pop()
            logger.debug(f"Queue full, removed notification: {removed.title}")
        
        # Insert based on priority
        inserted = False
        for i, queued_notification in enumerate(self.notification_queue):
            if notification.priority.value > queued_notification.priority.value:
                self.notification_queue.insert(i, notification)
                inserted = True
                break
        
        if not inserted:
            self.notification_queue.append(notification)
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        now = datetime.now()
        
        # Clean old notifications from recent list
        self.recent_notifications = [
            n for n in self.recent_notifications
            if now - n.timestamp < self.rate_limit_window
        ]
        
        # Check if we're under the limit
        return len(self.recent_notifications) < self.max_notifications_per_window
    
    def _process_queue(self):
        """Process notification queue"""
        try:
            # Skip if currently showing a notification
            if self.is_showing_notification or not self.notification_queue:
                return
            
            # Get next notification
            notification = self.notification_queue.pop(0)
            
            # Show the notification
            self._show_notification_now(notification)
            
        except Exception as e:
            logger.error(f"Error processing notification queue: {e}")
    
    def _show_notification_now(self, notification: Notification):
        """Actually display the notification"""
        try:
            self.is_showing_notification = True
            self.current_notification = notification
            
            # Add to recent notifications for rate limiting
            self.recent_notifications.append(notification)
            
            # Add to history
            self._add_to_history(notification)
            
            # Show based on available system
            if PYQT_AVAILABLE and self.tray_icon:
                self._show_qt_notification(notification)
            else:
                self._show_fallback_notification(notification)
            
            # Mark as shown
            notification.shown = True
            
            # Emit signal if available
            if PYQT_AVAILABLE:
                self.notification_shown.emit(notification)
            
            # Schedule dismissal
            if not notification.persistent:
                self._schedule_dismissal(notification)
            
            logger.debug(f"Notification shown: {notification}")
            
        except Exception as e:
            logger.error(f"Failed to show notification: {e}")
            self.is_showing_notification = False
    
    def _show_qt_notification(self, notification: Notification):
        """Show notification using Qt system tray"""
        # Map notification types to Qt icons
        icon_map = {
            NotificationType.INFO: QSystemTrayIcon.Information,
            NotificationType.SUCCESS: QSystemTrayIcon.Information,
            NotificationType.WARNING: QSystemTrayIcon.Warning,
            NotificationType.ERROR: QSystemTrayIcon.Critical,
            NotificationType.VOICE_COMMAND: QSystemTrayIcon.Information,
            NotificationType.STATUS_UPDATE: QSystemTrayIcon.Information,
        }
        
        icon = icon_map.get(notification.type, QSystemTrayIcon.Information)
        
        self.tray_icon.showMessage(
            notification.title,
            notification.message,
            icon,
            notification.duration
        )
    
    def _show_fallback_notification(self, notification: Notification):
        """Show notification using fallback method (console log)"""
        type_prefix = {
            NotificationType.INFO: "ℹ️",
            NotificationType.SUCCESS: "✅",
            NotificationType.WARNING: "⚠️",
            NotificationType.ERROR: "❌",
            NotificationType.VOICE_COMMAND: "🎤",
            NotificationType.STATUS_UPDATE: "📊",
        }
        
        prefix = type_prefix.get(notification.type, "ℹ️")
        print(f"{prefix} {notification.title}: {notification.message}")
    
    def _schedule_dismissal(self, notification: Notification):
        """Schedule notification dismissal"""
        if PYQT_AVAILABLE:
            dismiss_timer = QTimer()
            dismiss_timer.setSingleShot(True)
            dismiss_timer.timeout.connect(lambda: self._dismiss_notification(notification))
            dismiss_timer.start(notification.duration)
        else:
            # Fallback for non-Qt
            def dismiss_later():
                time.sleep(notification.duration / 1000.0)
                self._dismiss_notification(notification)
            
            dismiss_thread = threading.Thread(target=dismiss_later, daemon=True)
            dismiss_thread.start()
    
    def _dismiss_notification(self, notification: Notification):
        """Dismiss a notification"""
        try:
            if self.current_notification == notification:
                self.is_showing_notification = False
                self.current_notification = None
            
            notification.dismissed = True
            
            # Emit signal if available
            if PYQT_AVAILABLE:
                self.notification_dismissed.emit(notification)
            
            logger.debug(f"Notification dismissed: {notification.title}")
            
        except Exception as e:
            logger.error(f"Error dismissing notification: {e}")
    
    def _add_to_history(self, notification: Notification):
        """Add notification to history"""
        self.notification_history.append(notification)
        
        # Trim history if too large
        if len(self.notification_history) > self.max_history_size:
            self.notification_history.pop(0)
    
    def get_notification_history(self, limit: int = 20) -> List[Notification]:
        """Get recent notification history"""
        return self.notification_history[-limit:]
    
    def clear_history(self):
        """Clear notification history"""
        self.notification_history.clear()
        logger.info("Notification history cleared")
    
    def enable_notifications(self):
        """Enable notifications"""
        self.notifications_enabled = True
        logger.info("Notifications enabled")
    
    def disable_notifications(self):
        """Disable notifications"""
        self.notifications_enabled = False
        logger.info("Notifications disabled")
    
    def clear_queue(self):
        """Clear pending notifications"""
        cleared_count = len(self.notification_queue)
        self.notification_queue.clear()
        logger.info(f"Cleared {cleared_count} pending notifications")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            "queue_size": len(self.notification_queue),
            "is_showing": self.is_showing_notification,
            "current_notification": str(self.current_notification) if self.current_notification else None,
            "notifications_enabled": self.notifications_enabled,
            "history_size": len(self.notification_history)
        }
    
    def set_tray_icon(self, tray_icon: QSystemTrayIcon):
        """Set or update the tray icon reference"""
        self.tray_icon = tray_icon
        logger.debug("Tray icon reference updated")


# Global notification manager instance
_notification_manager = None


def get_notification_manager(tray_icon: Optional[QSystemTrayIcon] = None) -> NotificationManager:
    """Get or create global notification manager instance"""
    global _notification_manager
    
    if _notification_manager is None:
        _notification_manager = NotificationManager(tray_icon)
    elif tray_icon and _notification_manager.tray_icon != tray_icon:
        _notification_manager.set_tray_icon(tray_icon)
    
    return _notification_manager


def main():
    """Test the notification manager"""
    import sys
    
    logging.basicConfig(level=logging.DEBUG)
    
    if PYQT_AVAILABLE:
        app = QApplication(sys.argv)
        
        # Create a test tray icon
        tray_icon = QSystemTrayIcon()
        tray_icon.show()
        
        # Create notification manager
        notif_mgr = NotificationManager(tray_icon)
        
        # Test notifications
        notif_mgr.show_success("Test Success", "This is a success notification")
        notif_mgr.show_error("Test Error", "This is an error notification")
        notif_mgr.show_warning("Test Warning", "This is a warning notification")
        notif_mgr.show_voice_command_feedback("test command", "executed successfully")
        notif_mgr.show_status_update("Listening", "Voice recognition active")
        
        # Print status
        print("Queue status:", notif_mgr.get_queue_status())
        
        app.exec_()
    else:
        print("PyQt5 not available, testing fallback mode...")
        
        notif_mgr = NotificationManager()
        
        notif_mgr.show_success("Test Success", "This is a success notification")
        notif_mgr.show_error("Test Error", "This is an error notification")
        
        time.sleep(5)


if __name__ == "__main__":
    main()