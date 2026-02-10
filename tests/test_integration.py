"""
Integration tests for Jeeves.

These tests require Ollama to be running and may take longer to execute.
Mark them with @pytest.mark.integration to skip them by default.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from router import JeevesRouter
from config import JeevesConfig

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def real_config():
    """Create a real JeevesConfig (may require Ollama)."""
    return JeevesConfig()


class TestOllamaConnection:
    """Tests that require Ollama to be running."""
    
    def test_ollama_is_installed(self, real_config):
        """Verify Ollama is installed on the system."""
        assert real_config.is_ollama_installed(), "Ollama should be installed"
    
    def test_ollama_is_running(self, real_config):
        """Verify Ollama server is running."""
        assert real_config.is_ollama_running(), "Ollama server should be running"
    
    def test_can_list_models(self, real_config):
        """Test that we can list installed models."""
        models = real_config.get_installed_models()
        assert isinstance(models, list), "Should return a list of models"


class TestRouterWithOllama:
    """Integration tests for JeevesRouter with real Ollama."""
    
    @pytest.fixture
    def router(self):
        """Create a real JeevesRouter instance."""
        return JeevesRouter()
    
    def test_execute_real_shell_command(self, router):
        """Test executing a real shell command."""
        result = router._execute_local_shell("echo 'integration test'")
        
        assert "integration test" in result
    
    def test_list_real_directory(self, router):
        """Test listing a real directory."""
        result = router._list_local_directory(".")
        
        assert len(result) > 0
        # Should contain test files
        assert "test_" in result or ".py" in result or "conftest" in result
    
    def test_read_real_file(self, router):
        """Test reading a real file."""
        result = router._read_local_file("README.md")
        
        if "not found" not in result.lower():
            assert len(result) > 0
    
    def test_route_shell_command_integration(self, router):
        """Test routing a shell command through the full pipeline."""
        result = router.route("echo hello")
        
        assert result['destination'] == 'local'
        assert result['should_escalate'] is False
        assert "hello" in result.get('result', '')


class TestConfigPersistence:
    """Tests for configuration persistence."""
    
    def test_config_save_and_load(self, tmp_path):
        """Test that config can be saved and loaded."""
        config_file = tmp_path / "test_config.json"
        
        with patch.object(JeevesConfig, 'CONFIG_FILE', config_file):
            with patch.object(JeevesConfig, 'CONFIG_DIR', tmp_path):
                # Create and modify config
                config = JeevesConfig()
                config.config["jeeves"]["default_model"] = "test-model"
                config.save_config()
                
                # Load config in new instance
                config2 = JeevesConfig()
                
                assert config2.config["jeeves"]["default_model"] == "test-model"


class TestErrorHandling:
    """Tests for error handling in real scenarios."""
    
    @pytest.fixture
    def router(self):
        return JeevesRouter()
    
    def test_read_nonexistent_file(self, router):
        """Test reading a file that doesn't exist."""
        result = router._read_local_file("/this/path/does/not/exist/file.txt")
        
        assert "not found" in result.lower() or "error" in result.lower()
    
    def test_list_nonexistent_directory(self, router):
        """Test listing a directory that doesn't exist."""
        result = router._list_local_directory("/this/path/does/not/exist")
        
        assert "not found" in result.lower() or "error" in result.lower()
    
    def test_invalid_shell_command(self, router):
        """Test executing an invalid shell command."""
        result = router._execute_local_shell("thiscommanddoesnotexist12345")
        
        # Should either have exit code or stderr
        assert "exit code" in result.lower() or "error" in result.lower() or "not found" in result.lower()
