#!/usr/bin/env python3
"""
Unit tests for speech recognition functionality
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Add voice_control to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from voice_control.speech.speech_router import SpeechRecognitionRouter
from voice_control.speech.base_backend import SpeechBackend


class MockSpeechBackend(SpeechBackend):
    """Mock speech backend for testing"""
    
    def __init__(self, name="mock", should_fail=False):
        super().__init__(name)
        self.should_fail = should_fail
        self.recognition_calls = 0
        
    def initialize(self, config=None):
        """Mock initialization"""
        if self.should_fail:
            return False
        self.initialized = True
        return True
    
    def recognize(self, audio_data, sample_rate=16000):
        """Mock recognition"""
        self.recognition_calls += 1
        if self.should_fail:
            return None
        return f"mock recognition result {self.recognition_calls}"
    
    def cleanup(self):
        """Mock cleanup"""
        self.initialized = False
    
    def is_available(self):
        """Mock availability check"""
        return not self.should_fail


class TestSpeechRecognitionRouter(unittest.TestCase):
    """Test speech recognition router functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.router = SpeechRecognitionRouter()
    
    def tearDown(self):
        """Clean up test environment"""
        self.router.cleanup()
    
    def test_router_initialization(self):
        """Test router initialization"""
        self.assertIsInstance(self.router, SpeechRecognitionRouter)
        self.assertEqual(len(self.router.backends), 0)  # No backends registered by default
        self.assertIsNone(self.router.current_backend)
    
    def test_backend_registration(self):
        """Test backend registration"""
        mock_backend = MockSpeechBackend("test_backend")
        
        self.router.register_backend("test", mock_backend, is_primary=True)
        
        self.assertIn("test", self.router.backends)
        self.assertEqual(self.router.primary_backend, "test")
    
    def test_fallback_backend_registration(self):
        """Test fallback backend registration"""
        primary_backend = MockSpeechBackend("primary")
        fallback_backend = MockSpeechBackend("fallback")
        
        self.router.register_backend("primary", primary_backend, is_primary=True)
        self.router.register_backend("fallback", fallback_backend, is_fallback=True)
        
        self.assertEqual(self.router.primary_backend, "primary")
        self.assertIn("fallback", self.router.fallback_backends)
    
    def test_router_initialization_with_backends(self):
        """Test router initialization with registered backends"""
        mock_backend = MockSpeechBackend("test_backend")
        self.router.register_backend("test", mock_backend, is_primary=True)
        
        # Initialize should succeed with available backend
        result = self.router.initialize()
        self.assertTrue(result)
        self.assertEqual(self.router.current_backend, "test")
    
    def test_router_initialization_no_backends(self):
        """Test router initialization with no backends"""
        # Should fail with no backends
        result = self.router.initialize()
        self.assertFalse(result)
    
    def test_speech_recognition_success(self):
        """Test successful speech recognition"""
        mock_backend = MockSpeechBackend("test_backend")
        self.router.register_backend("test", mock_backend, is_primary=True)
        self.router.initialize()
        
        # Create mock audio data
        audio_data = np.random.rand(1000).astype(np.float32)
        
        result = self.router.recognize_speech(audio_data)
        self.assertIsNotNone(result)
        self.assertIn("mock recognition result", result)
    
    def test_speech_recognition_fallback(self):
        """Test speech recognition with fallback"""
        failing_backend = MockSpeechBackend("failing", should_fail=True)
        working_backend = MockSpeechBackend("working")
        
        self.router.register_backend("failing", failing_backend, is_primary=True)
        self.router.register_backend("working", working_backend, is_fallback=True)
        
        # Initialize - should work even with failing primary
        self.router.initialize()
        
        # Create mock audio data
        audio_data = np.random.rand(1000).astype(np.float32)
        
        # Should fallback to working backend
        result = self.router.recognize_speech(audio_data)
        self.assertIsNotNone(result)
        self.assertIn("mock recognition result", result)
    
    def test_speech_recognition_no_backend(self):
        """Test speech recognition with no available backend"""
        # Don't register any backends
        result = self.router.recognize_speech(np.random.rand(1000).astype(np.float32))
        self.assertIsNone(result)
    
    def test_backend_switching(self):
        """Test manual backend switching"""
        backend1 = MockSpeechBackend("backend1")
        backend2 = MockSpeechBackend("backend2")
        
        self.router.register_backend("backend1", backend1, is_primary=True)
        self.router.register_backend("backend2", backend2)
        
        self.router.initialize()
        
        # Should start with primary backend
        self.assertEqual(self.router.current_backend, "backend1")
        
        # Switch to backend2
        result = self.router.switch_backend("backend2")
        self.assertTrue(result)
        self.assertEqual(self.router.current_backend, "backend2")
    
    def test_backend_switching_invalid(self):
        """Test switching to invalid backend"""
        mock_backend = MockSpeechBackend("test_backend")
        self.router.register_backend("test", mock_backend, is_primary=True)
        self.router.initialize()
        
        # Try to switch to non-existent backend
        result = self.router.switch_backend("nonexistent")
        self.assertFalse(result)
        self.assertEqual(self.router.current_backend, "test")  # Should remain unchanged
    
    def test_available_backends(self):
        """Test getting available backends"""
        backend1 = MockSpeechBackend("backend1")
        backend2 = MockSpeechBackend("backend2", should_fail=True)  # Not available
        
        self.router.register_backend("backend1", backend1)
        self.router.register_backend("backend2", backend2)
        
        available = self.router.get_available_backends()
        self.assertIn("backend1", available)
        self.assertNotIn("backend2", available)  # Should not be available
    
    def test_backend_info(self):
        """Test getting backend information"""
        mock_backend = MockSpeechBackend("test_backend")
        self.router.register_backend("test", mock_backend)
        
        info = self.router.get_backend_info("test")
        self.assertIsInstance(info, dict)
        self.assertIn("name", info)
        self.assertEqual(info["name"], "test_backend")
    
    def test_performance_stats(self):
        """Test performance statistics tracking"""
        mock_backend = MockSpeechBackend("test_backend")
        self.router.register_backend("test", mock_backend, is_primary=True)
        self.router.initialize()
        
        # Perform some recognition
        audio_data = np.random.rand(1000).astype(np.float32)
        self.router.recognize_speech(audio_data)
        
        stats = self.router.get_performance_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("total_requests", stats)
        self.assertIn("successful_requests", stats)
        self.assertGreater(stats["total_requests"], 0)
    
    def test_cleanup(self):
        """Test router cleanup"""
        mock_backend = MockSpeechBackend("test_backend")
        self.router.register_backend("test", mock_backend, is_primary=True)
        self.router.initialize()
        
        # Cleanup should not raise exception
        self.router.cleanup()
        
        # Backend should be cleaned up
        self.assertFalse(mock_backend.initialized)


class TestSpeechBackend(unittest.TestCase):
    """Test base speech backend functionality"""
    
    def test_backend_creation(self):
        """Test backend creation"""
        backend = MockSpeechBackend("test")
        self.assertEqual(backend.name, "test")
        self.assertFalse(backend.initialized)
    
    def test_backend_initialization(self):
        """Test backend initialization"""
        backend = MockSpeechBackend("test")
        
        result = backend.initialize()
        self.assertTrue(result)
        self.assertTrue(backend.initialized)
    
    def test_backend_recognition(self):
        """Test backend recognition"""
        backend = MockSpeechBackend("test")
        backend.initialize()
        
        audio_data = np.random.rand(1000).astype(np.float32)
        result = backend.recognize(audio_data)
        
        self.assertIsNotNone(result)
        self.assertIn("mock recognition result", result)
    
    def test_backend_cleanup(self):
        """Test backend cleanup"""
        backend = MockSpeechBackend("test")
        backend.initialize()
        
        backend.cleanup()
        self.assertFalse(backend.initialized)
    
    def test_backend_availability(self):
        """Test backend availability check"""
        working_backend = MockSpeechBackend("working")
        failing_backend = MockSpeechBackend("failing", should_fail=True)
        
        self.assertTrue(working_backend.is_available())
        self.assertFalse(failing_backend.is_available())
    
    def test_backend_info(self):
        """Test backend info retrieval"""
        backend = MockSpeechBackend("test")
        info = backend.get_info()
        
        self.assertIsInstance(info, dict)
        self.assertIn("name", info)
        self.assertIn("initialized", info)
        self.assertEqual(info["name"], "test")


class TestAudioProcessing(unittest.TestCase):
    """Test audio processing utilities"""
    
    def test_audio_data_validation(self):
        """Test audio data validation"""
        # Valid audio data
        valid_audio = np.random.rand(1000).astype(np.float32)
        self.assertEqual(valid_audio.dtype, np.float32)
        self.assertGreater(len(valid_audio), 0)
        
        # Test different data types
        int_audio = np.random.randint(-32768, 32767, 1000, dtype=np.int16)
        self.assertEqual(int_audio.dtype, np.int16)
    
    def test_sample_rate_validation(self):
        """Test sample rate validation"""
        common_rates = [8000, 16000, 22050, 44100, 48000]
        
        for rate in common_rates:
            self.assertGreater(rate, 0)
            self.assertIsInstance(rate, int)
    
    def test_audio_normalization(self):
        """Test audio normalization"""
        # Create audio with known range
        audio = np.array([-2.0, -1.0, 0.0, 1.0, 2.0], dtype=np.float32)
        
        # Normalize to [-1, 1] range
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            normalized = audio / max_val
        else:
            normalized = audio
        
        self.assertLessEqual(np.max(np.abs(normalized)), 1.0)
    
    def test_audio_chunking(self):
        """Test audio chunking for processing"""
        # Create long audio data
        long_audio = np.random.rand(10000).astype(np.float32)
        chunk_size = 1000
        
        chunks = []
        for i in range(0, len(long_audio), chunk_size):
            chunk = long_audio[i:i + chunk_size]
            chunks.append(chunk)
        
        # Verify chunking
        self.assertGreater(len(chunks), 1)
        self.assertEqual(len(chunks[0]), chunk_size)
        
        # Verify we can reconstruct original
        reconstructed = np.concatenate(chunks)
        np.testing.assert_array_equal(reconstructed, long_audio)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)