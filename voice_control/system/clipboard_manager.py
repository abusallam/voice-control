#!/usr/bin/env python3
"""
Clipboard Manager for Voice Control Application

Provides robust clipboard operations with verification, error handling,
and clipboard history management.
"""

import logging
import subprocess
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import threading
import os

logger = logging.getLogger(__name__)


class ClipboardEntry:
    """Individual clipboard entry with metadata"""
    
    def __init__(self, content: str, content_type: str = "text"):
        self.content = content
        self.content_type = content_type
        self.timestamp = datetime.now()
        self.id = id(self)
    
    def __str__(self):
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {self.content_type}: {preview}"


class ClipboardManager:
    """Manages clipboard operations with history and verification"""
    
    def __init__(self):
        self.clipboard_history: List[ClipboardEntry] = []
        self.max_history_size = 50
        self.clipboard_backend = self._detect_clipboard_backend()
        self.verification_timeout = 2.0  # seconds
        
        logger.info(f"Clipboard manager initialized with backend: {self.clipboard_backend}")
    
    def _detect_clipboard_backend(self) -> str:
        """Detect available clipboard backend"""
        # Check for different clipboard tools in order of preference
        backends = [
            ("xclip", ["xclip", "-version"]),
            ("xsel", ["xsel", "--version"]),
            ("wl-clipboard", ["wl-copy", "--version"]),
            ("pbcopy", ["pbcopy", "--version"]),  # macOS fallback
        ]
        
        for backend_name, test_cmd in backends:
            try:
                result = subprocess.run(test_cmd, capture_output=True, timeout=2)
                if result.returncode == 0:
                    logger.info(f"Found clipboard backend: {backend_name}")
                    return backend_name
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
                continue
        
        logger.warning("No clipboard backend found, using fallback")
        return "fallback"
    
    def copy_to_clipboard(self, text: str, verify: bool = True) -> bool:
        """Copy text to clipboard with verification"""
        try:
            if not text:
                logger.warning("Attempted to copy empty text to clipboard")
                return False
            
            logger.debug(f"Copying to clipboard: {text[:100]}...")
            
            # Perform the copy operation
            success = self._copy_text(text)
            
            if not success:
                logger.error("Failed to copy text to clipboard")
                return False
            
            # Verify if requested
            if verify:
                if not self._verify_clipboard_content(text):
                    logger.error("Clipboard verification failed")
                    return False
            
            # Add to history
            self._add_to_history(text, "text")
            
            logger.debug("Text copied to clipboard successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error copying to clipboard: {e}")
            return False
    
    def _copy_text(self, text: str) -> bool:
        """Perform the actual copy operation based on backend"""
        try:
            if self.clipboard_backend == "xclip":
                return self._copy_with_xclip(text)
            elif self.clipboard_backend == "xsel":
                return self._copy_with_xsel(text)
            elif self.clipboard_backend == "wl-clipboard":
                return self._copy_with_wl_clipboard(text)
            elif self.clipboard_backend == "pbcopy":
                return self._copy_with_pbcopy(text)
            else:
                return self._copy_with_fallback(text)
                
        except Exception as e:
            logger.error(f"Copy operation failed: {e}")
            return False
    
    def _copy_with_xclip(self, text: str) -> bool:
        """Copy using xclip"""
        try:
            # Copy to both primary and clipboard selections
            process = subprocess.Popen(
                ["xclip", "-selection", "clipboard"],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(input=text, timeout=5)
            return process.returncode == 0
        except Exception as e:
            logger.error(f"xclip copy failed: {e}")
            return False
    
    def _copy_with_xsel(self, text: str) -> bool:
        """Copy using xsel"""
        try:
            process = subprocess.Popen(
                ["xsel", "--clipboard", "--input"],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(input=text, timeout=5)
            return process.returncode == 0
        except Exception as e:
            logger.error(f"xsel copy failed: {e}")
            return False
    
    def _copy_with_wl_clipboard(self, text: str) -> bool:
        """Copy using wl-clipboard (Wayland)"""
        try:
            process = subprocess.Popen(
                ["wl-copy"],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(input=text, timeout=5)
            return process.returncode == 0
        except Exception as e:
            logger.error(f"wl-copy failed: {e}")
            return False
    
    def _copy_with_pbcopy(self, text: str) -> bool:
        """Copy using pbcopy (macOS)"""
        try:
            process = subprocess.Popen(
                ["pbcopy"],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(input=text, timeout=5)
            return process.returncode == 0
        except Exception as e:
            logger.error(f"pbcopy failed: {e}")
            return False
    
    def _copy_with_fallback(self, text: str) -> bool:
        """Fallback copy method using temporary file"""
        try:
            # Create a temporary file with the text
            temp_file = Path("/tmp/voice_control_clipboard.txt")
            temp_file.write_text(text)
            
            logger.warning("Using fallback clipboard method - text saved to temporary file")
            logger.info(f"Clipboard content saved to: {temp_file}")
            
            return True
        except Exception as e:
            logger.error(f"Fallback copy failed: {e}")
            return False
    
    def get_clipboard_content(self) -> Optional[str]:
        """Get current clipboard content"""
        try:
            if self.clipboard_backend == "xclip":
                return self._get_with_xclip()
            elif self.clipboard_backend == "xsel":
                return self._get_with_xsel()
            elif self.clipboard_backend == "wl-clipboard":
                return self._get_with_wl_clipboard()
            elif self.clipboard_backend == "pbcopy":
                return self._get_with_pbpaste()
            else:
                return self._get_with_fallback()
                
        except Exception as e:
            logger.error(f"Error getting clipboard content: {e}")
            return None
    
    def _get_with_xclip(self) -> Optional[str]:
        """Get clipboard content using xclip"""
        try:
            result = subprocess.run(
                ["xclip", "-selection", "clipboard", "-out"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout if result.returncode == 0 else None
        except Exception as e:
            logger.error(f"xclip get failed: {e}")
            return None
    
    def _get_with_xsel(self) -> Optional[str]:
        """Get clipboard content using xsel"""
        try:
            result = subprocess.run(
                ["xsel", "--clipboard", "--output"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout if result.returncode == 0 else None
        except Exception as e:
            logger.error(f"xsel get failed: {e}")
            return None
    
    def _get_with_wl_clipboard(self) -> Optional[str]:
        """Get clipboard content using wl-clipboard"""
        try:
            result = subprocess.run(
                ["wl-paste"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout if result.returncode == 0 else None
        except Exception as e:
            logger.error(f"wl-paste failed: {e}")
            return None
    
    def _get_with_pbpaste(self) -> Optional[str]:
        """Get clipboard content using pbpaste (macOS)"""
        try:
            result = subprocess.run(
                ["pbpaste"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout if result.returncode == 0 else None
        except Exception as e:
            logger.error(f"pbpaste failed: {e}")
            return None
    
    def _get_with_fallback(self) -> Optional[str]:
        """Get clipboard content using fallback method"""
        try:
            temp_file = Path("/tmp/voice_control_clipboard.txt")
            if temp_file.exists():
                return temp_file.read_text()
            return None
        except Exception as e:
            logger.error(f"Fallback get failed: {e}")
            return None
    
    def _verify_clipboard_content(self, expected_text: str) -> bool:
        """Verify that clipboard contains expected text"""
        try:
            # Wait a moment for clipboard to update
            time.sleep(0.1)
            
            # Get current clipboard content
            current_content = self.get_clipboard_content()
            
            if current_content is None:
                logger.warning("Could not retrieve clipboard content for verification")
                return False
            
            # Compare content
            if current_content.strip() == expected_text.strip():
                return True
            else:
                logger.warning(f"Clipboard verification failed. Expected: '{expected_text[:50]}...', Got: '{current_content[:50]}...'")
                return False
                
        except Exception as e:
            logger.error(f"Clipboard verification error: {e}")
            return False
    
    def paste_from_clipboard(self) -> Optional[str]:
        """Get text from clipboard for pasting"""
        content = self.get_clipboard_content()
        if content:
            logger.debug(f"Retrieved from clipboard: {content[:100]}...")
        return content
    
    def cut_to_clipboard(self, text: str) -> bool:
        """Cut text to clipboard (same as copy for text)"""
        return self.copy_to_clipboard(text)
    
    def _add_to_history(self, content: str, content_type: str = "text"):
        """Add entry to clipboard history"""
        entry = ClipboardEntry(content, content_type)
        self.clipboard_history.append(entry)
        
        # Trim history if too large
        if len(self.clipboard_history) > self.max_history_size:
            self.clipboard_history.pop(0)
        
        logger.debug(f"Added to clipboard history: {entry}")
    
    def get_clipboard_history(self, limit: int = 10) -> List[ClipboardEntry]:
        """Get recent clipboard history"""
        return self.clipboard_history[-limit:]
    
    def clear_clipboard_history(self):
        """Clear clipboard history"""
        self.clipboard_history.clear()
        logger.info("Clipboard history cleared")
    
    def detect_content_type(self, content: str) -> str:
        """Detect the type of clipboard content"""
        if not content:
            return "empty"
        
        # Check for URLs
        if content.startswith(("http://", "https://", "ftp://", "file://")):
            return "url"
        
        # Check for file paths
        if content.startswith("/") and Path(content).exists():
            return "file_path"
        
        # Check for email addresses
        if "@" in content and "." in content.split("@")[-1]:
            return "email"
        
        # Check for numbers
        try:
            float(content.strip())
            return "number"
        except ValueError:
            pass
        
        # Check for code (contains common programming keywords)
        code_indicators = ["def ", "class ", "import ", "function", "var ", "let ", "const "]
        if any(indicator in content.lower() for indicator in code_indicators):
            return "code"
        
        # Default to text
        return "text"
    
    def get_clipboard_status(self) -> Dict[str, Any]:
        """Get current clipboard manager status"""
        current_content = self.get_clipboard_content()
        
        return {
            "backend": self.clipboard_backend,
            "current_content_length": len(current_content) if current_content else 0,
            "current_content_type": self.detect_content_type(current_content) if current_content else "empty",
            "history_size": len(self.clipboard_history),
            "max_history_size": self.max_history_size,
            "backend_available": self.clipboard_backend != "fallback"
        }
    
    def test_clipboard_operations(self) -> Dict[str, bool]:
        """Test clipboard operations and return results"""
        test_text = "Voice Control Clipboard Test"
        results = {
            "copy_operation": False,
            "get_operation": False,
            "verification": False,
            "backend_functional": False
        }
        
        try:
            # Test copy
            results["copy_operation"] = self._copy_text(test_text)
            
            # Test get
            retrieved_content = self.get_clipboard_content()
            results["get_operation"] = retrieved_content is not None
            
            # Test verification
            if retrieved_content:
                results["verification"] = retrieved_content.strip() == test_text.strip()
            
            # Overall backend functionality
            results["backend_functional"] = all([
                results["copy_operation"],
                results["get_operation"],
                results["verification"]
            ])
            
        except Exception as e:
            logger.error(f"Clipboard test failed: {e}")
        
        return results


# Global clipboard manager instance
_clipboard_manager = None


def get_clipboard_manager() -> ClipboardManager:
    """Get or create global clipboard manager instance"""
    global _clipboard_manager
    
    if _clipboard_manager is None:
        _clipboard_manager = ClipboardManager()
    
    return _clipboard_manager


def main():
    """Test the clipboard manager"""
    logging.basicConfig(level=logging.DEBUG)
    
    clipboard_mgr = ClipboardManager()
    
    # Test clipboard operations
    print("Testing clipboard operations...")
    
    test_results = clipboard_mgr.test_clipboard_operations()
    print("Test results:")
    for test, result in test_results.items():
        print(f"  {test}: {'✓' if result else '✗'}")
    
    # Test copy and paste
    test_text = "Hello from Voice Control!"
    print(f"\nTesting copy: '{test_text}'")
    
    if clipboard_mgr.copy_to_clipboard(test_text):
        print("Copy successful")
        
        retrieved = clipboard_mgr.paste_from_clipboard()
        print(f"Retrieved: '{retrieved}'")
        
        if retrieved == test_text:
            print("✓ Copy/paste test passed")
        else:
            print("✗ Copy/paste test failed")
    else:
        print("✗ Copy failed")
    
    # Show status
    status = clipboard_mgr.get_clipboard_status()
    print(f"\nClipboard status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Show history
    history = clipboard_mgr.get_clipboard_history()
    print(f"\nClipboard history ({len(history)} entries):")
    for entry in history:
        print(f"  {entry}")


if __name__ == "__main__":
    main()