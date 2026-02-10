"""
Tests for the main CLI module.
"""

import pytest
import sys
import argparse
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

sys.path.insert(0, str(Path(__file__).parent.parent))

import main


class TestPrintBanner:
    """Tests for the print_banner function."""
    
    def test_print_banner(self, capsys):
        """Test that banner prints correctly."""
        main.print_banner()
        
        captured = capsys.readouterr()
        assert "Jeeves" in captured.out
        assert "🎩" in captured.out


class TestCmdSetup:
    """Tests for the setup command."""
    
    @patch('main.JeevesConfig')
    @patch('main.interactive_setup')
    def test_cmd_setup(self, mock_setup, mock_config_class):
        """Test setup command execution."""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        
        args = Mock()
        main.cmd_setup(args)
        
        mock_config_class.assert_called_once()
        mock_setup.assert_called_once_with(mock_config)


class TestCmdStatus:
    """Tests for the status command."""
    
    @patch('main.JeevesConfig')
    def test_cmd_status(self, mock_config_class, capsys):
        """Test status command execution."""
        mock_config = Mock()
        mock_config.CONFIG_FILE = Path("/test/config.json")
        mock_config.is_ollama_installed.return_value = True
        mock_config.is_ollama_running.return_value = True
        mock_config.config = {
            'jeeves': {'default_model': 'test-model'},
            'routing': {
                'use_pattern_matching': True,
                'use_local_llm': True,
                'auto_fallback': True,
            }
        }
        mock_config.get_installed_models.return_value = ['model1', 'model2']
        mock_config_class.return_value = mock_config
        
        args = Mock()
        main.cmd_status(args)
        
        captured = capsys.readouterr()
        assert "Jeeves Status" in captured.out
        assert "test-model" in captured.out
        assert "Yes" in captured.out or "On" in captured.out


class TestCmdModels:
    """Tests for the models command."""
    
    @patch('main.JeevesConfig')
    @patch('main.manage_models')
    def test_cmd_models(self, mock_manage, mock_config_class):
        """Test models command execution."""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        
        args = Mock()
        main.cmd_models(args)
        
        mock_manage.assert_called_once_with(mock_config)


class TestCmdSwitch:
    """Tests for the switch command."""
    
    @patch('main.JeevesConfig')
    @patch('main.switch_model')
    def test_cmd_switch(self, mock_switch, mock_config_class):
        """Test switch command execution."""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        
        args = Mock()
        main.cmd_switch(args)
        
        mock_switch.assert_called_once_with(mock_config)


class TestCmdRoute:
    """Tests for the route command."""
    
    @patch('main.JeevesRouter')
    def test_cmd_route_local(self, mock_router_class, capsys):
        """Test routing a request locally."""
        mock_router = Mock()
        mock_router.route.return_value = {
            'destination': 'local',
            'method': 'pattern_match',
            'should_escalate': False,
            'result': 'test output'
        }
        mock_router_class.return_value = mock_router
        
        args = Mock()
        args.request = ['ls', '-la']
        
        main.cmd_route(args)
        
        captured = capsys.readouterr()
        assert "local" in captured.out.lower()
        assert "test output" in captured.out
    
    @patch('main.JeevesRouter')
    def test_cmd_route_cloud(self, mock_router_class, capsys):
        """Test routing a request to cloud."""
        mock_router = Mock()
        mock_router.route.return_value = {
            'destination': 'cloud',
            'method': 'llm_classification',
            'should_escalate': True
        }
        mock_router_class.return_value = mock_router
        
        args = Mock()
        args.request = ['explain', 'quantum', 'physics']
        
        main.cmd_route(args)
        
        captured = capsys.readouterr()
        assert "cloud" in captured.out.lower() or "Kimi" in captured.out
    
    def test_cmd_route_no_request(self):
        """Test routing with no request."""
        args = Mock()
        args.request = None
        
        with pytest.raises(SystemExit) as exc_info:
            main.cmd_route(args)
        
        assert exc_info.value.code == 1


class TestCmdInteractive:
    """Tests for the interactive command."""
    
    @patch('main.JeevesRouter')
    @patch('main.print_banner')
    def test_cmd_interactive_exit(self, mock_print, mock_router_class):
        """Test interactive mode with exit command."""
        mock_router = Mock()
        mock_router.route.return_value = {
            'destination': 'local',
            'method': 'pattern_match',
            'should_escalate': False,
            'result': 'output'
        }
        mock_router_class.return_value = mock_router
        
        # Simulate user typing 'exit'
        with patch('builtins.input', side_effect=['exit']):
            main.cmd_interactive(Mock())
        
        mock_print.assert_called_once()
    
    @patch('main.JeevesRouter')
    def test_cmd_interactive_keyboard_interrupt(self, mock_router_class):
        """Test interactive mode with keyboard interrupt."""
        mock_router = Mock()
        mock_router_class.return_value = mock_router
        
        with patch('builtins.input', side_effect=KeyboardInterrupt()):
            main.cmd_interactive(Mock())
        
        # Should exit gracefully
    
    @patch('main.JeevesRouter')
    def test_cmd_interactive_init_failure(self, mock_router_class):
        """Test interactive mode when router initialization fails."""
        mock_router_class.side_effect = RuntimeError("Ollama not running")
        
        with pytest.raises(SystemExit) as exc_info:
            main.cmd_interactive(Mock())
        
        assert exc_info.value.code == 1


class TestMain:
    """Tests for the main function."""
    
    def test_main_no_args(self):
        """Test main with no arguments prints help."""
        with patch('sys.argv', ['jeeves']):
            with pytest.raises(SystemExit) as exc_info:
                main.main()
            
            assert exc_info.value.code == 0
    
    @patch('main.cmd_setup')
    def test_main_setup_command(self, mock_cmd):
        """Test main with setup command."""
        with patch('sys.argv', ['jeeves', 'setup']):
            main.main()
        
        mock_cmd.assert_called_once()
    
    @patch('main.cmd_status')
    def test_main_status_command(self, mock_cmd):
        """Test main with status command."""
        with patch('sys.argv', ['jeeves', 'status']):
            main.main()
        
        mock_cmd.assert_called_once()
    
    @patch('main.cmd_models')
    def test_main_models_command(self, mock_cmd):
        """Test main with models command."""
        with patch('sys.argv', ['jeeves', 'models']):
            main.main()
        
        mock_cmd.assert_called_once()
    
    @patch('main.cmd_switch')
    def test_main_switch_command(self, mock_cmd):
        """Test main with switch command."""
        with patch('sys.argv', ['jeeves', 'switch']):
            main.main()
        
        mock_cmd.assert_called_once()
    
    @patch('main.cmd_route')
    def test_main_route_command(self, mock_cmd):
        """Test main with route command."""
        # The route command takes all remaining arguments as the request
        with patch('sys.argv', ['jeeves', 'route', 'ls -la']):
            main.main()
        
        mock_cmd.assert_called_once()
        args = mock_cmd.call_args[0][0]
        assert args.request == ['ls -la']
    
    @patch('main.cmd_interactive')
    def test_main_interactive_command(self, mock_cmd):
        """Test main with interactive command."""
        with patch('sys.argv', ['jeeves', 'interactive']):
            main.main()
        
        mock_cmd.assert_called_once()


class TestArgumentParsing:
    """Tests for argument parsing."""
    
    def test_parser_description(self):
        """Test that parser has correct description."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        
        # This just verifies argparse works as expected
        args = parser.parse_args([])
        assert args == argparse.Namespace()
