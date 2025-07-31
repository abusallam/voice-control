# Enhanced Voice Commands Design

## Overview

This design document outlines the architecture for adding intelligent command processing to the Voice Control for Linux application. The system will extend beyond simple speech-to-text to recognize and execute specific voice commands while maintaining the existing dictation functionality.

## Current System Analysis

### What Works Well
- **Speech Recognition**: Whisper-based recognition is accurate and reliable
- **System Tray Integration**: User interface is intuitive and accessible
- **Audio Processing**: Real-time audio capture and processing pipeline
- **Service Management**: Stable systemd service integration
- **Cross-Platform Support**: Works reliably across Linux distributions

### What Needs Enhancement
- **Command Intelligence**: Currently only does speech-to-text dictation
- **Application Awareness**: No understanding of current application context
- **User Feedback**: Limited visual feedback for command execution
- **Customization**: No way for users to add custom commands
- **Context Sensitivity**: Commands work the same regardless of situation

## Architecture Design

### Enhanced System Architecture

```
Voice Control Enhanced Architecture
├── Speech Recognition Layer (Existing)
│   ├── Audio Capture
│   ├── Whisper Processing
│   └── Text Output
├── Command Processing Layer (NEW)
│   ├── Command Parser
│   ├── Fuzzy Matcher
│   ├── Context Analyzer
│   └── Command Router
├── Execution Layer (NEW)
│   ├── Built-in Commands
│   ├── Application Integration
│   ├── Custom Commands
│   └── System Actions
├── Feedback Layer (ENHANCED)
│   ├── Visual Notifications
│   ├── System Tray Updates
│   ├── Command History
│   └── Error Reporting
└── Configuration Layer (ENHANCED)
    ├── Command Management
    ├── User Preferences
    ├── Application Profiles
    └── Custom Command Editor
```

## Component Design

### 1. Command Processing System

The core of the enhanced system is the command processor that analyzes recognized text and determines whether it's a command or dictation.

```python
class CommandProcessor:
    """Main command processing engine"""
    
    def __init__(self):
        self.command_registry = CommandRegistry()
        self.fuzzy_matcher = FuzzyMatcher()
        self.context_analyzer = ContextAnalyzer()
        self.history_manager = HistoryManager()
        
    def process_text(self, recognized_text: str) -> ProcessingResult:
        """Process recognized text and determine action"""
        # Analyze current context
        context = self.context_analyzer.get_current_context()
        
        # Try to match as command
        command_match = self.fuzzy_matcher.find_best_match(
            recognized_text, 
            self.command_registry.get_commands(context)
        )
        
        if command_match.confidence > COMMAND_THRESHOLD:
            return self._execute_command(command_match, context)
        else:
            return self._handle_dictation(recognized_text)
    
    def _execute_command(self, match: CommandMatch, context: Context) -> ProcessingResult:
        """Execute a matched command"""
        command = match.command
        
        # Check if confirmation required
        if command.requires_confirmation:
            if not self._get_user_confirmation(command):
                return ProcessingResult.cancelled()
        
        # Execute command
        try:
            result = command.execute(context, match.parameters)
            self.history_manager.record_command(command, result)
            return ProcessingResult.success(result)
        except Exception as e:
            return ProcessingResult.error(str(e))
```

### 2. Command Registry System

A flexible system for managing built-in and custom commands.

```python
class Command:
    """Base class for all voice commands"""
    
    def __init__(self, 
                 name: str,
                 trigger_phrases: List[str],
                 description: str,
                 requires_confirmation: bool = False,
                 application_context: Optional[str] = None):
        self.name = name
        self.trigger_phrases = trigger_phrases
        self.description = description
        self.requires_confirmation = requires_confirmation
        self.application_context = application_context
    
    def matches_context(self, context: Context) -> bool:
        """Check if command is applicable in current context"""
        if self.application_context is None:
            return True
        return context.application == self.application_context
    
    def execute(self, context: Context, parameters: Dict[str, Any]) -> CommandResult:
        """Execute the command - to be implemented by subclasses"""
        raise NotImplementedError

class SystemCommand(Command):
    """Commands that interact with the system"""
    
    def execute(self, context: Context, parameters: Dict[str, Any]) -> CommandResult:
        if self.name == "lock_screen":
            subprocess.run(["loginctl", "lock-session"])
            return CommandResult.success("Screen locked")
        elif self.name == "take_screenshot":
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            subprocess.run(["gnome-screenshot", "-f", filename])
            return CommandResult.success(f"Screenshot saved as {filename}")

class ApplicationCommand(Command):
    """Commands that interact with applications"""
    
    def execute(self, context: Context, parameters: Dict[str, Any]) -> CommandResult:
        if self.name == "new_tab" and context.application == "firefox":
            self._send_key_combination("ctrl+t")
            return CommandResult.success("New tab opened")
        elif self.name == "save_file":
            self._send_key_combination("ctrl+s")
            return CommandResult.success("Save command sent")
```

### 3. Context Analysis System

Understanding the current application and desktop state for context-aware commands.

```python
class ContextAnalyzer:
    """Analyzes current desktop context for command processing"""
    
    def __init__(self):
        self.window_manager = WindowManager()
        self.application_detector = ApplicationDetector()
    
    def get_current_context(self) -> Context:
        """Get current desktop context"""
        active_window = self.window_manager.get_active_window()
        
        return Context(
            application=self.application_detector.identify_application(active_window),
            window_title=active_window.title if active_window else None,
            desktop_environment=self._detect_desktop_environment(),
            display_server=self._detect_display_server(),
            timestamp=datetime.now()
        )
    
    def _detect_desktop_environment(self) -> str:
        """Detect current desktop environment"""
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        if 'gnome' in desktop:
            return 'gnome'
        elif 'kde' in desktop:
            return 'kde'
        elif 'xfce' in desktop:
            return 'xfce'
        else:
            return 'unknown'

class WindowManager:
    """Cross-platform window management"""
    
    def __init__(self):
        self.display_server = self._detect_display_server()
        
    def get_active_window(self) -> Optional[Window]:
        """Get currently active window"""
        if self.display_server == 'x11':
            return self._get_active_window_x11()
        elif self.display_server == 'wayland':
            return self._get_active_window_wayland()
        else:
            return None
    
    def _get_active_window_x11(self) -> Optional[Window]:
        """Get active window using X11 APIs"""
        try:
            from Xlib import display
            d = display.Display()
            window = d.get_input_focus().focus
            return Window(
                id=window.id,
                title=window.get_wm_name(),
                class_name=window.get_wm_class()
            )
        except Exception:
            return None
```

### 4. Fuzzy Command Matching

Intelligent matching of spoken text to available commands.

```python
class FuzzyMatcher:
    """Fuzzy matching for voice commands"""
    
    def __init__(self):
        self.similarity_threshold = 0.7
        self.word_weights = {
            'action_words': 2.0,  # open, close, save, etc.
            'object_words': 1.5,  # browser, file, window, etc.
            'modifier_words': 1.0  # new, current, next, etc.
        }
    
    def find_best_match(self, text: str, commands: List[Command]) -> CommandMatch:
        """Find best matching command for given text"""
        text_normalized = self._normalize_text(text)
        best_match = None
        best_score = 0.0
        
        for command in commands:
            for phrase in command.trigger_phrases:
                score = self._calculate_similarity(text_normalized, phrase)
                if score > best_score:
                    best_score = score
                    best_match = CommandMatch(
                        command=command,
                        confidence=score,
                        matched_phrase=phrase,
                        parameters=self._extract_parameters(text, phrase)
                    )
        
        return best_match or CommandMatch.no_match()
    
    def _calculate_similarity(self, text: str, phrase: str) -> float:
        """Calculate similarity between text and command phrase"""
        # Use combination of:
        # 1. Levenshtein distance
        # 2. Word overlap
        # 3. Semantic similarity
        # 4. Weighted word importance
        
        words_text = text.split()
        words_phrase = phrase.split()
        
        # Word overlap score
        overlap_score = len(set(words_text) & set(words_phrase)) / max(len(words_text), len(words_phrase))
        
        # Levenshtein distance score
        distance_score = 1.0 - (levenshtein_distance(text, phrase) / max(len(text), len(phrase)))
        
        # Combine scores
        return (overlap_score * 0.6) + (distance_score * 0.4)
```

### 5. Built-in Command Library

A comprehensive set of built-in commands for common operations.

```python
class BuiltinCommands:
    """Library of built-in voice commands"""
    
    @staticmethod
    def get_system_commands() -> List[Command]:
        """Get system-level commands"""
        return [
            SystemCommand(
                name="lock_screen",
                trigger_phrases=["lock screen", "lock computer", "lock desktop"],
                description="Lock the desktop session",
                requires_confirmation=True
            ),
            SystemCommand(
                name="take_screenshot",
                trigger_phrases=["take screenshot", "capture screen", "screenshot"],
                description="Capture a screenshot"
            ),
            SystemCommand(
                name="open_terminal",
                trigger_phrases=["open terminal", "launch terminal", "start terminal"],
                description="Open the default terminal application"
            ),
            SystemCommand(
                name="open_browser",
                trigger_phrases=["open browser", "launch browser", "start browser"],
                description="Open the default web browser"
            )
        ]
    
    @staticmethod
    def get_application_commands() -> List[Command]:
        """Get application-specific commands"""
        return [
            ApplicationCommand(
                name="new_tab",
                trigger_phrases=["new tab", "open tab", "create tab"],
                description="Open a new tab",
                application_context="browser"
            ),
            ApplicationCommand(
                name="save_file",
                trigger_phrases=["save file", "save document", "save"],
                description="Save the current file"
            ),
            ApplicationCommand(
                name="copy_selection",
                trigger_phrases=["copy", "copy selection", "copy text"],
                description="Copy selected text to clipboard"
            ),
            ApplicationCommand(
                name="paste_clipboard",
                trigger_phrases=["paste", "paste clipboard", "paste text"],
                description="Paste from clipboard"
            )
        ]
```

### 6. Visual Feedback System

Enhanced system tray and notification system for command feedback.

```python
class CommandFeedbackManager:
    """Manages visual feedback for command execution"""
    
    def __init__(self, system_tray, notification_manager):
        self.system_tray = system_tray
        self.notification_manager = notification_manager
        self.current_command = None
        
    def show_command_recognized(self, command: Command):
        """Show that a command was recognized"""
        self.current_command = command
        self.system_tray.update_status(f"Command: {command.name}")
        
    def show_command_executing(self, command: Command):
        """Show that a command is executing"""
        self.system_tray.show_progress_indicator()
        self.notification_manager.show_info(
            "Executing Command",
            f"Running: {command.description}"
        )
        
    def show_command_success(self, command: Command, result: CommandResult):
        """Show successful command execution"""
        self.system_tray.hide_progress_indicator()
        self.system_tray.update_status("Ready")
        self.notification_manager.show_success(
            "Command Completed",
            result.message
        )
        
    def show_command_error(self, command: Command, error: str):
        """Show command execution error"""
        self.system_tray.hide_progress_indicator()
        self.system_tray.update_status("Error")
        self.notification_manager.show_error(
            "Command Failed",
            f"{command.name}: {error}"
        )
```

## Implementation Strategy

### Phase 1: Core Command Processing (Week 1-2)
1. **Command Infrastructure**: Implement base Command class and CommandProcessor
2. **Basic Commands**: Add essential system commands (lock, screenshot, terminal)
3. **Fuzzy Matching**: Implement basic fuzzy matching for command recognition
4. **Integration**: Connect command processor to existing speech recognition

### Phase 2: Context Awareness (Week 2-3)
1. **Window Detection**: Implement cross-platform window detection
2. **Application Recognition**: Add application identification system
3. **Context-Aware Commands**: Implement application-specific commands
4. **Desktop Environment Support**: Add support for GNOME, KDE, XFCE

### Phase 3: User Experience (Week 3-4)
1. **Visual Feedback**: Enhance system tray with command status
2. **Command History**: Add command history and learning
3. **Error Handling**: Implement comprehensive error handling
4. **Performance Optimization**: Optimize for responsiveness

### Phase 4: Customization (Week 4+)
1. **Custom Commands**: Allow users to create custom commands
2. **Configuration GUI**: Add visual command management interface
3. **Import/Export**: Enable sharing of custom command sets
4. **Advanced Features**: Add confirmation dialogs, undo functionality

## Quality Assurance

### Testing Strategy
1. **Unit Tests**: Test individual command classes and processors
2. **Integration Tests**: Test command execution in different contexts
3. **User Experience Tests**: Test with real users for usability
4. **Performance Tests**: Ensure commands execute within time limits

### Error Handling
1. **Graceful Degradation**: Fall back to dictation if command processing fails
2. **Clear Error Messages**: Provide actionable error information
3. **Recovery Mechanisms**: Allow users to retry or correct failed commands
4. **Logging**: Comprehensive logging for debugging and improvement

This design provides a solid foundation for transforming the voice control system from simple dictation into an intelligent command processing system while maintaining the reliability and user experience of the current implementation.
</content>