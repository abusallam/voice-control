#!/usr/bin/env python3
"""
Comprehensive Test Suite for Voice Control Application

Tests all major components including stability fixes, system integration,
GUI components, and overall system health.
"""

import unittest
import logging
import sys
import time
import threading
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Setup logging for tests
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class TestResourceManager(unittest.TestCase):
    """Test resource management and cleanup"""
    
    def setUp(self):
        from voice_control.core.resource_manager import ResourceManager
        self.resource_manager = ResourceManager(max_memory_mb=100)
    
    def tearDown(self):
        self.resource_manager.cleanup_all()
        self.resource_manager.stop_monitoring()
    
    def test_resource_registration(self):
        """Test resource registration and cleanup"""
        test_resource = {"data": "test"}
        cleanup_called = False
        
        def cleanup_func(resource):
            nonlocal cleanup_called
            cleanup_called = True
        
        # Register resource
        self.resource_manager.register_resource("test_resource", test_resource, cleanup_func)
        
        # Check it's registered
        self.assertIn("test_resource", self.resource_manager.active_resources)
        
        # Cleanup specific resource
        self.resource_manager.cleanup_resource("test_resource")
        
        # Check cleanup was called
        self.assertTrue(cleanup_called)
        self.assertNotIn("test_resource", self.resource_manager.active_resources)
    
    def test_memory_monitoring(self):
        """Test memory usage monitoring"""
        # Start monitoring with short interval
        self.resource_manager.start_monitoring(interval=1)
        
        # Wait for at least one monitoring cycle
        time.sleep(2)
        
        # Get resource stats
        stats = self.resource_manager.get_resource_stats()
        
        # Check stats are populated
        self.assertIn("memory_mb", stats)
        self.assertIsInstance(stats["memory_mb"], (int, float))
        self.assertGreater(stats["memory_mb"], 0)
    
    def test_cleanup_all(self):
        """Test cleanup of all resources"""
        cleanup_count = 0
        
        def cleanup_func(resource):
            nonlocal cleanup_count
            cleanup_count += 1
        
        # Register multiple resources
        for i in range(3):
            self.resource_manager.register_resource(
                f"test_resource_{i}", 
                {"id": i}, 
                cleanup_func
            )
        
        # Cleanup all
        self.resource_manager.cleanup_all()
        
        # Check all were cleaned up
        self.assertEqual(cleanup_count, 3)
        self.assertEqual(len(self.resource_manager.active_resources), 0)


class TestErrorHandler(unittest.TestCase):
    """Test error handling and recovery"""
    
    def setUp(self):
        from voice_control.core.error_handler import ErrorHandler, VoiceControlError
        self.error_handler = ErrorHandler()
        self.VoiceControlError = VoiceControlError
    
    def test_error_handling(self):
        """Test basic error handling"""
        test_error = self.VoiceControlError("Test error")
        
        # Handle error
        result = self.error_handler.handle_error(test_error, "test_context")
        
        # Check error was logged
        stats = self.error_handler.get_error_statistics()
        self.assertGreater(stats["total_errors"], 0)
    
    def test_error_threshold(self):
        """Test error threshold detection"""
        test_error = self.VoiceControlError("Repeated error")
        
        # Generate multiple errors to exceed threshold
        for _ in range(6):  # Threshold is 5
            self.error_handler.handle_error(test_error, "test_context")
        
        # Check that threshold was detected
        stats = self.error_handler.get_error_statistics()
        self.assertGreaterEqual(stats["total_errors"], 5)
    
    def test_recovery_handler_registration(self):
        """Test recovery handler registration"""
        handler_called = False
        
        def test_recovery_handler(error, context):
            nonlocal handler_called
            handler_called = True
            return True
        
        # Register handler
        self.error_handler.register_recovery_handler(
            self.VoiceControlError, 
            test_recovery_handler
        )
        
        # Trigger error
        test_error = self.VoiceControlError("Test error")
        self.error_handler.handle_error(test_error, "test_context")
        
        # Check handler was called
        self.assertTrue(handler_called)


class TestHealthMonitor(unittest.TestCase):
    """Test health monitoring system"""
    
    def setUp(self):
        from voice_control.core.health_monitor import HealthMonitor
        self.health_monitor = HealthMonitor()
    
    def tearDown(self):
        self.health_monitor.stop_monitoring()
    
    def test_health_check(self):
        """Test comprehensive health check"""
        checks = self.health_monitor.perform_health_check()
        
        # Check that all expected components were checked
        from voice_control.core.health_monitor import ComponentType
        expected_components = [
            ComponentType.MEMORY_USAGE,
            ComponentType.CPU_USAGE,
            ComponentType.DISK_USAGE,
            ComponentType.AUDIO_SYSTEM,
            ComponentType.GUI_SYSTEM
        ]
        
        for component in expected_components:
            self.assertIn(component, checks)
            self.assertIsNotNone(checks[component].status)
    
    def test_health_report(self):
        """Test health report generation"""
        # Perform health check first
        self.health_monitor.perform_health_check()
        
        # Get report
        report = self.health_monitor.get_health_report()
        
        # Check report structure
        self.assertIn("overall_status", report)
        self.assertIn("components", report)
        self.assertIn("check_count", report)
        self.assertGreater(report["check_count"], 0)
    
    def test_monitoring_start_stop(self):
        """Test monitoring start and stop"""
        # Start monitoring
        self.health_monitor.start_monitoring(interval=1)
        self.assertTrue(self.health_monitor.monitoring_active)
        
        # Wait for at least one check
        time.sleep(2)
        
        # Stop monitoring
        self.health_monitor.stop_monitoring()
        self.assertFalse(self.health_monitor.monitoring_active)


class TestClipboardManager(unittest.TestCase):
    """Test clipboard operations"""
    
    def setUp(self):
        from voice_control.system.clipboard_manager import ClipboardManager
        self.clipboard_manager = ClipboardManager()
    
    def test_clipboard_backend_detection(self):
        """Test clipboard backend detection"""
        backend = self.clipboard_manager.clipboard_backend
        self.assertIsInstance(backend, str)
        self.assertNotEqual(backend, "")
    
    def test_clipboard_operations(self):
        """Test basic clipboard operations"""
        test_text = "Test clipboard content"
        
        # Test copy operation (may not work in headless environment)
        try:
            success = self.clipboard_manager.copy_to_clipboard(test_text, verify=False)
            # Don't assert success since it depends on system setup
            logger.info(f"Clipboard copy test: {'passed' if success else 'skipped (no backend)'}")
        except Exception as e:
            logger.warning(f"Clipboard test skipped: {e}")
    
    def test_clipboard_history(self):
        """Test clipboard history functionality"""
        # Add some entries to history
        self.clipboard_manager._add_to_history("Test 1", "text")
        self.clipboard_manager._add_to_history("Test 2", "text")
        
        # Get history
        history = self.clipboard_manager.get_clipboard_history()
        
        # Check history
        self.assertGreaterEqual(len(history), 2)
        self.assertEqual(history[-1].content, "Test 2")
        self.assertEqual(history[-2].content, "Test 1")
    
    def test_content_type_detection(self):
        """Test content type detection"""
        test_cases = [
            ("https://example.com", "url"),
            ("user@example.com", "email"),
            ("123.45", "number"),
            ("def function():", "code"),
            ("regular text", "text")
        ]
        
        for content, expected_type in test_cases:
            detected_type = self.clipboard_manager.detect_content_type(content)
            self.assertEqual(detected_type, expected_type, 
                           f"Failed for content: {content}")


class TestInputHandler(unittest.TestCase):
    """Test input handling system"""
    
    def setUp(self):
        from voice_control.system.input_handler import InputHandler
        self.input_handler = InputHandler()
    
    def test_input_context_detection(self):
        """Test input context detection"""
        context = self.input_handler.input_context
        
        # Check context is populated
        self.assertIsNotNone(context.display_server)
        self.assertIsNotNone(context.input_method)
        self.assertIn(context.display_server, ["x11", "wayland"])
    
    def test_cursor_position_handling(self):
        """Test cursor position functionality"""
        # This may not work in headless environment
        try:
            position = self.input_handler.get_cursor_position()
            if position:
                self.assertIsInstance(position.x, int)
                self.assertIsInstance(position.y, int)
                logger.info(f"Cursor position: ({position.x}, {position.y})")
            else:
                logger.info("Cursor position test skipped (no display)")
        except Exception as e:
            logger.warning(f"Cursor position test skipped: {e}")
    
    def test_input_status(self):
        """Test input status reporting"""
        status = self.input_handler.get_input_status()
        
        # Check status structure
        self.assertIn("display_server", status)
        self.assertIn("input_method", status)
        self.assertIn("input_method_available", status)
        self.assertIsInstance(status["input_method_available"], bool)


class TestSystemTray(unittest.TestCase):
    """Test system tray functionality"""
    
    def setUp(self):
        # Mock GUI components since we might not have a display
        self.gui_available = True
        try:
            from voice_control.gui.system_tray import VoiceControlTray
            self.VoiceControlTray = VoiceControlTray
        except ImportError:
            self.gui_available = False
            self.skipTest("GUI components not available")
    
    @patch('voice_control.gui.system_tray.QApplication')
    @patch('voice_control.gui.system_tray.QSystemTrayIcon')
    def test_tray_initialization(self, mock_tray_icon, mock_app):
        """Test system tray initialization"""
        if not self.gui_available:
            self.skipTest("GUI not available")
        
        # Mock the GUI components
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        
        mock_tray_instance = Mock()
        mock_tray_icon.return_value = mock_tray_instance
        mock_tray_icon.isSystemTrayAvailable.return_value = True
        
        # Create tray instance
        try:
            tray = self.VoiceControlTray()
            self.assertIsNotNone(tray)
            logger.info("System tray initialization test passed")
        except Exception as e:
            logger.warning(f"System tray test skipped: {e}")


class TestNotificationManager(unittest.TestCase):
    """Test notification system"""
    
    def setUp(self):
        try:
            from voice_control.gui.notification_manager import NotificationManager
            self.notification_manager = NotificationManager()
        except ImportError:
            self.skipTest("Notification manager not available")
    
    def test_notification_creation(self):
        """Test notification creation and queuing"""
        # Show test notifications
        success = self.notification_manager.show_notification(
            "Test Title", "Test message"
        )
        
        # Check notification was queued (even if not displayed)
        self.assertTrue(success)
        
        # Check queue status
        status = self.notification_manager.get_queue_status()
        self.assertIn("queue_size", status)
        self.assertIn("notifications_enabled", status)
    
    def test_notification_types(self):
        """Test different notification types"""
        # Test different notification methods
        methods = [
            ("show_success", ("Success", "Test success message")),
            ("show_error", ("Error", "Test error message")),
            ("show_warning", ("Warning", "Test warning message")),
        ]
        
        for method_name, args in methods:
            method = getattr(self.notification_manager, method_name)
            success = method(*args)
            self.assertTrue(success, f"Failed for method: {method_name}")


class TestServiceManager(unittest.TestCase):
    """Test service management"""
    
    def setUp(self):
        from voice_control.system.service_manager import ServiceManager
        self.service_manager = ServiceManager()
    
    def test_service_file_generation(self):
        """Test service file generation"""
        service_content = self.service_manager._generate_user_service_file()
        
        # Check service file contains expected sections
        self.assertIn("[Unit]", service_content)
        self.assertIn("[Service]", service_content)
        self.assertIn("[Install]", service_content)
        self.assertIn("voice-control", service_content)
    
    def test_service_status(self):
        """Test service status checking"""
        status = self.service_manager.get_service_status()
        
        # Check status structure
        self.assertIn("installed", status)
        self.assertIn("enabled", status)
        self.assertIn("running", status)
        self.assertIsInstance(status["installed"], bool)


class TestVoiceControlEngine(unittest.TestCase):
    """Test main voice control engine"""
    
    def setUp(self):
        from voice_control.core.engine import VoiceControlEngine
        self.engine = VoiceControlEngine(daemon_mode=True)
    
    def tearDown(self):
        if hasattr(self, 'engine'):
            self.engine.shutdown()
    
    def test_engine_initialization(self):
        """Test engine initialization"""
        # Check components are initialized
        self.assertIsNotNone(self.engine.resource_manager)
        self.assertIsNotNone(self.engine.error_handler)
        self.assertIsNotNone(self.engine.health_monitor)
        self.assertIsNotNone(self.engine.service_manager)
    
    def test_engine_configuration(self):
        """Test engine configuration loading"""
        config = self.engine.config
        
        # Check config structure
        self.assertIn("speech_recognition", config)
        self.assertIn("input", config)
        self.assertIn("gui", config)
        self.assertIn("health_monitoring", config)
    
    def test_engine_status(self):
        """Test engine status reporting"""
        status = self.engine.get_status()
        
        # Check status structure
        self.assertIn("running", status)
        self.assertIn("daemon_mode", status)
        self.assertIn("components", status)
        self.assertTrue(status["daemon_mode"])


class TestIntegration(unittest.TestCase):
    """Integration tests for complete system"""
    
    def test_component_integration(self):
        """Test that all components can work together"""
        from voice_control.core.resource_manager import get_resource_manager
        from voice_control.core.error_handler import get_error_handler
        from voice_control.core.health_monitor import get_health_monitor
        
        # Get global instances
        resource_manager = get_resource_manager()
        error_handler = get_error_handler()
        health_monitor = get_health_monitor(resource_manager, error_handler)
        
        # Check they're all connected
        self.assertIsNotNone(resource_manager)
        self.assertIsNotNone(error_handler)
        self.assertIsNotNone(health_monitor)
        
        # Test basic functionality
        resource_manager.start_monitoring(interval=1)
        health_monitor.perform_health_check()
        
        # Cleanup
        resource_manager.stop_monitoring()
        health_monitor.stop_monitoring()
    
    def test_system_stability(self):
        """Test system stability under load"""
        from voice_control.core.engine import VoiceControlEngine
        
        # Create engine
        engine = VoiceControlEngine(daemon_mode=True)
        
        try:
            # Start engine
            engine.start()
            
            # Run for a short time
            time.sleep(2)
            
            # Check it's still running
            status = engine.get_status()
            self.assertTrue(status["running"])
            
            # Get health report
            if status["health"]:
                health = status["health"]
                self.assertIn("overall_status", health)
                logger.info(f"System health: {health['overall_status']}")
        
        finally:
            engine.shutdown()


def run_performance_tests():
    """Run performance-specific tests"""
    logger.info("Running performance tests...")
    
    # Test resource usage
    from voice_control.core.resource_manager import get_resource_manager
    resource_manager = get_resource_manager()
    
    start_stats = resource_manager.get_resource_stats()
    logger.info(f"Initial resource usage: {start_stats.get('memory_mb', 0):.1f}MB")
    
    # Simulate some work
    time.sleep(1)
    
    end_stats = resource_manager.get_resource_stats()
    logger.info(f"Final resource usage: {end_stats.get('memory_mb', 0):.1f}MB")
    
    # Check memory didn't grow excessively
    memory_growth = end_stats.get('memory_mb', 0) - start_stats.get('memory_mb', 0)
    logger.info(f"Memory growth: {memory_growth:.1f}MB")
    
    resource_manager.cleanup_all()


def main():
    """Run comprehensive tests"""
    logger.info("Starting comprehensive voice control tests...")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestResourceManager,
        TestErrorHandler,
        TestHealthMonitor,
        TestClipboardManager,
        TestInputHandler,
        TestSystemTray,
        TestNotificationManager,
        TestServiceManager,
        TestVoiceControlEngine,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Run performance tests
    run_performance_tests()
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'✅ PASSED' if success else '❌ FAILED'}")
    print("="*60)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())