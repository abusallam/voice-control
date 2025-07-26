#!/usr/bin/env python3
"""
Installation verification script for Voice Control

This script verifies that all required dependencies are installed
and the voice control system is ready to use.
"""

import sys
import importlib
import logging
import subprocess
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def check_python_version():
    """Check if Python version is compatible"""
    logger.info("Checking Python version...")
    
    if sys.version_info < (3, 8):
        logger.error(f"✗ Python 3.8+ required, found {sys.version}")
        return False
    
    logger.info(f"✓ Python {sys.version.split()[0]}")
    return True


def check_core_dependencies():
    """Check if core dependencies are installed"""
    logger.info("Checking core dependencies...")
    
    core_packages = [
        'numpy',
        'psutil',
        'soundfile',
        'pyaudio',
        'PIL',  # Pillow
        'pynput',
    ]
    
    missing_packages = []
    
    for package in core_packages:
        try:
            importlib.import_module(package)
            logger.info(f"✓ {package}")
        except ImportError:
            logger.error(f"✗ {package} (required)")
            missing_packages.append(package)
    
    # Check speech recognition dependencies
    speech_packages = [
        'speech_recognition',
        'whisper',
    ]
    
    for package in speech_packages:
        try:
            importlib.import_module(package)
            logger.info(f"✓ {package}")
        except ImportError:
            logger.error(f"✗ {package} (required for speech recognition)")
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        logger.error("Install with: pip install -r requirements.txt")
        return False
    
    return True


def check_audio_system():
    """Check if audio system is working"""
    logger.info("Checking audio system...")
    
    try:
        # Check for PulseAudio
        result = subprocess.run(['pactl', 'info'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            logger.info("✓ PulseAudio detected")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    try:
        # Check for PipeWire
        result = subprocess.run(['pipewire', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            logger.info("✓ PipeWire detected")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    logger.warning("⚠ No audio system detected (PulseAudio/PipeWire)")
    logger.warning("Audio functionality may not work properly")
    return True  # Don't fail installation for this


def check_voice_control_modules():
    """Check if voice control modules are available"""
    logger.info("Checking voice control modules...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Test core modules
        from voice_control.core import engine, resource_manager, error_handler
        from voice_control.system import service_manager, autostart_manager
        
        # Test GUI modules (may fail if PyQt5 not available, which is OK)
        try:
            from voice_control.gui import system_tray, notification_manager
            logger.info("✓ Voice control modules loaded successfully (with GUI)")
        except ImportError as gui_error:
            logger.info("✓ Voice control modules loaded successfully (GUI fallback mode)")
            logger.debug(f"GUI import warning: {gui_error}")
        
        return True
        
    except ImportError as e:
        logger.error(f"✗ Voice control modules failed to load: {e}")
        return False


def check_system_integration():
    """Check system integration capabilities"""
    logger.info("Checking system integration...")
    
    # Check for systemd (user services)
    try:
        result = subprocess.run(['systemctl', '--user', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            logger.info("✓ systemd user services available")
        else:
            logger.warning("⚠ systemd user services may not be available")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        logger.warning("⚠ systemd not found - service management may not work")
    
    # Check for X11/Wayland
    display = os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')
    if display:
        logger.info("✓ Display server detected")
    else:
        logger.warning("⚠ No display server detected")
    
    return True


def run_basic_functionality_test():
    """Run basic functionality tests"""
    logger.info("Running basic functionality tests...")
    
    try:
        # Test resource manager
        from voice_control.core.resource_manager import get_resource_manager
        manager = get_resource_manager()
        logger.info("✓ Resource manager working")
        
        # Test error handler
        from voice_control.core.error_handler import get_error_handler
        handler = get_error_handler()
        logger.info("✓ Error handler working")
        
        # Test service manager
        from voice_control.system.service_manager import ServiceManager
        service_mgr = ServiceManager()
        logger.info("✓ Service manager working")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Basic functionality test failed: {e}")
        return False


def main():
    """Main verification function"""
    logger.info("=" * 60)
    logger.info("Voice Control Installation Verification")
    logger.info("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Core Dependencies", check_core_dependencies),
        ("Audio System", check_audio_system),
        ("Voice Control Modules", check_voice_control_modules),
        ("System Integration", check_system_integration),
        ("Basic Functionality", run_basic_functionality_test),
    ]
    
    passed = 0
    failed = 0
    
    for name, check_func in checks:
        logger.info(f"\n{name}:")
        logger.info("-" * len(name))
        
        try:
            if check_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"✗ {name} check crashed: {e}")
            failed += 1
    
    logger.info("\n" + "=" * 60)
    logger.info(f"Verification Results: {passed} passed, {failed} failed")
    logger.info("=" * 60)
    
    if failed == 0:
        logger.info("🎉 Installation verification successful!")
        logger.info("Voice Control is ready to use.")
        logger.info("\nNext steps:")
        logger.info("1. Start the application: voice-control")
        logger.info("2. Install as service: voice-control --service install")
        logger.info("3. Enable autostart: systemctl --user enable voice-control")
        return 0
    else:
        logger.error("⚠️ Installation verification failed.")
        logger.error("Please fix the issues above before using Voice Control.")
        return 1


if __name__ == "__main__":
    import os
    sys.exit(main())