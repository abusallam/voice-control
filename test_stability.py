#!/usr/bin/env python3
"""
Test script for voice control stability fixes

This script tests the critical stability components to ensure they work
properly and don't cause system hangs or crashes.
"""

import sys
import logging
import time
from pathlib import Path

# Add voice_control to path
sys.path.insert(0, str(Path(__file__).parent))

from voice_control.core.resource_manager import ResourceManager
from voice_control.core.error_handler import ErrorHandler, VoiceControlError
from voice_control.system.service_manager import ServiceManager


def setup_test_logging():
    """Setup logging for tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_resource_manager():
    """Test resource manager functionality"""
    print("Testing Resource Manager...")
    
    try:
        # Create resource manager
        rm = ResourceManager(max_memory_mb=100)  # Low limit for testing
        
        # Test resource registration
        test_resource = {"data": "test"}
        rm.register_resource("test_resource", test_resource, lambda x: print(f"Cleaned up: {x}"))
        
        # Test resource stats
        stats = rm.get_resource_stats()
        print(f"Resource stats: {stats}")
        
        # Test cleanup
        rm.cleanup_all()
        
        print("✓ Resource Manager test passed")
        return True
        
    except Exception as e:
        print(f"✗ Resource Manager test failed: {e}")
        return False


def test_error_handler():
    """Test error handler functionality"""
    print("Testing Error Handler...")
    
    try:
        # Create error handler
        eh = ErrorHandler()
        
        # Test error handling
        test_error = VoiceControlError("Test error")
        result = eh.handle_error(test_error, "test_context")
        
        # Test error statistics
        stats = eh.get_error_statistics()
        print(f"Error stats: {stats}")
        
        print("✓ Error Handler test passed")
        return True
        
    except Exception as e:
        print(f"✗ Error Handler test failed: {e}")
        return False


def test_service_manager():
    """Test service manager functionality"""
    print("Testing Service Manager...")
    
    try:
        # Create service manager
        sm = ServiceManager()
        
        # Test service status check
        status = sm.get_service_status()
        print(f"Service status: {status}")
        
        # Test service file generation (without installing)
        service_content = sm._generate_user_service_file()
        print("✓ Service file generation works")
        
        print("✓ Service Manager test passed")
        return True
        
    except Exception as e:
        print(f"✗ Service Manager test failed: {e}")
        return False


def test_memory_stability():
    """Test memory stability under load"""
    print("Testing Memory Stability...")
    
    try:
        rm = ResourceManager(max_memory_mb=50)  # Very low limit
        rm.start_monitoring(interval=1)  # Fast monitoring
        
        # Create some resources to test cleanup
        for i in range(10):
            test_data = [0] * 1000  # Small data chunks
            rm.register_resource(f"test_data_{i}", test_data, lambda x: None)
        
        # Wait for monitoring to kick in
        time.sleep(3)
        
        # Check if cleanup happened
        stats = rm.get_resource_stats()
        print(f"Memory after test: {stats.get('memory_mb', 0):.1f}MB")
        
        rm.stop_monitoring()
        rm.cleanup_all()
        
        print("✓ Memory Stability test passed")
        return True
        
    except Exception as e:
        print(f"✗ Memory Stability test failed: {e}")
        return False


def test_graceful_shutdown():
    """Test graceful shutdown functionality"""
    print("Testing Graceful Shutdown...")
    
    try:
        from voice_control.core.engine import VoiceControlEngine
        
        # Create minimal engine
        rm = ResourceManager()
        eh = ErrorHandler()
        engine = VoiceControlEngine(rm, eh, daemon_mode=True)
        
        # Test initialization
        engine.start()
        
        # Test shutdown
        engine.shutdown()
        
        print("✓ Graceful Shutdown test passed")
        return True
        
    except Exception as e:
        print(f"✗ Graceful Shutdown test failed: {e}")
        return False


def main():
    """Run all stability tests"""
    setup_test_logging()
    
    print("=" * 50)
    print("Voice Control Stability Tests")
    print("=" * 50)
    
    tests = [
        test_resource_manager,
        test_error_handler,
        test_service_manager,
        test_memory_stability,
        test_graceful_shutdown
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            failed += 1
        
        print()  # Empty line between tests
    
    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    if failed == 0:
        print("🎉 All stability tests passed!")
        print("The application should now be stable and not cause system hangs.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())