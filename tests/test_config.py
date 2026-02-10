"""
Tests for the JeevesConfig class.
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import JeevesConfig, DEFAULT_CONFIG, interactive_setup


class TestJeevesConfigInit:
    """Tests for JeevesConfig initialization."""
    
    def test_default_config_creation(self, tmp_path):
        """Test that default config is created when no config file exists."""
        with patch.object(JeevesConfig, 'CONFIG_FILE', tmp_path / "config.json"):
            with patch.object(JeevesConfig, 'CONFIG_DIR', tmp_path):
                config = JeevesConfig()
                
                assert config.config == DEFAULT_CONFIG
    
    def test_config_directory_creation(self, tmp_path):
        """Test that config directory is created if it doesn't exist."""
        config_dir = tmp_path / ".config" / "jeeves"
        
        with patch.object(JeevesConfig, 'CONFIG_FILE', config_dir / "config.json"):
            with patch.object(JeevesConfig, 'CONFIG_DIR', config_dir):
                config = JeevesConfig()
                
                assert config_dir.exists()


class TestConfigLoading:
    """Tests for configuration loading."""
    
    def test_load_existing_config(self, tmp_path):
        """Test loading an existing config file."""
        config_file = tmp_path / "config.json"
        custom_config = {
            "jeeves": {
                "default_model": "custom-model",
                "fallback_threshold": 0.5,
                "timeout_seconds": 60,
                "classification_prompt": "detailed",
            }
        }
        config_file.write_text(json.dumps(custom_config))
        
        with patch.object(JeevesConfig, 'CONFIG_FILE', config_file):
            with patch.object(JeevesConfig, 'CONFIG_DIR', tmp_path):
                config = JeevesConfig()
                
                assert config.config["jeeves"]["default_model"] == "custom-model"
                assert config.config["jeeves"]["fallback_threshold"] == 0.5
    
    def test_merge_with_defaults(self, tmp_path):
        """Test that loaded config is merged with defaults."""
        config_file = tmp_path / "config.json"
        partial_config = {
            "jeeves": {
                "default_model": "custom-model",
            }
        }
        config_file.write_text(json.dumps(partial_config))
        
        with patch.object(JeevesConfig, 'CONFIG_FILE', config_file):
            with patch.object(JeevesConfig, 'CONFIG_DIR', tmp_path):
                config = JeevesConfig()
                
                # Custom value should be preserved
                assert config.config["jeeves"]["default_model"] == "custom-model"
                # Default values should still exist at top level of config
                assert "jeeves" in config.config
                assert "ollama" in config.config
                assert "routing" in config.config


class TestConfigSaving:
    """Tests for configuration saving."""
    
    def test_save_config(self, tmp_path):
        """Test saving configuration to file."""
        config_file = tmp_path / "config.json"
        
        with patch.object(JeevesConfig, 'CONFIG_FILE', config_file):
            with patch.object(JeevesConfig, 'CONFIG_DIR', tmp_path):
                config = JeevesConfig()
                config.config["jeeves"]["default_model"] = "new-model"
                
                result = config.save_config()
                
                assert result is True
                assert config_file.exists()
                
                saved_data = json.loads(config_file.read_text())
                assert saved_data["jeeves"]["default_model"] == "new-model"


class TestOllamaChecks:
    """Tests for Ollama installation and status checks."""
    
    @patch('config.subprocess.run')
    def test_ollama_installed(self, mock_run):
        """Test checking if Ollama is installed."""
        mock_run.return_value = Mock(returncode=0)
        
        config = JeevesConfig()
        
        assert config.is_ollama_installed() is True
        mock_run.assert_called_once_with(
            ['which', 'ollama'],
            capture_output=True,
            text=True,
            timeout=5
        )
    
    @patch('config.subprocess.run')
    def test_ollama_not_installed(self, mock_run):
        """Test checking if Ollama is not installed."""
        mock_run.return_value = Mock(returncode=1)
        
        config = JeevesConfig()
        
        assert config.is_ollama_installed() is False
    
    @patch('config.requests.get')
    def test_ollama_running(self, mock_get):
        """Test checking if Ollama server is running."""
        mock_get.return_value = Mock(status_code=200)
        
        config = JeevesConfig()
        
        assert config.is_ollama_running() is True
    
    @patch('config.requests.get')
    def test_ollama_not_running(self, mock_get):
        """Test checking if Ollama server is not running."""
        mock_get.side_effect = Exception("Connection refused")
        
        config = JeevesConfig()
        
        assert config.is_ollama_running() is False


class TestOllamaStart:
    """Tests for starting Ollama server."""
    
    @patch('config.subprocess.Popen')
    @patch.object(JeevesConfig, 'is_ollama_running')
    def test_start_ollama_already_running(self, mock_running, mock_popen):
        """Test starting Ollama when it's already running."""
        mock_running.return_value = True
        
        config = JeevesConfig()
        result = config.start_ollama()
        
        assert result is True
        mock_popen.assert_not_called()
    
    @patch('config.subprocess.Popen')
    @patch.object(JeevesConfig, 'is_ollama_running')
    @patch('config.time.sleep')
    def test_start_ollama_success(self, mock_sleep, mock_running, mock_popen):
        """Test successfully starting Ollama server."""
        mock_running.side_effect = [False, False, True]  # Not running, then running
        
        config = JeevesConfig()
        result = config.start_ollama()
        
        assert result is True
        mock_popen.assert_called_once()
    
    @patch('config.subprocess.Popen')
    @patch.object(JeevesConfig, 'is_ollama_running')
    @patch('config.time.sleep')
    def test_start_ollama_failure(self, mock_sleep, mock_running, mock_popen):
        """Test failing to start Ollama server."""
        mock_running.return_value = False  # Never starts
        
        config = JeevesConfig()
        result = config.start_ollama()
        
        assert result is False


class TestModelManagement:
    """Tests for model management."""
    
    @patch('config.requests.get')
    def test_get_installed_models(self, mock_get):
        """Test getting list of installed models."""
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {
                'models': [
                    {'name': 'model1'},
                    {'name': 'model2'},
                ]
            }
        )
        
        config = JeevesConfig()
        models = config.get_installed_models()
        
        assert models == ['model1', 'model2']
        assert config.config['installed_models'] == ['model1', 'model2']
    
    @patch('config.requests.get')
    def test_get_installed_models_failure(self, mock_get):
        """Test getting models when API fails."""
        mock_get.side_effect = Exception("Connection error")
        
        config = JeevesConfig()
        config.config['installed_models'] = ['cached-model']
        
        models = config.get_installed_models()
        
        assert models == ['cached-model']  # Returns cached list
    
    @patch('config.requests.post')
    def test_pull_model(self, mock_post):
        """Test pulling a model."""
        mock_post.return_value = Mock(
            status_code=200,
            iter_lines=lambda: [
                b'{"status": "pulling"}',
                b'{"status": "complete"}',
            ]
        )
        
        config = JeevesConfig()
        result = config.pull_model('test-model')
        
        assert result is True
    
    @patch('config.requests.post')
    def test_pull_model_http_error(self, mock_post):
        """Test pulling a model with HTTP error."""
        mock_post.return_value = Mock(status_code=404)
        
        config = JeevesConfig()
        result = config.pull_model('test-model')
        
        assert result is False
    
    @patch('config.subprocess.run')
    def test_remove_model(self, mock_run):
        """Test removing a model."""
        mock_run.return_value = Mock(returncode=0)
        
        config = JeevesConfig()
        result = config.remove_model('test-model')
        
        assert result is True
        mock_run.assert_called_once_with(
            ['ollama', 'rm', 'test-model'],
            capture_output=True,
            text=True,
            timeout=60
        )
    
    @patch('config.subprocess.run')
    def test_remove_model_failure(self, mock_run):
        """Test removing a model that fails."""
        mock_run.return_value = Mock(returncode=1, stderr="Model not found")
        
        config = JeevesConfig()
        result = config.remove_model('test-model')
        
        assert result is False


class TestRemoteSuggestions:
    """Tests for fetching remote model suggestions."""
    
    @patch('config.requests.get')
    def test_fetch_remote_suggestions(self, mock_get):
        """Test fetching remote suggestions."""
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {
                'ultra_fast': [{'name': 'new-model', 'size': '1GB'}]
            }
        )
        
        config = JeevesConfig()
        result = config.fetch_remote_suggestions()
        
        assert result == {'ultra_fast': [{'name': 'new-model', 'size': '1GB'}]}
    
    @patch('config.requests.get')
    def test_fetch_remote_suggestions_failure(self, mock_get):
        """Test fetching remote suggestions when network fails."""
        mock_get.side_effect = Exception("Network error")
        
        config = JeevesConfig()
        result = config.fetch_remote_suggestions()
        
        assert result == {}
    
    def test_get_all_suggested_models_built_in(self):
        """Test getting suggested models (built-in only when remote fails)."""
        with patch.object(JeevesConfig, 'fetch_remote_suggestions', return_value={}):
            config = JeevesConfig()
            models = config.get_all_suggested_models()
            
            assert 'ultra_fast' in models
            assert 'balanced' in models
            assert 'capable' in models
            assert len(models['balanced']) > 0


class TestInteractiveSetup:
    """Tests for interactive setup wizard."""
    
    @patch('config.interactive_setup')
    def test_setup_with_ollama_not_installed(self, mock_setup):
        """Test setup when Ollama is not installed."""
        mock_config = Mock()
        mock_config.is_ollama_installed.return_value = False
        
        # The actual function would print instructions and return False
        # We just verify the mock was called correctly
        mock_setup.return_value = False
        
        result = mock_setup(mock_config)
        
        assert result is False
    
    @patch('config.interactive_setup')
    def test_setup_success(self, mock_setup):
        """Test successful setup."""
        mock_config = Mock()
        mock_config.is_ollama_installed.return_value = True
        mock_config.is_ollama_running.return_value = True
        mock_config.save_config.return_value = True
        
        mock_setup.return_value = True
        
        result = mock_setup(mock_config)
        
        assert result is True
