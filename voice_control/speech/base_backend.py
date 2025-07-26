#!/usr/bin/env python3
"""
Base speech recognition backend interface
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import numpy as np


class SpeechBackend(ABC):
    """Abstract base class for speech recognition backends"""
    
    def __init__(self, name: str):
        self.name = name
        self.initialized = False
        self.config = {}
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """Initialize the speech recognition backend"""
        pass
    
    @abstractmethod
    def recognize(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Optional[str]:
        """Recognize speech from audio data"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Clean up resources"""
        pass
    
    def is_available(self) -> bool:
        """Check if this backend is available on the system"""
        return self.initialized
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about this backend"""
        return {
            'name': self.name,
            'initialized': self.initialized,
            'config': self.config
        }