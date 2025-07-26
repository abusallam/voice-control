#!/usr/bin/env python3
"""
Unit tests for core Voice Control functionality
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add voice_control to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from voice_control.core.resource_manager import get_resource_manager, ResourceManager
from voice_control.core.error_handler import get_error_handler, ErrorHandler, safe_execute
from voice_control.core.health_monitor import HealthMonitor
from voice_control.core.diagnostics import SystemDiagnostics


class TestResourceManager(unittest.TestCase):
    """Test resource management functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.manager = ResourceManager()
        
    def tearDown(self):
        """Clean up test environment"""
        self.manager.cleanup_all()
    
    def test_singleton_pattern(self):
        """Test that resource manager follows singleton pattern"""
        manager1 = get_resource_manager()
        manager2 = get_resource_manager()
        self.assertIs(manager1, manager2)
    
    def test_cleanup_handler_registration(self):
        """Test cleanup handler registration and execution"""
        cleanup_called = False
        
        def test_cleanup():
            nonlocal cleanup_called
            cleanup_called = True
        
        self.manager.add_cleanup_handler(test_cleanup)
        self.manager.cleanup_all()
        
        self.assertTrue(cleanup_called)
    
    def test_multiple_cleanup_handlers(self):
        """Test multiple cleanup handlers are called"""
        call_order = []
        
        def cleanup1():
            call_order.append(1)
        
        def cleanup2():
            call_order.append(2)
        
        self.manager.add_cleanup_handler(cleanup1)
        self.manager.add_cleanup_handler(cleanup2)
        self.manager.cleanup_all()
        
        self.assertEqual(call_order, [1, 2])
    
    def test_cleanup_handler_exception_handling(self):
        """Test that exceptions in cleanup handlers don't break cleanup"""
        cleanup_called = False
        
        def failing_cleanup():
            raise Exception("Test exception")
        
        def working_cleanup():
            nonlocal cleanup_called
            cleanup_called = True
        
        self.manager.add_cleanup_handler(failing_cleanup)
        self.manager.add_cleanup_handler(working_cleanup)
        
        # Should not raise exception
        self.manager.cleanup_all()
        
        # Working cleanup should still be called
        self.assertTrue(cleanup_called)


class TestErrorHandler(unittest.TestCase):
    """Test error handling functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.handler = ErrorHandler()
    
    def test_singleton_pattern(self):
        """Test that error handler follows singleton pattern"""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        self.assertIs(handler1, handler2)
    
    def test_error_handling(self):
        """Test basic error handling"""
        test_error = Exception("Test error")
        
        # Should not raise exception
        self.handler.handle_error(test_error, "test_context")
        
        # Check that error was recorded
        self.assertGreater(len(self.handler.error_history), 0)
    
    def test_safe_execute_decorator(self):
        """Test safe_execute decorator"""
        @safe_execute(self.handler, "test_operation")
        def test_function():
            return "success"
        
        result = test_function()
        self.assertEqual(result, "success")
    
    def test_safe_execute_with_exception(self):
        """Test safe_execute decorator with exception"""
        @safe_execute(self.handler, "test_operation")
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        self.assertIsNone(result)  # Should return None on exception
        
        # Check that error was recorded
        self.assertGreater(len(self.handler.error_history), 0)
    
    def test_error_recovery(self):
        """Test error recovery mechanisms"""
        recovery_called = False
        
        def recovery_function():
            nonlocal recovery_called
            recovery_called = True
            return "recovered"
        
        @safe_execute(self.handler, "test_operation", recovery_function)
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        self.assertEqual(result, "recovered")
        self.assertTrue(recovery_called)


class TestHealthMonitor(unittest.TestCase):
    """Test health monitoring functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.monitor = HealthMonitor()
    
    def test_health_check_basic(self):
        """Test basic health check functionality"""
        health_status = self.monitor.get_health_status()
        
        self.assertIsInstance(health_status, dict)
        self.assertIn('status', health_status)
        self.assertIn('timestamp', health_status)
    
    def test_system_resources_check(self):
        """Test system resources monitoring"""
        resources = self.monitor.check_system_resources()
        
        self.assertIsInstance(resources, dict)
        self.assertIn('cpu_percent', resources)
        self.assertIn('memory_percent', resources)
        self.assertIn('disk_usage', resources)
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_resource_thresholds(self, mock_memory, mock_cpu):
        """Test resource threshold monitoring"""
        # Mock high resource usage
        mock_cpu.return_value = 95.0
        mock_memory.return_value = Mock(percent=90.0)
        
        health_status = self.monitor.get_health_status()
        
        # Should detect high resource usage
        self.assertIn('warnings', health_status)
    
    def test_service_health_check(self):
        """Test service-specific health checks"""
        # This is a placeholder test since actual services may not be running
        service_health = self.monitor.check_service_health()
        
        self.assertIsInstance(service_health, dict)


class TestSystemDiagnostics(unittest.TestCase):
    """Test system diagnostics functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.diagnostics = SystemDiagnostics()
    
    def test_system_info_collection(self):
        """Test system information collection"""
        system_info = self.diagnostics.get_system_info()
        
        self.assertIsInstance(system_info, dict)
        self.assertIn('platform', system_info)
        self.assertIn('python_version', system_info)
        self.assertIn('architecture', system_info)
    
    def test_dependency_check(self):
        """Test dependency checking"""
        dependencies = self.diagnostics.check_dependencies()
        
        self.assertIsInstance(dependencies, dict)
        # Should at least check for basic dependencies
        self.assertIn('numpy', dependencies)
        self.assertIn('psutil', dependencies)
    
    def test_audio_system_detection(self):
        """Test audio system detection"""
        audio_info = self.diagnostics.check_audio_system()
        
        self.assertIsInstance(audio_info, dict)
        self.assertIn('audio_system', audio_info)
    
    def test_desktop_environment_detection(self):
        """Test desktop environment detection"""
        desktop_info = self.diagnostics.get_desktop_info()
        
        self.assertIsInstance(desktop_info, dict)
        self.assertIn('desktop_environment', desktop_info)
        self.assertIn('display_server', desktop_info)
    
    def test_generate_diagnostic_report(self):
        """Test diagnostic report generation"""
        report = self.diagnostics.generate_report()
        
        self.assertIsInstance(report, str)
        self.assertIn('System Information', report)
        self.assertIn('Dependencies', report)


class TestConfigurationLoading(unittest.TestCase):
    """Test configuration loading and validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'voice-control.py')
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_basic_config_loading(self):
        """Test basic configuration file loading"""
        # Create a simple config file
        config_content = '''
def voice_control_process(text):
    return text.upper()
'''
        
        with open(self.config_file, 'w') as f:
            f.write(config_content)
        
        # Test that we can load and execute the config
        # This is a basic test - actual config loading would be in the main application
        with open(self.config_file, 'r') as f:
            config_code = f.read()
        
        # Should not raise exception
        exec(config_code)
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Create an invalid config file
        invalid_config = '''
def voice_control_process(text):
    return text.invalid_method()  # This would cause runtime error
'''
        
        with open(self.config_file, 'w') as f:
            f.write(invalid_config)
        
        # Test that we can detect syntax issues
        with open(self.config_file, 'r') as f:
            config_code = f.read()
        
        # Should be able to compile (syntax check)
        try:
            compile(config_code, self.config_file, 'exec')
            syntax_valid = True
        except SyntaxError:
            syntax_valid = False
        
        self.assertTrue(syntax_valid)  # This particular example should have valid syntax


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)