#!/usr/bin/env python3
"""
Enhanced Input Handler for Voice Control Application

Provides cursor position-aware voice commands, reliable text insertion,
and mouse-aware functionality across different applications and environments.
"""

import logging
import subprocess
import time
from typing import Optional, Tuple, Dict, Any, List
from pathlib import Path
import os
import threading
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CursorPosition:
    """Represents cursor position with context"""
    x: int
    y: int
    window_id: Optional[str] = None
    window_title: Optional[str] = None
    application: Optional[str] = None
    context: Optional[str] = None


@dataclass
class InputContext:
    """Represents the current input context"""
    display_server: str  # "x11" or "wayland"
    input_method: str    # "ydotool", "xdotool", "wtype", etc.
    cursor_position: Optional[CursorPosition] = None
    active_window: Optional[str] = None
    focused_element: Optional[str] = None


class InputHandler:
    """Enhanced input handler with cursor awareness and mouse integration"""
    
    def __init__(self):
        self.input_context = self._detect_input_context()
        self.clipboard_manager = None
        self.last_cursor_position = None
        self.position_cache_timeout = 1.0  # seconds
        self.last_position_update = 0
        
        # Import clipboard manager
        try:
            from voice_control.system.clipboard_manager import get_clipboard_manager
            self.clipboard_manager = get_clipboard_manager()
        except ImportError:
            logger.warning("Clipboard manager not available")
        
        logger.info(f"Input handler initialized: {self.input_context.display_server} with {self.input_context.input_method}")
    
    def _detect_input_context(self) -> InputContext:
        """Detect the current input environment and available tools"""
        # Detect display server
        display_server = "x11"
        if os.getenv("WAYLAND_DISPLAY"):
            display_server = "wayland"
        elif not os.getenv("DISPLAY"):
            logger.warning("No display server detected")
        
        # Detect available input method
        input_method = self._detect_input_method(display_server)
        
        return InputContext(
            display_server=display_server,
            input_method=input_method
        )
    
    def _detect_input_method(self, display_server: str) -> str:
        """Detect available input simulation method"""
        if display_server == "wayland":
            # Wayland input methods
            methods = [
                ("ydotool", ["ydotool", "--help"]),
                ("wtype", ["wtype", "--help"]),
                ("dotool", ["dotool", "--help"]),
            ]
        else:
            # X11 input methods
            methods = [
                ("xdotool", ["xdotool", "--help"]),
                ("ydotool", ["ydotool", "--help"]),
                ("xte", ["xte", "--help"]),
            ]
        
        for method_name, test_cmd in methods:
            try:
                result = subprocess.run(test_cmd, capture_output=True, timeout=2)
                if result.returncode == 0:
                    logger.info(f"Found input method: {method_name}")
                    return method_name
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
                continue
        
        logger.warning("No input simulation method found")
        return "none"
    
    def get_cursor_position(self, force_update: bool = False) -> Optional[CursorPosition]:
        """Get current cursor position with caching"""
        current_time = time.time()
        
        # Use cached position if recent and not forced
        if (not force_update and 
            self.last_cursor_position and 
            current_time - self.last_position_update < self.position_cache_timeout):
            return self.last_cursor_position
        
        # Get fresh position
        position = self._get_cursor_position_now()
        
        if position:
            self.last_cursor_position = position
            self.last_position_update = current_time
        
        return position
    
    def _get_cursor_position_now(self) -> Optional[CursorPosition]:
        """Get current cursor position immediately"""
        try:
            if self.input_context.display_server == "x11":
                return self._get_x11_cursor_position()
            else:
                return self._get_wayland_cursor_position()
        except Exception as e:
            logger.error(f"Error getting cursor position: {e}")
            return None
    
    def _get_x11_cursor_position(self) -> Optional[CursorPosition]:
        """Get cursor position in X11"""
        try:
            # Use xdotool to get mouse position
            result = subprocess.run(
                ["xdotool", "getmouselocation"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                # Parse output: "x:123 y:456 screen:0 window:12345"
                parts = result.stdout.strip().split()
                x = int(parts[0].split(':')[1])
                y = int(parts[1].split(':')[1])
                window_id = parts[3].split(':')[1] if len(parts) > 3 else None
                
                # Get window information
                window_title, application = self._get_x11_window_info(window_id)
                
                return CursorPosition(
                    x=x, y=y,
                    window_id=window_id,
                    window_title=window_title,
                    application=application
                )
        except Exception as e:
            logger.error(f"X11 cursor position detection failed: {e}")
        
        return None
    
    def _get_wayland_cursor_position(self) -> Optional[CursorPosition]:
        """Get cursor position in Wayland (limited support)"""
        try:
            # Wayland doesn't provide direct cursor position access
            # We'll use a workaround or return a default position
            logger.warning("Wayland cursor position detection limited")
            
            # Try to get focused window information
            window_info = self._get_wayland_window_info()
            
            return CursorPosition(
                x=0, y=0,  # Wayland doesn't expose cursor position
                window_title=window_info.get("title"),
                application=window_info.get("app_id")
            )
        except Exception as e:
            logger.error(f"Wayland cursor position detection failed: {e}")
        
        return None
    
    def _get_x11_window_info(self, window_id: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """Get window title and application name for X11 window"""
        if not window_id:
            return None, None
        
        try:
            # Get window title
            title_result = subprocess.run(
                ["xdotool", "getwindowname", window_id],
                capture_output=True,
                text=True,
                timeout=2
            )
            title = title_result.stdout.strip() if title_result.returncode == 0 else None
            
            # Get application name
            app_result = subprocess.run(
                ["xprop", "-id", window_id, "WM_CLASS"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            application = None
            if app_result.returncode == 0:
                # Parse WM_CLASS output: WM_CLASS(STRING) = "instance", "class"
                output = app_result.stdout.strip()
                if "=" in output:
                    class_part = output.split("=")[1].strip()
                    # Extract the class name (second part)
                    if "," in class_part:
                        application = class_part.split(",")[1].strip().strip('"')
            
            return title, application
            
        except Exception as e:
            logger.error(f"Error getting X11 window info: {e}")
            return None, None
    
    def _get_wayland_window_info(self) -> Dict[str, Optional[str]]:
        """Get window information for Wayland"""
        try:
            # Try different methods to get window info
            methods = [
                self._get_sway_window_info,
                self._get_gnome_window_info,
                self._get_kde_window_info,
            ]
            
            for method in methods:
                try:
                    info = method()
                    if info:
                        return info
                except Exception:
                    continue
            
        except Exception as e:
            logger.error(f"Error getting Wayland window info: {e}")
        
        return {"title": None, "app_id": None}
    
    def _get_sway_window_info(self) -> Optional[Dict[str, str]]:
        """Get window info from Sway compositor"""
        try:
            result = subprocess.run(
                ["swaymsg", "-t", "get_tree"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                import json
                tree = json.loads(result.stdout)
                focused = self._find_focused_node(tree)
                
                if focused:
                    return {
                        "title": focused.get("name"),
                        "app_id": focused.get("app_id")
                    }
        except Exception:
            pass
        
        return None
    
    def _find_focused_node(self, node: Dict) -> Optional[Dict]:
        """Find focused node in Sway tree"""
        if node.get("focused"):
            return node
        
        for child in node.get("nodes", []):
            result = self._find_focused_node(child)
            if result:
                return result
        
        for child in node.get("floating_nodes", []):
            result = self._find_focused_node(child)
            if result:
                return result
        
        return None
    
    def _get_gnome_window_info(self) -> Optional[Dict[str, str]]:
        """Get window info from GNOME"""
        try:
            result = subprocess.run([
                "gdbus", "call", "--session",
                "--dest", "org.gnome.Shell",
                "--object-path", "/org/gnome/Shell",
                "--method", "org.gnome.Shell.Eval",
                "global.get_window_actors().find(a => a.meta_window.has_focus()).meta_window.get_title()"
            ], capture_output=True, text=True, timeout=2)
            
            if result.returncode == 0:
                # Parse the result
                output = result.stdout.strip()
                if "'" in output:
                    title = output.split("'")[1]
                    return {"title": title, "app_id": None}
        except Exception:
            pass
        
        return None
    
    def _get_kde_window_info(self) -> Optional[Dict[str, str]]:
        """Get window info from KDE"""
        try:
            result = subprocess.run([
                "qdbus", "org.kde.KWin", "/KWin",
                "org.kde.KWin.activeWindow"
            ], capture_output=True, text=True, timeout=2)
            
            if result.returncode == 0:
                window_id = result.stdout.strip()
                
                # Get window title
                title_result = subprocess.run([
                    "qdbus", "org.kde.KWin", f"/KWin/Window_{window_id}",
                    "org.kde.KWin.Window.caption"
                ], capture_output=True, text=True, timeout=2)
                
                if title_result.returncode == 0:
                    title = title_result.stdout.strip()
                    return {"title": title, "app_id": None}
        except Exception:
            pass
        
        return None
    
    def type_text_at_cursor(self, text: str, verify: bool = True) -> bool:
        """Type text at current cursor position"""
        try:
            if not text:
                logger.warning("Attempted to type empty text")
                return False
            
            logger.debug(f"Typing text at cursor: {text[:100]}...")
            
            # Get current cursor position for context
            cursor_pos = self.get_cursor_position()
            if cursor_pos:
                logger.debug(f"Cursor context: {cursor_pos.application} - {cursor_pos.window_title}")
            
            # Perform the typing
            success = self._type_text(text)
            
            if success and verify:
                # Brief verification by checking if cursor moved or content changed
                time.sleep(0.1)
                new_pos = self.get_cursor_position(force_update=True)
                if new_pos and cursor_pos:
                    if new_pos.x != cursor_pos.x or new_pos.y != cursor_pos.y:
                        logger.debug("Cursor position changed, typing likely successful")
            
            return success
            
        except Exception as e:
            logger.error(f"Error typing text at cursor: {e}")
            return False
    
    def _type_text(self, text: str) -> bool:
        """Perform the actual text typing based on input method"""
        try:
            if self.input_context.input_method == "xdotool":
                return self._type_with_xdotool(text)
            elif self.input_context.input_method == "ydotool":
                return self._type_with_ydotool(text)
            elif self.input_context.input_method == "wtype":
                return self._type_with_wtype(text)
            elif self.input_context.input_method == "dotool":
                return self._type_with_dotool(text)
            else:
                return self._type_with_fallback(text)
                
        except Exception as e:
            logger.error(f"Text typing failed: {e}")
            return False
    
    def _type_with_xdotool(self, text: str) -> bool:
        """Type text using xdotool"""
        try:
            result = subprocess.run(
                ["xdotool", "type", "--delay", "10", text],
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"xdotool typing failed: {e}")
            return False
    
    def _type_with_ydotool(self, text: str) -> bool:
        """Type text using ydotool"""
        try:
            result = subprocess.run(
                ["ydotool", "type", text],
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"ydotool typing failed: {e}")
            return False
    
    def _type_with_wtype(self, text: str) -> bool:
        """Type text using wtype (Wayland)"""
        try:
            result = subprocess.run(
                ["wtype", text],
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"wtype typing failed: {e}")
            return False
    
    def _type_with_dotool(self, text: str) -> bool:
        """Type text using dotool"""
        try:
            result = subprocess.run(
                ["dotool", "type", text],
                timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"dotool typing failed: {e}")
            return False
    
    def _type_with_fallback(self, text: str) -> bool:
        """Fallback typing method using clipboard"""
        try:
            if not self.clipboard_manager:
                logger.error("No clipboard manager available for fallback typing")
                return False
            
            # Save current clipboard content
            original_content = self.clipboard_manager.get_clipboard_content()
            
            # Copy text to clipboard
            if not self.clipboard_manager.copy_to_clipboard(text):
                logger.error("Failed to copy text to clipboard for fallback typing")
                return False
            
            # Simulate Ctrl+V
            success = self._simulate_paste_shortcut()
            
            # Restore original clipboard content
            if original_content:
                self.clipboard_manager.copy_to_clipboard(original_content, verify=False)
            
            return success
            
        except Exception as e:
            logger.error(f"Fallback typing failed: {e}")
            return False
    
    def _simulate_paste_shortcut(self) -> bool:
        """Simulate Ctrl+V paste shortcut"""
        try:
            if self.input_context.input_method == "xdotool":
                result = subprocess.run([
                    "xdotool", "key", "ctrl+v"
                ], timeout=5)
                return result.returncode == 0
            elif self.input_context.input_method == "ydotool":
                result = subprocess.run([
                    "ydotool", "key", "29:1", "47:1", "47:0", "29:0"  # Ctrl+V
                ], timeout=5)
                return result.returncode == 0
            else:
                logger.warning("Cannot simulate paste shortcut with current input method")
                return False
        except Exception as e:
            logger.error(f"Paste shortcut simulation failed: {e}")
            return False
    
    def click_at_position(self, x: int, y: int, button: str = "left") -> bool:
        """Click at specific coordinates"""
        try:
            logger.debug(f"Clicking at position ({x}, {y}) with {button} button")
            
            if self.input_context.input_method == "xdotool":
                return self._click_with_xdotool(x, y, button)
            elif self.input_context.input_method == "ydotool":
                return self._click_with_ydotool(x, y, button)
            else:
                logger.warning("Click not supported with current input method")
                return False
                
        except Exception as e:
            logger.error(f"Click operation failed: {e}")
            return False
    
    def _click_with_xdotool(self, x: int, y: int, button: str) -> bool:
        """Click using xdotool"""
        try:
            # Map button names
            button_map = {"left": "1", "middle": "2", "right": "3"}
            button_num = button_map.get(button, "1")
            
            result = subprocess.run([
                "xdotool", "mousemove", str(x), str(y), "click", button_num
            ], timeout=5)
            
            return result.returncode == 0
        except Exception as e:
            logger.error(f"xdotool click failed: {e}")
            return False
    
    def _click_with_ydotool(self, x: int, y: int, button: str) -> bool:
        """Click using ydotool"""
        try:
            # Move mouse to position
            subprocess.run([
                "ydotool", "mousemove", str(x), str(y)
            ], timeout=5)
            
            # Click
            button_map = {"left": "0xC0", "middle": "0xC1", "right": "0xC2"}
            button_code = button_map.get(button, "0xC0")
            
            result = subprocess.run([
                "ydotool", "click", button_code
            ], timeout=5)
            
            return result.returncode == 0
        except Exception as e:
            logger.error(f"ydotool click failed: {e}")
            return False
    
    def click_at_cursor(self, button: str = "left") -> bool:
        """Click at current cursor position"""
        cursor_pos = self.get_cursor_position()
        if not cursor_pos:
            logger.error("Cannot get cursor position for click")
            return False
        
        return self.click_at_position(cursor_pos.x, cursor_pos.y, button)
    
    def move_cursor_to(self, x: int, y: int) -> bool:
        """Move cursor to specific position"""
        try:
            logger.debug(f"Moving cursor to ({x}, {y})")
            
            if self.input_context.input_method == "xdotool":
                result = subprocess.run([
                    "xdotool", "mousemove", str(x), str(y)
                ], timeout=5)
                return result.returncode == 0
            elif self.input_context.input_method == "ydotool":
                result = subprocess.run([
                    "ydotool", "mousemove", str(x), str(y)
                ], timeout=5)
                return result.returncode == 0
            else:
                logger.warning("Cursor movement not supported with current input method")
                return False
                
        except Exception as e:
            logger.error(f"Cursor movement failed: {e}")
            return False
    
    def get_element_at_cursor(self) -> Optional[Dict[str, Any]]:
        """Get information about the element under the cursor"""
        cursor_pos = self.get_cursor_position()
        if not cursor_pos:
            return None
        
        try:
            # This is a simplified implementation
            # In a full implementation, you might use accessibility APIs
            return {
                "position": (cursor_pos.x, cursor_pos.y),
                "window": cursor_pos.window_title,
                "application": cursor_pos.application,
                "type": "unknown"  # Would need accessibility API to determine
            }
        except Exception as e:
            logger.error(f"Error getting element at cursor: {e}")
            return None
    
    def get_input_status(self) -> Dict[str, Any]:
        """Get current input handler status"""
        cursor_pos = self.get_cursor_position()
        
        return {
            "display_server": self.input_context.display_server,
            "input_method": self.input_context.input_method,
            "input_method_available": self.input_context.input_method != "none",
            "cursor_position": {
                "x": cursor_pos.x if cursor_pos else None,
                "y": cursor_pos.y if cursor_pos else None,
                "window": cursor_pos.window_title if cursor_pos else None,
                "application": cursor_pos.application if cursor_pos else None
            } if cursor_pos else None,
            "clipboard_available": self.clipboard_manager is not None
        }


# Global input handler instance
_input_handler = None


def get_input_handler() -> InputHandler:
    """Get or create global input handler instance"""
    global _input_handler
    
    if _input_handler is None:
        _input_handler = InputHandler()
    
    return _input_handler


def main():
    """Test the input handler"""
    logging.basicConfig(level=logging.DEBUG)
    
    input_handler = InputHandler()
    
    # Test cursor position
    print("Testing cursor position...")
    cursor_pos = input_handler.get_cursor_position()
    if cursor_pos:
        print(f"Cursor at: ({cursor_pos.x}, {cursor_pos.y})")
        print(f"Window: {cursor_pos.window_title}")
        print(f"Application: {cursor_pos.application}")
    else:
        print("Could not get cursor position")
    
    # Test input status
    status = input_handler.get_input_status()
    print(f"\nInput status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Test typing (commented out to avoid accidental typing)
    # print("\nTesting typing in 3 seconds...")
    # time.sleep(3)
    # input_handler.type_text_at_cursor("Hello from Voice Control!")


if __name__ == "__main__":
    main()