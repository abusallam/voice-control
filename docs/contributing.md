# Contributing to Voice Control for Linux

Thank you for your interest in contributing to Voice Control! This guide will help you get started with contributing to this community-driven project.

## 🎯 Project Goals

Voice Control for Linux aims to provide:
- **Reliable** voice control that works consistently
- **Privacy-focused** local processing without cloud dependencies
- **Cross-platform** support for major Linux distributions
- **User-friendly** installation and configuration
- **Community-driven** development and maintenance

## 🚀 Quick Start for Contributors

### 1. Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/voice-control.git
cd voice-control

# Create development environment
python3 -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy

# Install in development mode
pip install -e .
```

### 2. Run Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=voice_control

# Run specific test file
pytest tests/test_core.py
```

### 3. Code Quality Checks

```bash
# Format code
black voice_control/ tests/

# Lint code
flake8 voice_control/ tests/

# Type checking
mypy voice_control/
```

## 📋 Development Guidelines

### Code Style

- **Python Style**: Follow PEP 8 guidelines
- **Formatting**: Use `black` for automatic code formatting
- **Line Length**: Maximum 88 characters (black default)
- **Imports**: Use `isort` for import organization
- **Type Hints**: Add type hints for all public functions

### Code Quality

- **Linting**: Code must pass `flake8` checks
- **Type Checking**: Use `mypy` for static type checking
- **Documentation**: All public functions need docstrings
- **Testing**: New features require corresponding tests

### Git Workflow

1. **Create Feature Branch**: `git checkout -b feature/your-feature-name`
2. **Make Changes**: Implement your feature or fix
3. **Test**: Ensure all tests pass
4. **Commit**: Use clear, descriptive commit messages
5. **Push**: Push your branch to your fork
6. **Pull Request**: Create a PR with detailed description

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add speech recognition backend for Whisper
fix: resolve system tray crash on KDE
docs: update installation guide for Fedora
test: add unit tests for audio processing
refactor: simplify configuration loading
```

## 🧪 Testing

### Test Structure

```
tests/
├── test_core.py          # Core functionality tests
├── test_speech.py        # Speech recognition tests
├── test_gui.py           # GUI component tests
├── test_system.py        # System integration tests
└── fixtures/             # Test data and fixtures
```

### Writing Tests

```python
import unittest
from voice_control.core.engine import VoiceControlEngine

class TestVoiceControlEngine(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.engine = VoiceControlEngine()
    
    def test_engine_initialization(self):
        """Test that engine initializes correctly"""
        self.assertIsNotNone(self.engine)
        self.assertFalse(self.engine.is_running)
    
    def tearDown(self):
        """Clean up after tests"""
        if self.engine.is_running:
            self.engine.stop()
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test class
pytest tests/test_core.py::TestVoiceControlEngine

# Run with coverage report
pytest --cov=voice_control --cov-report=html
```

## 📚 Documentation

### Documentation Structure

- **README.md**: Project overview and quick start
- **docs/installation.md**: Detailed installation instructions
- **docs/configuration.md**: Configuration options and examples
- **docs/troubleshooting.md**: Common issues and solutions
- **docs/contributing.md**: This file
- **docs/architecture.md**: Technical architecture details

### Writing Documentation

- Use clear, concise language
- Include practical examples
- Test all code examples
- Update documentation when changing functionality
- Use proper Markdown formatting

### Docstring Format

```python
def process_audio(audio_data: bytes, sample_rate: int = 16000) -> Optional[str]:
    """Process audio data for speech recognition.
    
    Args:
        audio_data: Raw audio data in bytes
        sample_rate: Audio sample rate in Hz (default: 16000)
    
    Returns:
        Recognized text string, or None if recognition failed
    
    Raises:
        AudioProcessingError: If audio data is invalid
        
    Example:
        >>> audio = load_audio_file("test.wav")
        >>> text = process_audio(audio, 44100)
        >>> print(text)
        "Hello world"
    """
```

## 🐛 Bug Reports

### Before Reporting

1. Check existing issues for duplicates
2. Test with the latest version
3. Follow the troubleshooting guide
4. Gather system information

### Bug Report Template

Use the GitHub issue template and include:

- **System Information**: OS, Python version, desktop environment
- **Steps to Reproduce**: Clear, numbered steps
- **Expected vs Actual Behavior**: What should happen vs what happens
- **Error Messages**: Full error messages and stack traces
- **Logs**: Relevant application logs

## 💡 Feature Requests

### Before Requesting

1. Check existing feature requests
2. Consider if it fits the project goals
3. Think about implementation complexity
4. Consider backwards compatibility

### Feature Request Guidelines

- **Clear Use Case**: Explain who benefits and how
- **Implementation Ideas**: Suggest how it could work
- **Alternatives**: Consider other approaches
- **Priority**: Indicate importance level

## 🔧 Areas for Contribution

### High Priority

- **Speech Recognition Backends**: Implement proven speech recognition libraries
- **Cross-Distribution Testing**: Test on various Linux distributions
- **Documentation**: Improve user and developer documentation
- **Bug Fixes**: Fix reported issues and improve stability

### Medium Priority

- **Performance Optimization**: Improve resource usage and speed
- **GUI Improvements**: Enhance user interface and experience
- **Accessibility**: Improve accessibility features
- **Internationalization**: Add support for multiple languages

### Low Priority

- **Advanced Features**: Plugin system, mobile integration
- **Packaging**: Create distribution packages (deb, rpm, AUR)
- **CI/CD**: Improve automated testing and deployment
- **Monitoring**: Add performance and usage monitoring

## 🏗️ Architecture Overview

### Project Structure

```
voice-control/
├── voice_control/           # Main application package
│   ├── core/               # Core engine and configuration
│   ├── speech/             # Speech recognition backends
│   ├── gui/                # GUI components
│   └── system/             # System integration
├── tests/                  # Test suite
├── docs/                   # Documentation
├── examples/               # Usage examples
└── .github/                # GitHub templates and workflows
```

### Key Components

- **Engine**: Main application controller
- **Speech Router**: Manages speech recognition backends
- **System Tray**: GUI integration with desktop
- **Service Manager**: Systemd service management
- **Resource Manager**: Memory and resource cleanup
- **Error Handler**: Centralized error handling

## 🤝 Community Guidelines

### Code of Conduct

Please read and follow our [Code of Conduct](../CODE_OF_CONDUCT.md).

### Communication

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Pull Requests**: Code contributions and reviews

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and quality checks
2. **Code Review**: Maintainers review code for quality and fit
3. **Testing**: Contributors test changes on their systems
4. **Documentation**: Ensure documentation is updated
5. **Merge**: Approved changes are merged to main branch

## 📞 Getting Help

### For Contributors

- **Documentation**: Check the docs/ directory
- **Issues**: Search existing issues for similar problems
- **Discussions**: Ask questions in GitHub Discussions
- **Code**: Look at existing code for examples

### For Users

- **Installation**: Follow the installation guide
- **Configuration**: Check the configuration documentation
- **Troubleshooting**: Use the troubleshooting guide
- **Support**: Create an issue for bugs or problems

## 🎉 Recognition

Contributors are recognized in:
- **README**: Major contributors listed
- **Releases**: Contributors mentioned in release notes
- **GitHub**: Contributor statistics and graphs

Thank you for contributing to Voice Control for Linux! Your contributions help make Linux more accessible through voice control technology.