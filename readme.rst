##############
Voice Control
##############

*Offline Speech to Text for Desktop Linux.* - See `demo video <https://www.youtube.com/watch?v=T7sR-4DFhpQ>`__.

This is a utility that provides simple access speech to text for using in Linux
without being tied to a desktop environment, using the excellent `Whisper <https://github.com/openai/whisper>`__ or `CMU Sphinx <https://cmusphinx.github.io/>`__.

- **Simple**: This is a single file Python script with minimal dependencies.
- **Hackable**: User configuration lets you manipulate text using Python string operations.
- **Zero Overhead**: As this relies on manual activation there are no background processes.

Dictation is accessed manually with a hotkey (Ctrl+Alt+D by default).


Usage
=====

Press the hotkey (Ctrl+Alt+D) to start and stop dictation.

To configure the application, run the UI:

.. code-block:: sh

   python3 voice-control-ui

For details on how this can be used, see:
``voice-control --help`` and ``voice-control begin --help``.


Features
========

- UI for Configuration
- Multi-Engine Support (Whisper, CMU Sphinx)
- Systemd Service
- Voice Commands
- Context-Aware Dictation
- Deeper Desktop Integration
- Accessibility Features
- User Experience Improvements
- Numbers as Digits
- Time Out
- Suspend/Resume

See ``voice-control begin --help`` for details on how to access these options.


Dependencies
============

- Python 3.9 (or newer).
- The Whisper library.
- The CMU Sphinx library.
- An audio recording utility (``parec`` by default).
- An input simulation utility (``xdotool`` by default).


Install
=======

.. code-block:: sh

    ./install.sh

To test dictation, run the script and press the hotkey (Ctrl+Alt+D):

.. code-block:: sh

   python3 voice-control

To configure the application, run the UI:

.. code-block:: sh

    python3 voice-control-ui


Configuration
=============

This is an example of a trivial configuration file which simply makes the input text uppercase.

.. code-block:: python

   # ~/.config/voice-control/voice-control.py
   def voice_control_process(text):
       return text.upper()


Paths
=====

- **Local Configuration**: ``~/.config/voice-control/voice-control.py``
- **Settings**:    ``~/.config/voice-control/settings.ini``
