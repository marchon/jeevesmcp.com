# AGENTS.md - Jeeves Project Guide

This file contains essential information for AI coding agents working on the Jeeves project.

---

## Project Overview

**Jeeves** is an intelligent request router that sits between users and their AI assistant (Kimi/Claude/etc). It uses a local LLM (via Ollama) to classify request complexity and route simple tasks to local execution while escalating complex requests to cloud AI services.

**Key Value Proposition**: Fast local execution for simple commands (shell, file operations) in milliseconds instead of waiting for cloud round-trips.

**Version**: 0.1.0  
**License**: MIT License

---

## Technology Stack

- **Language**: Python 3.8+
- **Production Dependencies**: 
  - `requests>=2.28.0` (only production dependency)
- **Test Dependencies**: `pytest>=7.0.0`, `pytest-cov>=4.0.0`, `pytest-asyncio>=0.21.0`, `responses>=0.23.0`
- **Documentation**: Sphinx with Furo theme, sphinx-copybutton, sphinx-tabs
- **Local LLM Engine**: Ollama (external dependency, auto-installed)
- **Build System**: Dual configuration with `pyproject.toml` (primary) and `setup.py` (legacy support)

---

## Project Structure

```
jeeves/
├── main.py                 # CLI entry point with argparse subcommands (~178 lines)
├── router.py               # Core routing logic (JeevesRouter class, ~544 lines)
├── config.py               # Configuration management (JeevesConfig class, ~531 lines)
├── platform_utils.py       # Cross-platform OS/shell/terminal detection (~450 lines)
├── model_configs.py        # Model-specific optimizations (~500 lines)
├── llm_logger.py           # LLM interaction logging (~400 lines)
├── __init__.py             # Package exports and version info
├── setup.py                # Python package setup (setuptools, legacy support)
├── pyproject.toml          # Modern Python project configuration
├── requirements.txt        # Production Python dependencies
├── pytest.ini             # Pytest configuration
├── install.sh              # Full-featured bash installer (~270 lines)
├── install-oneliner.sh     # Minimal one-liner install script (~68 lines)
├── run_tests.sh            # Bash test runner with auto-setup (~240 lines)
├── run_tests.py            # Python test runner, cross-platform (~401 lines)
├── models/
│   └── suggested_models.json  # Recommended Ollama models with metadata
├── tests/                  # Comprehensive test suite (91 tests)
│   ├── __init__.py         # Test package initialization
│   ├── conftest.py         # Pytest fixtures and mocks
│   ├── test_router.py      # Router tests (38 tests)
│   ├── test_config.py      # Config tests (23 tests)
│   ├── test_main.py        # CLI tests (19 tests)
│   ├── test_integration.py # Integration tests (11 tests)
│   ├── requirements-test.txt # Test dependencies
│   └── README.md           # Test documentation
├── docs/                   # Sphinx documentation
│   ├── conf.py             # Sphinx configuration (Furo theme, platform-aware)
│   ├── requirements.txt    # Documentation build dependencies
│   ├── Makefile            # Build automation
│   ├── index.rst           # Main documentation entry
│   ├── api.rst             # API documentation
│   ├── installation.rst    # Installation guide (platform-specific)
│   ├── platforms.rst       # Platform support guide
│   ├── quickstart.rst      # Quick start guide
│   ├── faq.rst             # FAQ
│   ├── development.rst     # Development guide & progress
│   ├── _static/            # Static assets
│   └── _templates/         # Custom templates
├── README.md               # User-facing documentation
├── LICENSE                 # MIT License
├── .gitignore              # Git ignore patterns
└── AGENTS.md              # This file
```

---

## Core Components

### 1. JeevesRouter (router.py)

The main router class that decides whether to handle requests locally or escalate to cloud AI.

**Key Methods:**
- `route(request: str) -> Dict[str, Any]` - Main routing logic, returns dict with `destination`, `method`, `result`, `should_escalate`
- `handle(request: str) -> str` - Convenience method that returns result or `[JEEVES_ESCALATE]` marker
- `_classify_with_local_llm(request: str)` - Uses Ollama API to classify complexity
- `_execute_local_shell(command: str)` - Executes shell commands via subprocess
- `_read_local_file(filepath: str)` - Reads files with 10MB size limit
- `_list_local_directory(dirpath: str)` - Lists directory contents with emoji indicators
- `_generate_local_response(request: str)` - Generates responses using local LLM

**Routing Logic Flow:**
1. **Pattern Matching** (fastest, 0ms): Checks against `SHELL_PATTERNS` and `FILE_PATTERNS`
2. **Local LLM Classification** (~100ms): Uses Ollama to classify as SIMPLE/MODERATE/COMPLEX/UNCERTAIN
3. **Validation**: Uncertain responses trigger escalation to cloud

**Key Class Attributes:**
- `SHELL_PATTERNS`: Regex patterns for instant shell command recognition (ls, cat, grep, git, etc.)
- `FILE_PATTERNS`: Regex patterns for file operations (read, list, search)
- `UNCERTAINTY_MARKERS`: Phrases indicating local LLM uncertainty (e.g., "i don't know", "uncertain")

### 2. ModelConfigs (model_configs.py)

Model-specific configurations for optimal performance with different LLM families.

**Supported Model Families:**
- **Qwen** (Alibaba) - ChatML format
- **Llama** (Meta) - Llama-2/3 format
- **Phi** (Microsoft) - Phi chat format
- **Gemma** (Google) - Gemma format
- **DeepSeek** - DeepSeek format

**Model-Specific Optimizations:**
- **Prompt Templates**: Different formats for each model family (ChatML, Llama-2, Alpaca, etc.)
- **Generation Parameters**: Optimal temperature, top_p, top_k per model
- **Confidence Thresholds**: Model-specific routing thresholds
  - Small models (0.5B-1.5B): Higher thresholds (0.8) for reliability
  - Medium models (3B-4B): Standard thresholds (0.7)
  - Large models (7B+): Standard thresholds (0.7)
- **Max Tokens**: Size-appropriate limits (small: 256, medium: 512-1024, large: 2048)
- **Stop Sequences**: Model-specific stop tokens

**Key Functions:**
- `format_classification_prompt(model, request)` - Get model-optimized classification prompt
- `format_response_prompt(model, request)` - Get model-optimized response prompt
- `get_classification_params(model)` - Get optimal parameters for classification
- `get_response_params(model)` - Get optimal parameters for response generation
- `get_confidence_thresholds(model)` - Get model-specific routing thresholds
- `get_model_capabilities(model)` - Get capability ratings for routing decisions

**Example Configurations:**
```python
# Qwen 2.5 1.5B - ChatML format
{
    "classification_temperature": 0.1,
    "response_temperature": 0.7,
    "classification_max_tokens": 10,
    "response_max_tokens": 512,
    "stop_sequences": ["<|im_end|>", "<|endoftext|>"],
    "confidence_threshold_simple": 0.7,
    "classification_prompt_template": "qwen"  # Uses ChatML format
}

# Llama 3.2 3B - Llama-3 format
{
    "classification_temperature": 0.1,
    "response_temperature": 0.7,
    "classification_max_tokens": 10,
    "response_max_tokens": 1024,
    "stop_sequences": ["<|eot_id|>", "<|end_of_text|>"],
    "confidence_threshold_simple": 0.7,
    "classification_prompt_template": "llama"  # Uses Llama-3 format
}
```

### 3. LLMLogger (llm_logger.py)

Comprehensive logging system for LLM interactions with timestamp-based log files.

**Key Methods:**
- `start_session(user_command: str)` - Begin logging a new user interaction
- `log_jeeves_decision_prompt(prompt, model, context)` - Log classification prompt to local LLM
- `log_jeeves_decision_response(response, classification, confidence)` - Log classification result
- `log_escalation(reason, target_llm, full_context)` - Log escalation to primary AI
- `log_target_llm_response(target_llm, response, metadata)` - Log response from primary AI
- `log_local_execution(command, result, execution_time_ms)` - Log local command execution
- `end_session(final_result, routing_decision)` - End logging session

**Log Filename Format:** `LLM-LOG-MM:DD:YY:mm:ss:ms.log`
- Example: `LLM-LOG-02:09:26:14:30:25:123.log`

**Log Directory:**
- Linux: `~/.local/share/jeeves/logs/`
- macOS: `~/Library/Logs/jeeves/`
- Windows: `%LOCALAPPDATA%\jeeves\logs\`

**CLI Commands:**
- `jeeves logging on` - Enable logging
- `jeeves logging off` - Disable logging
- `jeeves logging status` - Show status
- `jeeves logging list` - List recent logs
- `jeeves logging view --file FILE` - View specific log
- `jeeves logging clear --keep N` - Clear old logs

**Default:** Logging is **DISABLED** for privacy

### 4. JeevesConfig (config.py)

Manages user configuration, Ollama integration, and model management.

**Configuration Location:** `~/.config/jeeves/config.json`

**Default Configuration Structure:**
```python
{
    "ollama": {
        "host": "http://localhost:11434",
        "autostart": True,
        "autostart_with_kimi": True,
    },
    "jeeves": {
        "default_model": "qwen2.5:1.5b",
        "fallback_threshold": 0.7,
        "timeout_seconds": 30,
        "classification_prompt": "simple",
    },
    "routing": {
        "use_pattern_matching": True,
        "use_local_llm": True,
        "auto_fallback": True,
        "cloud_on_uncertainty": True,
    },
    "logging": {
        "enabled": False,  # LLM interaction logging (default: off for privacy)
        "log_dir": None,   # None = use platform default
        "max_log_files": 100,
    },
    "installed_models": [],
    "last_setup": None,
}
```

**Key Methods:**
- `is_ollama_installed() / is_ollama_running()` - Ollama status checks
- `start_ollama()` - Start Ollama server in background using subprocess.Popen
- `pull_model(name)` - Download model from Ollama registry with streaming progress
- `remove_model(name)` - Remove installed model
- `get_installed_models()` - List installed Ollama models via API
- `get_all_suggested_models()` - Get combined built-in + remote model suggestions

**Interactive Functions:**
- `interactive_setup(config)` - 6-step setup wizard
- `switch_model(config)` - Interactive model switching
- `manage_models(config)` - Model management menu

### 5. Platform Utilities (platform_utils.py)

Cross-platform detection and terminal integration utilities.

**Key Classes:**
- `PlatformInfo` - Container for platform detection results
- `OperatingSystem` - Enum: WINDOWS, MACOS, LINUX, UNKNOWN
- `ShellType` - Enum: BASH, ZSH, FISH, POWERSHELL, CMD, UNKNOWN  
- `TerminalType` - Enum for terminal emulators

**Key Features:**
- **OS Detection**: Windows, macOS, Linux, WSL detection
- **Shell Detection**: Automatic shell type detection from environment
- **Terminal Detection**: Detects GNOME Terminal, iTerm2, Windows Terminal, etc.
- **Terminal Launching**: Open commands in new terminal windows
- **Platform Paths**: Returns appropriate config/install paths for each platform

**Usage:**
```python
from platform_utils import PlatformInfo, get_platform_info, open_in_terminal

# Get platform info
info = get_platform_info()
print(f"OS: {info.os.value}")  # 'linux', 'macos', 'windows'
print(f"Shell: {info.shell.value}")  # 'bash', 'zsh', etc.

# Open in new terminal
open_in_terminal("ollama serve", title="Ollama Server")
```

### 6. CLI Commands (main.py)

Available subcommands:
- `jeeves setup` - Interactive setup wizard (7 steps, includes LLM selection & auto-install)
- `jeeves status` - Show Jeeves and Ollama status
- `jeeves models` - Manage installed models (install/remove/set default)
- `jeeves switch` - Switch default model
- `jeeves route "<request>"` - Route a single request and show result
- `jeeves interactive` - Start interactive chat mode with banner
- `jeeves logging on/off` - Enable/disable LLM interaction logging
- `jeeves logging status` - Show logging status
- `jeeves logging list` - List recent log files
- `jeeves logging view --file FILE` - View a specific log file
- `jeeves logging clear --keep N` - Clear old logs, keeping N most recent

---

## Build and Test Commands

### Installation

**One-Line Install (Production):**
```bash
curl -fsSL https://raw.githubusercontent.com/marchon/jeevesmcp.com/main/install.sh | bash
```

**Development Setup:**
```bash
# Clone repository
git clone https://github.com/marchon/jeevesmcp.com.git ~/.local/share/jeeves
cd ~/.local/share/jeeves

# Install dependencies
pip install -r requirements.txt

# Run directly
python main.py setup
```

### Testing

**Run all tests (auto-installs dependencies and Ollama):**
```bash
./run_tests.sh
```

**Run unit tests only (no Ollama required):**
```bash
./run_tests.sh --quick
# or
pytest tests/ -m "not integration" -v
```

**Run all tests including integration (requires Ollama):**
```bash
./run_tests.sh --all
```

**Run with coverage report:**
```bash
./run_tests.sh --coverage
# Generates: coverage_html/index.html
```

**Manual pytest:**
```bash
pytest tests/ -v                          # All tests
pytest tests/ -m "not integration" -v     # Unit tests only
pytest tests/test_router.py -v            # Specific test file
pytest tests/test_router.py::TestShellPatternMatching::test_simple_shell_commands -v  # Specific test
```

### Documentation

**Build Documentation:**
```bash
cd docs
pip install -r requirements.txt  # Install sphinx, furo, etc.
make html                        # Build HTML docs
# Output: docs/_build/html/
```

---

## Code Style Guidelines

### Docstrings
- Use **Google-style docstrings** with type hints
- Example:
  ```python
  def method(self, param: str) -> Dict[str, Any]:
      """Short description.
      
      Longer description if needed.
      
      Args:
          param: Description of parameter
          
      Returns:
          Dictionary containing results
      """
  ```

### Typing
- Use `typing` module for type annotations: `Optional`, `Dict`, `Any`, `List`, `Tuple`
- Always include return type annotations

### Line Length
- Follow PEP 8 (implied by codebase style, ~100 chars is acceptable)

### String Quotes
- Use **double quotes** for strings
- Use **single quotes** for single characters

### Naming Conventions
- Classes: `PascalCase` (e.g., `JeevesRouter`, `JeevesConfig`)
- Methods/functions: `snake_case` (e.g., `route()`, `handle()`)
- Constants: `UPPER_CASE` (e.g., `SHELL_PATTERNS`, `DEFAULT_CONFIG`)
- Private methods: `_leading_underscore` (e.g., `_execute_local_shell()`)

### Error Handling
- Use try-except blocks with specific exception types
- Return meaningful error messages in local execution results
- Log errors with descriptive messages (print statements for CLI feedback)
- Use emoji indicators for user-facing messages (✅, ❌, ⚠️, 🎩)

---

## Testing Strategy

**Current State**: Comprehensive test suite with **91 tests**.

### Test Suite Structure

```
tests/
├── conftest.py              # Shared fixtures
│   ├── mock_config          # Mock JeevesConfig
│   ├── temp_directory       # Temporary path fixture
│   ├── sample_shell_commands # Shell command test data
│   ├── sample_file_commands  # File command test data
│   └── mock_ollama_response  # OLLama response mocks
├── test_router.py           # 38 tests - Routing logic, pattern matching, file operations
├── test_config.py           # 23 tests - Config management, Ollama integration
├── test_main.py             # 19 tests - CLI commands, argument parsing
└── test_integration.py      # 11 tests - End-to-end with real Ollama
```

### Test Markers

- `@pytest.mark.integration` - Tests requiring Ollama (slow, external dependency)
- `@pytest.mark.slow` - Tests that take longer to run

### Writing New Tests

1. **Unit Tests**: Mock external dependencies (Ollama, network)
   ```python
   @patch('router.requests.post')
   def test_something(self, mock_post):
       mock_post.return_value = Mock(status_code=200, json=lambda: {...})
       # ... test code
   ```

2. **Integration Tests**: Mark with `@pytest.mark.integration`
   ```python
   @pytest.mark.integration
   def test_with_real_ollama(self):
       # ... test code
   ```

3. **Test Class Naming**: `Test<FeatureName>`
4. **Test Method Naming**: `test_<what>_<condition>`

---

## Development Conventions

### Adding New Shell/Command Patterns

When adding new patterns to router.py:

1. **Shell patterns** (router.py, `SHELL_PATTERNS` list):
   ```python
   SHELL_PATTERNS = [
       r'^your_command\b',  # \b ensures word boundary
       # ...
   ]
   ```

2. **File operation patterns** (router.py, `FILE_PATTERNS` list):
   ```python
   FILE_PATTERNS = [
       (r'^your_pattern["\']?(.+?)["\']?$', 'handler_name'),
       # ...
   ]
   ```

3. **Handler methods**: Follow naming convention `_<action>_local_<target>`
   - Example: `_read_local_file()`, `_list_local_directory()`

### Configuration Changes

When adding new config options:
1. Add to `DEFAULT_CONFIG` dictionary in config.py
2. Handle migration in `load_config()` (already merges with defaults)
3. Update `interactive_setup()` if user-configurable
4. Update tests in `test_config.py`

### Adding a New CLI Command

1. Add command handler function in `main.py` (e.g., `def cmd_newcmd(args):`)
2. Create subparser in `main()` function
3. Set defaults with `set_defaults(func=cmd_newcmd)`
4. Add tests in `test_main.py`
5. Update help text in `print_banner()` if needed

### Modifying Routing Logic

1. Locate relevant method in `JeevesRouter` class
2. Update classification logic or add new pattern checks
3. Return format must include: `destination`, `method`, `should_escalate`
4. Ensure `handle()` method properly interprets results

---

## Security Considerations

1. **Shell Command Execution**: 
   - Commands are executed via `subprocess.run(shell=True)` - this is intentional for flexibility
   - User is expected to be the system owner (local personal assistant use case)
   - No command filtering beyond pattern matching
   
2. **File Access**:
   - File operations respect filesystem permissions
   - 10MB file size limit for local reading (configurable in `_read_local_file()`)
   - Path expansion with `Path(filepath).expanduser()`

3. **Ollama API**:
   - Default binds to localhost only (http://localhost:11434)
   - No authentication on local Ollama by design
   - Timeout defaults to 30 seconds

4. **Configuration**:
   - Config stored in user's home directory (`~/.config/jeeves/`)
   - JSON format - no sensitive data expected
   - File permissions follow umask

---

## Model Recommendations

**Default model**: `qwen2.5:1.5b` (1GB, fast, good balance)

Categories (from `models/suggested_models.json`):

| Category | Models | Best For |
|----------|--------|----------|
| **Ultra Fast** | qwen2.5:0.5b (400MB), phi3:mini | Routing only, minimal RAM (1GB) |
| **Balanced** | qwen2.5:1.5b, llama3.2:3b, gemma2:2b | **Recommended default** |
| **Capable** | qwen2.5:7b, llama3.2:8b, deepseek-r1:1.5b | Complex classification, reasoning |
| **Experimental** | nemotron-mini:4b, smollm2:1.7b | Testing new models |

### Adding New Model Suggestions

Edit `models/suggested_models.json`:
```json
{
  "categories": {
    "your_category": [
      {
        "name": "model:name",
        "size": "XGB",
        "speed": "Fast",
        "desc": "Description",
        "recommended_for": ["use_case"],
        "min_ram": "XGB"
      }
    ]
  }
}
```

---

## Release Checklist

For maintainers:

- [ ] Update version in `setup.py`
- [ ] Update version in `__init__.py`
- [ ] Update version in `pyproject.toml`
- [ ] Update version in `main.py` (banner)
- [ ] Update `README.md` with new features
- [ ] Update documentation in `docs/`
- [ ] Update `AGENTS.md` if project structure or conventions changed
- [ ] Update `models/suggested_models.json` if needed
- [ ] Test install script on fresh system
- [ ] Tag release in git

---

## Troubleshooting Common Issues

1. **"Ollama not running"**:
   - Check: `curl http://localhost:11434/api/tags`
   - Start: `ollama serve`

2. **"jeeves: command not found"**:
   - Add to PATH: `export PATH="$HOME/.local/bin:$PATH"`
   - Or restart terminal: `source ~/.bashrc` or `source ~/.zshrc`

3. **Model download fails**:
   - Pull manually: `ollama pull qwen2.5:1.5b`
   - Check Ollama status: `ollama list`

4. **Python import errors**:
   - Ensure dependencies installed: `pip install -r requirements.txt`
   - Check Python version: `python3 --version` (need 3.8+)

5. **Tests failing**:
   - Check virtual environment: `source .venv/bin/activate`
   - Reinstall deps: `pip install -r requirements.txt -r tests/requirements-test.txt`
   - Run with verbose: `pytest tests/ -v --tb=long`

6. **Permission denied errors**:
   - Check directory ownership: `ls -la ~/.local/share/jeeves/`
   - Fix ownership: `sudo chown -R $USER:$USER ~/.local/share/jeeves/`

---

## Architecture Notes

### Dual Build Configuration

The project maintains both `pyproject.toml` (modern standard) and `setup.py` (legacy support):

- **pyproject.toml**: Primary configuration, used by pip, pytest, coverage
- **setup.py**: Legacy support, entry point for editable installs

Both specify:
- Package name: `jeeves` (pyproject.toml) / `jeeves-router` (setup.py)
- Version: `0.1.0`
- Entry point: `jeeves=main:main`

### Import Structure

The `__init__.py` uses a try/except pattern for flexible imports:
```python
try:
    from .router import JeevesRouter      # Package import
    from .config import JeevesConfig
except ImportError:
    from router import JeevesRouter       # Direct execution
    from config import JeevesConfig
```

### Ollama Integration Flow

1. Router initialization checks if Ollama is running
2. If not running and `autostart=True`, starts Ollama in background
3. Classification requests go to `http://localhost:11434/api/generate`
4. Model management uses both API (`/api/tags`, `/api/pull`) and CLI (`ollama rm`)

---

## Resources

- **Repository**: https://github.com/marchon/jeevesmcp.com
- **Issues**: https://github.com/marchon/jeevesmcp.com/issues
- **Discussions**: https://github.com/marchon/jeevesmcp.com/discussions
- **Ollama**: https://ollama.com
