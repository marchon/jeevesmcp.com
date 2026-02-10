"""
Pytest configuration and fixtures for Jeeves tests.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_config():
    """Create a mock JeevesConfig for testing."""
    config = Mock()
    config.config = {
        "ollama": {
            "host": "http://localhost:11434",
            "autostart": False,
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
        "installed_models": ["qwen2.5:1.5b"],
        "last_setup": None,
    }
    config.is_ollama_running.return_value = True
    config.is_ollama_installed.return_value = True
    return config


@pytest.fixture
def temp_directory(tmp_path):
    """Provide a temporary directory for file operations testing."""
    return tmp_path


@pytest.fixture
def sample_shell_commands():
    """Sample shell commands for testing pattern matching."""
    return {
        "simple": ["ls -la", "pwd", "whoami", "date", "uname -a"],
        "with_args": [
            "ls -la /tmp",
            "cat README.md",
            "grep -r pattern .",
            "find . -name '*.py'",
        ],
        "git": ["git status", "git log --oneline", "git diff"],
        "system": ["ps aux", "df -h", "free -m", "uptime"],
    }


@pytest.fixture
def sample_file_commands():
    """Sample file operation commands for testing."""
    return {
        "read_file": [
            "read README.md",
            "read file 'test.txt'",
            'read file "config.json"',
            "show me the content of file.txt",
            "open file document.txt",
            "cat file notes.txt",
            "display file output.log",
            "view file script.py",
        ],
        "list_dir": [
            "list files in /tmp",
            "list files in .",
            "what's in /home",
            "what is in directory",
        ],
    }


@pytest.fixture
def mock_ollama_response():
    """Mock response from Ollama API."""
    return {
        "SIMPLE": {"response": "SIMPLE", "confidence": 1.0},
        "MODERATE": {"response": "MODERATE", "confidence": 1.0},
        "COMPLEX": {"response": "COMPLEX", "confidence": 1.0},
        "UNCERTAIN": {"response": "UNCERTAIN", "confidence": 0.0},
    }
