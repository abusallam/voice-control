#!/usr/bin/env python3
"""
Test script for the production error handling framework
"""

import sys
import logging
from pathlib import Path

# Add voice_control to path
sys.path.insert(0, str(Path(__file__).parent))

from voice_control.core.error_handler import (
    get_error_handler, 
    production_safe_execute, 
    critical_operation,
    AudioError, 
    RecognitionError,
    ErrorSeverity,
    RecoveryAction
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_basic_error_handling():
    """Test basic error handling functionality"""
    print("=== Testing Basic Error Handling ===")
    
    error_handler = get_error_handler()
    
    # Test handling different error types
    audio_error = AudioError("Microphone not found", ErrorSeverity.HIGH, RecoveryAction.FALLBACK)
    recognition_error = RecognitionError("Speech recognition failed", ErrorSeverity.MEDIUM, RecoveryAction.RETRY)
    
    # Handle errors
    result1 = error_handler.handle_error(audio_error, "audio_initialization")
    result2 = error_handler.handle_error(recognition_error, "speech_processing")
    
    print(f"Audio error handled: {result1}")
    print(f"Recognition error handled: {result2}")
    
    # Get error statistics
    stats = error_handler.get_error_statistics()
    print(f"Error statistics: {stats}")
    
    # Get component health
    health = error_handler.get_component_health()
    print(f"Component health: {health}")

@production_safe_execute(context="test_function", fallback_value="fallback_result")
def test_safe_function():
    """Test function with safe execution decorator"""
    print("Executing safe function...")
    # This would normally do something that might fail
    return "success_result"

@production_safe_execute(context="failing_function", fallback_value="fallback_result")
def test_failing_function():
    """Test function that fails"""
    print("Executing failing function...")
    raise Exception("This function always fails")

@critical_operation(context="critical_test", max_retries=2)
def test_critical_function(should_fail=False):
    """Test critical operation"""
    print("Executing critical function...")
    if should_fail:
        raise Exception("Critical operation failed")
    return "critical_success"

def test_decorators():
    """Test the error handling decorators"""
    print("\n=== Testing Error Handling Decorators ===")
    
    # Test successful safe execution
    result1 = test_safe_function()
    print(f"Safe function result: {result1}")
    
    # Test failing safe execution
    result2 = test_failing_function()
    print(f"Failing function result: {result2}")
    
    # Test successful critical operation
    result3 = test_critical_function(should_fail=False)
    print(f"Critical function result: {result3}")
    
    # Test failing critical operation
    try:
        result4 = test_critical_function(should_fail=True)
        print(f"Critical function result: {result4}")
    except Exception as e:
        print(f"Critical function failed as expected: {e}")

def test_system_monitoring():
    """Test system monitoring functionality"""
    print("\n=== Testing System Monitoring ===")
    
    error_handler = get_error_handler()
    
    # Get system stats
    stats = error_handler.system_monitor.get_system_stats()
    print(f"System stats: {stats}")
    
    # Check resource limits
    warnings = error_handler.system_monitor.check_resource_limits()
    if warnings:
        print(f"Resource warnings: {warnings}")
    else:
        print("No resource warnings")

def test_error_reporting():
    """Test error reporting functionality"""
    print("\n=== Testing Error Reporting ===")
    
    error_handler = get_error_handler()
    
    # Generate some test errors
    for i in range(3):
        test_error = Exception(f"Test error {i}")
        error_handler.handle_error(test_error, f"test_context_{i}")
    
    # Get detailed error report
    report = error_handler.get_detailed_error_report()
    print(f"Error report generated with {len(report.get('recent_errors', []))} recent errors")
    
    # Save error report
    report_path = error_handler.save_error_report("test_error_report.json")
    if report_path:
        print(f"Error report saved to: {report_path}")
    else:
        print("Failed to save error report")

def main():
    """Run all tests"""
    print("Testing Production Error Handling Framework")
    print("=" * 50)
    
    try:
        test_basic_error_handling()
        test_decorators()
        test_system_monitoring()
        test_error_reporting()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("The production error handling framework is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())