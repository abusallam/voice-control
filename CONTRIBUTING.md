# Contributing to Voice Control for Linux

Thank you for your interest in contributing to Voice Control for Linux! This document provides guidelines for contributing to the project.

## 🚀 Quick Start for Contributors

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/voice-control.git
   cd voice-control
   ```

2. **Set up Development Environment**
   ```bash
   # Create virtual environment
   python3 -m venv .venv
   source .venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Install development tools
   pip install black flake8 pytest pytest-cov
   ```

3. **Verify Setup**
   ```bash
   python3 verify_installation.py
   ```

4. **Test the Application**
   ```bash
   ./voice-control-ui
   ```

## 🎯 Ways to Contribute

### 1. Bug Reports
- Use the [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md)
- Include system information (OS, Python version, desktop environment)
- Provide steps to reproduce the issue
- Include relevant logs and error messages

### 2. Feature Requests
- Use the [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md)
- Describe the problem you're trying to solve
- Explain your proposed solution
- Consider implementation complexity and user impact

### 3. Code Contributions
- Fix bugs or implement new features
- Improve documentation
- Add tests for existing functionality
- Optimize performance

### 4. Documentation
- Improve installation guides
- Add troubleshooting solutions
- Create usage examples
- Translate documentation

## 📝 Development Guidelines

### Code Style

We follow Python best practices and PEP 8:

```bash
# Format code with black
black voice_control/ tests/

# Check style with flake8
flake8 voice_control/ tests/

# Type checking (optional but recommended)
mypy voice_control/
```

### Code Standards

1. **Python Version**: Support Python 3.8+
2. **Dependencies**: Keep dependencies minimal and well-justified
3. **Error Handling**: Comprehensive error handling with user-friendly messages
4. **Logging**: Use appropriate logging levels
5. **Documentation**: Docstrings for all public functions and classes

### Testing

All contributions should include appropriate tests:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=voice_control --cov-report=html

# Test specific components
pytest tests/test_core.py -v
```

### Test Guidelines

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test component interactions
3. **System Tests**: Test end-to-end functionality
4. **Mock External Dependencies**: Use mocks for audio, system calls, etc.

## 🔄 Contribution Workflow

### 1. Before You Start

1. **Check existing issues** to avoid duplicate work
2. **Discuss major changes** in an issue before implementing
3. **Fork the repository** and create a feature branch

### 2. Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run tests
   pytest tests/
   
   # Test installation
   python3 verify_installation.py
   
   # Test functionality
   ./voice-control-ui
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add voice command processing"
   ```

### 3. Submitting Changes

1. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request**
   - Use the [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md)
   - Provide clear description of changes
   - Link related issues
   - Include testing information

3. **Respond to feedback**
   - Address review comments
   - Update tests and documentation
   - Keep the PR up to date with main branch

## 🏗️ Project Architecture

### Core Components

```
voice_control/
├── core/           # Core engine and configuration
├── speech/         # Speech recognition backends
├── gui/           # System tray and notifications
└── system/        # Service management and integration
```

### Key Design Principles

1. **Modularity**: Components should be loosely coupled
2. **Extensibility**: Easy to add new speech backends or features
3. **Reliability**: Comprehensive error handling and recovery
4. **User Experience**: Simple installation and intuitive interface
5. **Privacy**: All processing happens locally

## 🎨 Feature Development Guidelines

### Adding New Features

1. **Start with an issue** describing the feature
2. **Design the interface** before implementation
3. **Consider backward compatibility**
4. **Add comprehensive tests**
5. **Update documentation**

### Speech Recognition Backends

To add a new speech recognition backend:

1. **Inherit from base backend**
   ```python
   from voice_control.speech.base_backend import SpeechBackend
   
   class NewBackend(SpeechBackend):
       def recognize(self, audio_data: bytes) -> str:
           # Implementation here
           pass
   ```

2. **Register in speech router**
3. **Add configuration options**
4. **Include comprehensive tests**
5. **Update documentation**

### GUI Components

For GUI contributions:

1. **Support both PyQt5 and tkinter fallback**
2. **Follow system theme and conventions**
3. **Ensure accessibility compliance**
4. **Test on different desktop environments**

## 🐛 Debugging and Troubleshooting

### Development Debugging

1. **Enable debug logging**
   ```bash
   voice-control --log-level DEBUG
   ```

2. **Check service logs**
   ```bash
   journalctl --user -u voice-control -f
   ```

3. **Test components individually**
   ```python
   # Test speech recognition
   python3 -c "
   from voice_control.speech.speech_router import SpeechRouter
   router = SpeechRouter()
   print(router.get_available_backends())
   "
   ```

### Common Issues

1. **Audio Problems**: Check PulseAudio/PipeWire configuration
2. **Permission Issues**: Ensure user-space installation
3. **Dependency Conflicts**: Use virtual environments
4. **Service Issues**: Check systemd user service status

## 📋 Pull Request Checklist

Before submitting a pull request, ensure:

- [ ] Code follows project style guidelines
- [ ] All tests pass (`pytest tests/`)
- [ ] New functionality includes tests
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] PR description explains the changes
- [ ] Related issues are linked
- [ ] No breaking changes (or clearly documented)

## 🏷️ Commit Message Guidelines

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(speech): add new whisper backend
fix(gui): resolve system tray icon disappearing
docs(readme): update installation instructions
test(core): add tests for resource manager
```

## 🤝 Community Guidelines

### Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please read our [Code of Conduct](CODE_OF_CONDUCT.md).

### Communication

- **Be respectful** and constructive in discussions
- **Ask questions** if you're unsure about anything
- **Help others** when you can
- **Share knowledge** and learn from the community

### Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check docs/ directory first
- **Code Comments**: Read inline documentation

## 🎯 Priority Areas for Contribution

### High Priority
1. **Speech Recognition Improvements** - Better accuracy and performance
2. **Voice Command Processing** - Beyond simple dictation
3. **Configuration GUI** - Visual settings interface
4. **Cross-Platform Testing** - More Linux distributions

### Medium Priority
1. **Plugin System** - Extensible command architecture
2. **Performance Optimization** - Reduce resource usage
3. **Accessibility Features** - Better accessibility support
4. **Documentation Improvements** - More examples and guides

### Future Goals
1. **Multi-language Support** - International users
2. **Voice Training** - Personalized recognition
3. **Mobile Integration** - Companion apps
4. **Enterprise Features** - Business use cases

## 📚 Resources

### Documentation
- [Installation Guide](docs/installation.md)
- [Configuration Guide](docs/configuration.md)
- [Troubleshooting Guide](docs/troubleshooting.md)
- [Architecture Overview](docs/architecture.md)

### External Resources
- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Conventional Commits](https://conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [OpenAI Whisper Documentation](https://github.com/openai/whisper)

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- GitHub contributor statistics

Thank you for contributing to Voice Control for Linux! Your contributions help make voice control accessible to the Linux community.

---

**Questions?** Open an issue or start a discussion. We're here to help!