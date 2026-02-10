Development Guide
=================

This document tracks completed work, ongoing changes, and future todos for the Jeeves project.

**Last Updated:** 2026-02-09  
**Current Phase:** LLM Logging & Enhanced Setup

----

Completed Work
--------------

2026-02-09 - Model-Specific Optimizations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Summary**
Added model-specific configurations to optimize prompts, parameters, and routing decisions for different LLM families (Qwen, Llama, Phi, Gemma, DeepSeek).

**What Was Done**

1. **Created Model Configs Module** (``model_configs.py``)
   - Model family detection (Qwen, Llama, Phi, Gemma, DeepSeek, etc.)
   - Family-specific prompt templates:
     - **Qwen**: ChatML format with ``<|im_start|>``/``<|im_end|>`` tokens
     - **Llama**: Llama-3 format with ``<|start_header_id|>`` tokens
     - **Phi**: Phi format with ``<|user|>``/``<|assistant|>`` tokens
     - **Gemma**: Gemma format with ``<start_of_turn>``/``<end_of_turn>``
     - **DeepSeek**: Standard format with stop sequences
   - Model-specific generation parameters:
     - Temperature (classification: 0.05-0.1, response: 0.5-0.7)
     - Max tokens (classification: 5-10, response: 256-2048 based on model size)
     - Top_p, top_k, stop sequences
   - Capability ratings per model for routing decisions
   - Confidence thresholds adjusted by model size:
     - Small models (0.5B-1.5B): Higher thresholds (0.75-0.8) for reliability
     - Medium/Large models (3B+): Standard thresholds (0.7)

2. **Updated Router** (``router.py``)
   - Classification now uses model-optimized prompts
   - Response generation uses model-optimized prompts
   - API calls use model-specific parameters
   - Routing thresholds adapted per model capabilities

**New Files Created**

.. code-block:: text

   model_configs.py           # Model-specific optimization configurations

----

2026-02-09 - LLM Interaction Logging & Enhanced Setup
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Summary**
Added comprehensive LLM interaction logging system with timestamp-based log files, enhanced setup wizard with automatic Ollama installation and LLM selection.

**What Was Done**

1. **Created LLM Logging Module** (``llm_logger.py``)
   - ``LLMLogger`` class for comprehensive interaction logging
   - Timestamp-based log filenames: ``LLM-LOG-MM:DD:YY:mm:ss:ms.log``
   - Logs: user commands, system context, LLM prompts/responses, escalations
   - CLI commands: ``jeeves logging on/off/status/list/view/clear``
   - Configurable via config (default: disabled for privacy)

2. **Enhanced Setup Wizard** (``config.py``)
   - Automatic Ollama installation (macOS/Linux)
   - Interactive LLM model selection with categorized options
   - Logging configuration during setup
   - Better user guidance throughout setup process

3. **Updated Router** (``router.py``)
   - Integrated logging calls at all routing decision points
   - Fine-tuned messaging for routing decisions
   - Clear explanations when escalating to primary AI
   - Execution time tracking for local commands

4. **Added CLI Commands** (``main.py``)
   - ``jeeves logging on`` - Enable interaction logging
   - ``jeeves logging off`` - Disable logging
   - ``jeeves logging status`` - Show logging status
   - ``jeeves logging list`` - List recent log files
   - ``jeeves logging view --file FILE`` - View specific log
   - ``jeeves logging clear --keep N`` - Clear old logs

**Files Changed**

- ``router.py`` - Integrated logging and improved messaging
- ``main.py`` - Added logging subcommands
- ``config.py`` - Enhanced setup wizard

**New Files Created**

.. code-block:: text

   llm_logger.py              # LLM interaction logging module

----

2026-02-09 - Platform Detection & Documentation Update
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Summary**
Added comprehensive platform detection, shell detection, and updated Sphinx documentation.

**What Was Done**

1. **Created Platform Detection Module** (``platform_utils.py``)
   - ``PlatformInfo`` class for comprehensive platform detection
   - OS detection: Windows, macOS, Linux, WSL
   - Shell detection: Bash, Zsh, Fish, PowerShell, CMD
   - Terminal detection: GNOME Terminal, iTerm2, Windows Terminal, etc.
   - Platform-specific paths for config, install, and binary directories
   - Terminal launching functionality

2. **Updated Sphinx Documentation**
   - ``docs/platforms.rst`` - Comprehensive platform support guide
   - ``docs/installation.rst`` - Platform-specific installation instructions
   - ``docs/conf.py`` - Enhanced with platform detection and dynamic content
   - Added MyST parser for Markdown support
   - Moved ``progress-to-date.md`` to ``docs/development.rst``

3. **Platform-Specific Features**
   - Auto-detection of terminal emulator for launching commands
   - Shell configuration file detection (.bashrc, .zshrc, etc.)
   - Windows Terminal integration
   - iTerm2 AppleScript support
   - WSL detection and compatibility

**Files Changed**

- ``docs/conf.py`` - Enhanced configuration with platform awareness
- ``docs/installation.rst`` - Added platform tabs and OS-specific instructions
- ``docs/index.rst`` - Added platforms and development to toctree

**New Files Created**

.. code-block:: text

   platform_utils.py          # Platform detection utilities
   docs/platforms.rst         # Platform support guide
   docs/development.rst       # This development guide

----

2026-02-09 - Test Suite Implementation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Summary**
Created a comprehensive test suite for the Jeeves intelligent request router project.

**What Was Done**

1. **Created Test Infrastructure**
   - ``tests/`` directory structure
   - ``pytest.ini`` - Pytest configuration
   - ``pyproject.toml`` - Project configuration with coverage settings
   - ``tests/requirements-test.txt`` - Test dependencies
   - ``tests/__init__.py`` - Test package initialization
   - ``tests/conftest.py`` - Shared pytest fixtures

2. **Created Test Runners** (2 files)
   - ``run_tests.sh`` - Bash test runner with full setup automation
   - ``run_tests.py`` - Python test runner with cross-platform support

3. **Created Test Files** (4 files, 91 total tests)
   - ``tests/test_router.py`` - 38 tests for routing logic
   - ``tests/test_config.py`` - 23 tests for configuration management
   - ``tests/test_main.py`` - 19 tests for CLI interface
   - ``tests/test_integration.py`` - 11 integration tests

4. **Bug Fixes**
   - Fixed syntax error in ``config.py`` line 194 - missing ``except`` block for JSON parsing
   - Fixed ``__init__.py`` to handle both relative and absolute imports

5. **Documentation**
   - ``tests/README.md`` - Comprehensive test documentation
   - Updated ``AGENTS.md`` - Added testing strategy section
   - Updated ``.gitignore`` - Added test artifacts patterns

**Test Categories**

.. list-table::
   :header-rows: 1

   * - Category
     - Count
     - Description
   * - Unit Tests
     - 80
     - Mocked external dependencies
   * - Integration Tests
     - 11
     - Require Ollama server
   * - **Total**
     - **91**
     -

----

Current Project State
---------------------

Working Components
^^^^^^^^^^^^^^^^^^

- ✅ JeevesRouter - Core routing logic
- ✅ JeevesConfig - Configuration management
- ✅ CLI (main.py) - Command-line interface
- ✅ Ollama integration - Model management
- ✅ Test Suite - Comprehensive test coverage
- ✅ Platform Detection - Cross-platform support
- ✅ Sphinx Documentation - User and developer guides

Known Issues
^^^^^^^^^^^^

- None at this time

Test Results
^^^^^^^^^^^^

- Unit tests: 80/80 passing
- Integration tests: 11/11 passing (when Ollama available)
- Code coverage: ~40% (focusing on critical paths)

----

Todo List
---------

High Priority
^^^^^^^^^^^^^

- [ ] **CI/CD**: Set up GitHub Actions for automated testing
- [ ] **Packaging**: Publish to PyPI for easy installation
- [ ] **Integration**: Test platform detection on all target platforms

Medium Priority
^^^^^^^^^^^^^^^

- [ ] **Feature**: Add more shell command patterns
- [ ] **Feature**: Add file search functionality
- [ ] **Enhancement**: Improve error messages
- [ ] **Tests**: Add more edge case tests for file operations
- [ ] **Docs**: Add platform detection API documentation

Low Priority
^^^^^^^^^^^^

- [ ] **Refactor**: Extract magic numbers to constants
- [ ] **Style**: Add type hints to all functions
- [ ] **Docs**: Add architecture diagrams
- [ ] **Performance**: Benchmark routing speed

Backlog
^^^^^^^

- [ ] **Feature**: Web interface for configuration
- [ ] **Feature**: Plugin system for custom handlers
- [ ] **Feature**: Conversation history
- [ ] **Feature**: Multi-model support with automatic selection

----

Change Log
----------

Format
^^^^^^

Each entry should include:

- Date
- Summary of changes
- Files modified
- Files created
- Breaking changes (if any)

Recent Entries
^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Date
     - Change
     - Files
   * - 2026-02-09
     - Model-specific optimizations
     - ``model_configs.py``
   * - 2026-02-09
     - LLM interaction logging
     - ``llm_logger.py``, logging CLI commands
   * - 2026-02-09
     - Platform detection & docs update
     - ``platform_utils.py``, ``docs/*.rst``
   * - 2026-02-09
     - Test suite implementation
     - ``tests/``, ``run_tests.*``, ``pytest.ini``

----

Notes & Decisions
-----------------

Technical Decisions
^^^^^^^^^^^^^^^^^^^

1. **Platform Detection**: Created dedicated ``platform_utils.py`` module
2. **Model Optimization**: Created ``model_configs.py`` with family-specific prompts
3. **LLM Logging**: Created ``llm_logger.py`` for debugging (default: disabled)
4. **Documentation**: Using Sphinx with MyST for Markdown support
5. **Testing Framework**: Using pytest with fixtures and mocking
6. **Test Isolation**: Unit tests mock Ollama, integration tests use real Ollama
7. **Coverage Tool**: pytest-cov with HTML report generation
8. **Virtual Environment**: Test runners create ``.venv/`` automatically

Design Patterns
^^^^^^^^^^^^^^^

- Fixtures in ``conftest.py`` for shared test resources
- Mocking external dependencies (Ollama, network) in unit tests
- ``@pytest.mark.integration`` decorator for integration tests
- Platform detection via enums (OperatingSystem, ShellType, TerminalType)
- Singleton pattern for PlatformInfo

----

Metrics
-------

Code Statistics
^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Metric
     - Value
   * - Total Lines of Code
     - ~2,600
   * - Number of Python Modules
     - 7
   * - Number of Test Files
     - 4
   * - Number of Tests
     - 91
   * - Test Coverage
     - ~40%
   * - Dependencies
     - 1 production + 4 dev

Test Breakdown
^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Component
     - Tests
   * - Router
     - 38
   * - Config
     - 23
   * - CLI/Main
     - 19
   * - Integration
     - 11

Platform Support
^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Platform
     - Status
   * - Linux
     - ✅ Fully Supported
   * - macOS
     - ✅ Fully Supported
   * - Windows (WSL)
     - ✅ Fully Supported
   * - Windows (Native)
     - ⚠️ Experimental

----

How to Use This Document
------------------------

1. **When completing work**: Add new entry under "Completed Work" with date
2. **When making changes**: Update "Change Log" section
3. **When adding todos**: Add to appropriate priority section
4. **When completing todos**: Move to "Completed Work" and check off
5. **Regular updates**: Update "Last Updated" date and "Current Phase"

----

Quick Links
-----------

- Test Runner: ``./run_tests.sh`` or ``python3 run_tests.py``
- Main Code: ``router.py``, ``config.py``, ``main.py``, ``platform_utils.py``
- Documentation: ``README.md``, ``AGENTS.md``, ``tests/README.md``, ``docs/``
- Platform Utils: ``python3 platform_utils.py`` (prints detected platform info)
