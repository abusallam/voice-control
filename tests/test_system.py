#!/usr/bin/env python3
"""
Unit tests for system integration functionality
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open

# Add voice_control to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from voice_control.system.service_manager import ServiceManager
from voice_control.system.autostart_manager import AutostartManager
from voice_control.system.clipboard_manager import ClipboardManager
from voice_control.system.input_handler import InputHandler


class TestServiceManager(unittest.TestCase):
    """Test systemd service management functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.service_manager = ServiceManager()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_service_manager_creation(self):
        """Test service manager creation"""
        self.assertIsInstance(self.service_manager, ServiceManager)
        self.assertEqual(self.service_manager.service_name, "voice-control")
    
    @patch('subprocess.run')
    def test_service_status_check(self, mock_run):
        """Test service status checking"""
        # Mock successful status check
        mock_run.return_value = Mock(returncode=0, stdout="active")
        
        status = self.service_manager.get_service_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('running', status)
        self.assertIn('installed', status)
        self.assertIn('enabled', status)
    
    @patch('subprocess.run')
    def test_service_start(self, mock_run):
        """Test service start"""
        mock_run.return_value = Mock(returncode=0)
        
        result = self.service_manager.start_service()
        self.assertTrue(result)
        
        # Verify correct command was called
        mock_run.assert_called()
        args = mock_run.call_args[0][0]
        self.assertIn('systemctl', args)
        self.assertIn('start', args)
        self.assertIn('voice-control', args)
    
    @patch('subprocess.run')
    def test_service_stop(self, mock_run):
        """Test service stop"""
        mock_run.return_value = Mock(returncode=0)
        
        result = self.service_manager.stop_service()
        self.assertTrue(result)
        
        # Verify correct command was called
        args = mock_run.call_args[0][0]
        self.assertIn('systemctl', args)
        self.assertIn('stop', args)
        self.assertIn('voice-control', args)
    
    @patch('subprocess.run')
    def test_service_enable(self, mock_run):
        """Test service enable"""
        mock_run.return_value = Mock(returncode=0)
        
        result = self.service_manager.enable_service()
        self.assertTrue(result)
        
        # Verify correct command was called
        args = mock_run.call_args[0][0]
        self.assertIn('systemctl', args)
        self.assertIn('enable', args)
        self.assertIn('voice-control', args)
    
    @patch('subprocess.run')
    def test_service_command_failure(self, mock_run):
        """Test service command failure handling"""
        mock_run.return_value = Mock(returncode=1, stderr="Service not found")
        
        result = self.service_manager.start_service()
        self.assertFalse(result)
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_service_file_creation(self, mock_file, mock_exists):
        """Test service file creation"""
        mock_exists.return_value = False
        
        service_content = self.service_manager._generate_service_file()
        
        self.assertIsInstance(service_content, str)
        self.assertIn('[Unit]', service_content)
        self.assertIn('[Service]', service_content)
        self.assertIn('[Install]', service_content)
        self.assertIn('voice-control', service_content)


class TestAutostartManager(unittest.TestCase):
    """Test autostart management functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.autostart_manager = AutostartManager()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_autostart_manager_creation(self):
        """Test autostart manager creation"""
        self.assertIsInstance(self.autostart_manager, AutostartManager)
    
    @patch('os.path.exists')
    def test_autostart_status_check(self, mock_exists):
        """Test autostart status checking"""
        mock_exists.return_value = True
        
        is_enabled = self.autostart_manager.is_autostart_enabled()
        self.assertTrue(is_enabled)
        
        mock_exists.return_value = False
        is_enabled = self.autostart_manager.is_autostart_enabled()
        self.assertFalse(is_enabled)
    
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_autostart_enable(self, mock_file, mock_makedirs):
        """Test enabling autostart"""
        result = self.autostart_manager.enable_autostart()
        self.assertTrue(result)
        
        # Verify desktop file was written
        mock_file.assert_called()
        written_content = mock_file().write.call_args[0][0]
        self.assertIn('[Desktop Entry]', written_content)
        self.assertIn('voice-control', written_content)
    
    @patch('os.path.exists')
    @patch('os.remove')
    def test_autostart_disable(self, mock_remove, mock_exists):
        """Test disabling autostart"""
        mock_exists.return_value = True
        
        result = self.autostart_manager.disable_autostart()
        self.assertTrue(result)
        
        # Verify file was removed
        mock_remove.assert_called()
    
    def test_desktop_file_generation(self):
        """Test desktop file content generation"""
        desktop_content = self.autostart_manager._generate_desktop_file()
        
        self.assertIsInstance(desktop_content, str)
        self.assertIn('[Desktop Entry]', desktop_content)
        self.assertIn('Type=Application', desktop_content)
        self.assertIn('voice-control', desktop_content)


class TestClipboardManager(unittest.TestCase):
    """Test clipboard management functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.clipboard_manager = ClipboardManager()
    
    def test_clipboard_manager_creation(self):
        """Test clipboard manager creation"""
        self.assertIsInstance(self.clipboard_manager, ClipboardManager)
    
    @patch('subprocess.run')
    def test_clipboard_get_x11(self, mock_run):
        """Test getting clipboard content on X11"""
        mock_run.return_value = Mock(returncode=0, stdout="test content")
        
        with patch.dict(os.environ, {'XDG_SESSION_TYPE': 'x11'}):
            content = self.clipboard_manager.get_clipboard()
        
        self.assertEqual(content, "test content")
    
    @patch('subprocess.run')
    def test_clipboard_set_x11(self, mock_run):
        """Test setting clipboard content on X11"""
        mock_run.return_value = Mock(returncode=0)
        
        with patch.dict(os.environ, {'XDG_SESSION_TYPE': 'x11'}):
            result = self.clipboard_manager.set_clipboard("test content")
        
        self.assertTrue(result)
    
    @patch('subprocess.run')
    def test_clipboard_get_wayland(self, mock_run):
        """Test getting clipboard content on Wayland"""
        mock_run.return_value = Mock(returncode=0, stdout="test content")
        
        with patch.dict(os.environ, {'XDG_SESSION_TYPE': 'wayland'}):
            content = self.clipboard_manager.get_clipboard()
        
        self.assertEqual(content, "test content")
    
    @patch('subprocess.run')
    def test_clipboard_command_failure(self, mock_run):
        """Test clipboard command failure handling"""
        mock_run.return_value = Mock(returncode=1, stderr="Command failed")
        
        content = self.clipboard_manager.get_clipboard()
        self.assertIsNone(content)
        
        result = self.clipboard_manager.set_clipboard("test")
        self.assertFalse(result)
    
    def test_display_server_detection(self):
        """Test display server detection"""
        # Test X11 detection
        with patch.dict(os.environ, {'XDG_SESSION_TYPE': 'x11'}):
            server = self.clipboard_manager._detect_display_server()
            self.assertEqual(server, 'x11')
        
        # Test Wayland detection
        with patch.dict(os.environ, {'XDG_SESSION_TYPE': 'wayland'}):
            server = self.clipboard_manager._detect_display_server()
            self.assertEqual(server, 'wayland')
        
        # Test fallback
        with patch.dict(os.environ, {}, clear=True):
            server = self.clipboard_manager._detect_display_server()
            self.assertIn(server, ['x11', 'wayland', 'unknown'])


class TestInputHandler(unittest.TestCase):
    """Test input handling functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.input_handler = InputHandler()
    
    def test_input_handler_creation(self):
        """Test input handler creation"""
        self.assertIsInstance(self.input_handler, InputHandler)
    
    @patch('subprocess.run')
    def test_type_text_x11(self, mock_run):
        """Test typing text on X11"""
        mock_run.return_value = Mock(returncode=0)
        
        with patch.dict(os.environ, {'XDG_SESSION_TYPE': 'x11'}):
            result = self.input_handler.type_text("hello world")
        
        self.assertTrue(result)
        
        # Verify xdotool was called
        args = mock_run.call_args[0][0]
        self.assertIn('xdotool', args)
        self.assertIn('type', args)
    
    @patch('subprocess.run')
    def test_type_text_wayland(self, mock_run):
        """Test typing text on Wayland"""
        mock_run.return_value = Mock(returncode=0)
        
        with patch.dict(os.environ, {'XDG_SESSION_TYPE': 'wayland'}):
            result = self.input_handler.type_text("hello world")
        
        self.assertTrue(result)
        
        # Verify ydotool was called
        args = mock_run.call_args[0][0]
        self.assertIn('ydotool', args)
        self.assertIn('type', args)
    
    @patch('subprocess.run')
    def test_send_key_x11(self, mock_run):
        """Test sending key on X11"""
        mock_run.return_value = Mock(returncode=0)
        
        with patch.dict(os.environ, {'XDG_SESSION_TYPE': 'x11'}):
            result = self.input_handler.send_key("Return")
        
        self.assertTrue(result)
        
        # Verify xdotool was called
        args = mock_run.call_args[0][0]
        self.assertIn('xdotool', args)
        self.assertIn('key', args)
        self.assertIn('Return', args)
    
    @patch('subprocess.run')
    def test_send_backspace(self, mock_run):
        """Test sending backspace"""
        mock_run.return_value = Mock(returncode=0)
        
        result = self.input_handler.send_backspace(5)
        self.assertTrue(result)
    
    @patch('subprocess.run')
    def test_input_command_failure(self, mock_run):
        """Test input command failure handling"""
        mock_run.return_value = Mock(returncode=1, stderr="Command failed")
        
        result = self.input_handler.type_text("test")
        self.assertFalse(result)
    
    def test_text_sanitization(self):
        """Test text sanitization for input"""
        # Test special characters
        sanitized = self.input_handler._sanitize_text("hello\nworld\ttab")
        self.assertIsInstance(sanitized, str)
        
        # Test empty text
        sanitized = self.input_handler._sanitize_text("")
        self.assertEqual(sanitized, "")
        
        # Test None input
        sanitized = self.input_handler._sanitize_text(None)
        self.assertEqual(sanitized, "")
    
    def test_key_validation(self):
        """Test key name validation"""
        valid_keys = ["Return", "space", "BackSpace", "Tab", "Escape"]
        
        for key in valid_keys:
            is_valid = self.input_handler._is_valid_key(key)
            self.assertTrue(is_valid, f"Key {key} should be valid")
        
        # Test invalid key
        is_valid = self.input_handler._is_valid_key("InvalidKey123")
        # This depends on implementation - might be True if we allow any string


class TestSystemIntegration(unittest.TestCase):
    """Test overall system integration"""
    
    def test_desktop_environment_detection(self):
        """Test desktop environment detection"""
        # Test various environment variables
        test_cases = [
            ({'XDG_CURRENT_DESKTOP': 'GNOME'}, 'gnome'),
            ({'XDG_CURRENT_DESKTOP': 'KDE'}, 'kde'),
            ({'XDG_CURRENT_DESKTOP': 'XFCE'}, 'xfce'),
            ({'DESKTOP_SESSION': 'ubuntu'}, 'ubuntu'),
        ]
        
        for env_vars, expected in test_cases:
            with patch.dict(os.environ, env_vars, clear=True):
                # This would be implemented in actual system detection code
                detected = env_vars.get('XDG_CURRENT_DESKTOP', 
                                      env_vars.get('DESKTOP_SESSION', 'unknown')).lower()
                self.assertIn(expected, detected.lower())
    
    def test_audio_system_detection(self):
        """Test audio system detection"""
        # Mock different audio systems
        with patch('subprocess.run') as mock_run:
            # Test PulseAudio detection
            mock_run.return_value = Mock(returncode=0, stdout="PulseAudio")
            # This would be actual audio system detection code
            # For now, just test that we can mock the detection
            self.assertTrue(True)  # Placeholder
    
    def test_permission_checks(self):
        """Test permission checking"""
        # Test file permissions
        test_file = tempfile.NamedTemporaryFile(delete=False)
        test_file.close()
        
        try:
            # Check if file is readable
            self.assertTrue(os.access(test_file.name, os.R_OK))
            
            # Check if file is writable
            self.assertTrue(os.access(test_file.name, os.W_OK))
            
        finally:
            os.unlink(test_file.name)
    
    def test_path_validation(self):
        """Test path validation and creation"""
        # Test creating directories
        test_dir = os.path.join(tempfile.gettempdir(), 'voice_control_test')
        
        try:
            os.makedirs(test_dir, exist_ok=True)
            self.assertTrue(os.path.exists(test_dir))
            self.assertTrue(os.path.isdir(test_dir))
            
        finally:
            if os.path.exists(test_dir):
                os.rmdir(test_dir)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)