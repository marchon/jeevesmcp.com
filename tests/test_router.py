"""
Tests for the JeevesRouter class.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from router import JeevesRouter


class TestJeevesRouterInit:
    """Tests for JeevesRouter initialization."""
    
    def test_init_with_running_ollama(self, mock_config):
        """Test router initialization when Ollama is running."""
        mock_config.is_ollama_running.return_value = True
        
        router = JeevesRouter(config=mock_config)
        
        assert router.config == mock_config
        mock_config.is_ollama_running.assert_called_once()
    
    def test_init_starts_ollama_when_autostart_enabled(self, mock_config):
        """Test that router starts Ollama when autostart is enabled."""
        mock_config.is_ollama_running.return_value = False
        mock_config.config['ollama']['autostart'] = True
        mock_config.start_ollama.return_value = True
        
        router = JeevesRouter(config=mock_config)
        
        mock_config.start_ollama.assert_called_once()
    
    def test_init_raises_when_ollama_not_running_and_no_autostart(self, mock_config):
        """Test that router raises error when Ollama not running and autostart disabled."""
        mock_config.is_ollama_running.return_value = False
        mock_config.config['ollama']['autostart'] = False
        
        with pytest.raises(RuntimeError, match="Ollama is not running"):
            JeevesRouter(config=mock_config)


class TestShellPatternMatching:
    """Tests for shell command pattern matching."""
    
    @pytest.fixture
    def router(self, mock_config):
        mock_config.is_ollama_running.return_value = True
        return JeevesRouter(config=mock_config)
    
    def test_simple_shell_commands(self, router):
        """Test matching of simple shell commands."""
        commands = ["ls", "pwd", "whoami", "date", "uptime", "env", "clear", "exit"]
        
        for cmd in commands:
            assert router._matches_shell_pattern(cmd), f"Should match: {cmd}"
    
    def test_shell_commands_with_args(self, router):
        """Test matching of shell commands with arguments."""
        commands = [
            "ls -la",
            "ls /tmp",
            "cat README.md",
            "grep pattern file.txt",
            "find . -name '*.py'",
            "ps aux",
            "df -h",
            "free -m",
        ]
        
        for cmd in commands:
            assert router._matches_shell_pattern(cmd), f"Should match: {cmd}"
    
    def test_non_shell_commands(self, router):
        """Test that non-shell commands don't match."""
        commands = [
            "hello world",
            "what is the weather",
            "explain quantum physics",
            "write a poem",
        ]
        
        for cmd in commands:
            assert not router._matches_shell_pattern(cmd), f"Should not match: {cmd}"
    
    def test_git_commands(self, router):
        """Test matching of git commands."""
        commands = [
            "git status",
            "git log --oneline",
            "git diff HEAD~1",
            "git commit -m 'test'",
        ]
        
        for cmd in commands:
            assert router._matches_shell_pattern(cmd), f"Should match: {cmd}"
    
    def test_pattern_matching_disabled(self, router, mock_config):
        """Test that pattern matching can be disabled."""
        mock_config.config['routing']['use_pattern_matching'] = False
        
        assert not router._matches_shell_pattern("ls -la")
        assert not router._matches_shell_pattern("pwd")


class TestFilePatternMatching:
    """Tests for file operation pattern matching."""
    
    @pytest.fixture
    def router(self, mock_config):
        mock_config.is_ollama_running.return_value = True
        return JeevesRouter(config=mock_config)
    
    def test_read_file_patterns(self, router):
        """Test read file patterns."""
        patterns = [
            ("read README.md", ("read_file", ("README.md",))),
            ("read file 'test.txt'", ("read_file", ("test.txt",))),
            ('read file "config.json"', ("read_file", ("config.json",))),
            ("show me the content of file.txt", ("read_file", ("file.txt",))),
            ("open file document.txt", ("read_file", ("document.txt",))),
            ("cat file notes.txt", ("read_file", ("notes.txt",))),
            ("display file output.log", ("read_file", ("output.log",))),
            ("view file script.py", ("read_file", ("script.py",))),
        ]
        
        for command, expected in patterns:
            result = router._matches_file_pattern(command)
            assert result is not None, f"Should match: {command}"
            assert result[0] == expected[0], f"Action should be {expected[0]} for: {command}"
    
    def test_list_directory_patterns(self, router):
        """Test list directory patterns."""
        patterns = [
            ("list files in /tmp", ("list_dir", ("/tmp",))),
            ("list files in .", ("list_dir", (".",))),
            ("what's in /home", ("list_dir", ("/home",))),
            ("what is in directory", ("list_dir", ("directory",))),
        ]
        
        for command, expected in patterns:
            result = router._matches_file_pattern(command)
            assert result is not None, f"Should match: {command}"
            assert result[0] == expected[0], f"Action should be {expected[0]} for: {command}"
    
    def test_no_file_pattern_match(self, router):
        """Test commands that don't match file patterns."""
        commands = ["hello world", "explain this", "run the script"]
        
        for cmd in commands:
            assert router._matches_file_pattern(cmd) is None, f"Should not match: {cmd}"
    
    def test_file_pattern_disabled(self, router, mock_config):
        """Test that file pattern matching can be disabled."""
        mock_config.config['routing']['use_pattern_matching'] = False
        
        assert router._matches_file_pattern("read README.md") is None


class TestLocalShellExecution:
    """Tests for local shell command execution."""
    
    @pytest.fixture
    def router(self, mock_config):
        mock_config.is_ollama_running.return_value = True
        return JeevesRouter(config=mock_config)
    
    def test_execute_echo_command(self, router):
        """Test executing a simple echo command."""
        result = router._execute_local_shell("echo 'Hello World'")
        
        assert "Hello World" in result
    
    def test_execute_pwd_command(self, router):
        """Test executing pwd command."""
        result = router._execute_local_shell("pwd")
        
        assert Path(result.strip()).exists()
    
    def test_execute_with_error(self, router):
        """Test executing a command that returns an error."""
        result = router._execute_local_shell("cat /nonexistent/file")
        
        assert "exit code" in result.lower() or "error" in result.lower() or "stderr" in result.lower()
    
    def test_command_timeout(self, router):
        """Test command timeout handling."""
        result = router._execute_local_shell("sleep 65")
        
        assert "timed out" in result.lower() or "timeout" in result.lower()


class TestFileOperations:
    """Tests for local file operations."""
    
    @pytest.fixture
    def router(self, mock_config):
        mock_config.is_ollama_running.return_value = True
        return JeevesRouter(config=mock_config)
    
    def test_read_existing_file(self, router, temp_directory):
        """Test reading an existing file."""
        test_file = temp_directory / "test.txt"
        test_file.write_text("Hello, World!")
        
        result = router._read_local_file(str(test_file))
        
        assert result == "Hello, World!"
    
    def test_read_nonexistent_file(self, router):
        """Test reading a file that doesn't exist."""
        result = router._read_local_file("/nonexistent/path/file.txt")
        
        assert "not found" in result.lower() or "error" in result.lower()
    
    def test_read_directory(self, router, temp_directory):
        """Test reading a directory (should fail gracefully)."""
        result = router._read_local_file(str(temp_directory))
        
        assert "directory" in result.lower() or "error" in result.lower()
    
    def test_list_directory(self, router, temp_directory):
        """Test listing directory contents."""
        (temp_directory / "file1.txt").write_text("content1")
        (temp_directory / "file2.txt").write_text("content2")
        (temp_directory / "subdir").mkdir()
        
        result = router._list_local_directory(str(temp_directory))
        
        assert "file1.txt" in result
        assert "file2.txt" in result
        assert "subdir" in result
    
    def test_list_nonexistent_directory(self, router):
        """Test listing a directory that doesn't exist."""
        result = router._list_local_directory("/nonexistent/path")
        
        assert "not found" in result.lower() or "error" in result.lower()
    
    def test_list_file_as_directory(self, router, temp_directory):
        """Test listing a file as if it were a directory."""
        test_file = temp_directory / "file.txt"
        test_file.write_text("content")
        
        result = router._list_local_directory(str(test_file))
        
        assert "not a directory" in result.lower() or "error" in result.lower()


class TestUncertaintyDetection:
    """Tests for uncertainty detection in LLM responses."""
    
    @pytest.fixture
    def router(self, mock_config):
        mock_config.is_ollama_running.return_value = True
        return JeevesRouter(config=mock_config)
    
    def test_uncertainty_markers(self, router):
        """Test detection of uncertainty markers."""
        uncertain_responses = [
            "I don't know the answer",
            "I'm not sure about this",
            "I cannot help with that",
            "This is uncertain",
            "I'm confused by your request",
            "This is unclear to me",
            "This is beyond my capabilities",
            "I'm unable to do this",
        ]
        
        for response in uncertain_responses:
            assert router._is_uncertain_response(response), f"Should detect uncertainty: {response}"
    
    def test_confident_responses(self, router):
        """Test that confident responses are not flagged as uncertain."""
        confident_responses = [
            "The answer is 42",
            "Here is the file content",
            "I can help you with that",
            "The solution is simple",
        ]
        
        for response in confident_responses:
            assert not router._is_uncertain_response(response), f"Should not detect uncertainty: {response}"


class TestConfidenceExtraction:
    """Tests for confidence score extraction."""
    
    @pytest.fixture
    def router(self, mock_config):
        mock_config.is_ollama_running.return_value = True
        return JeevesRouter(config=mock_config)
    
    def test_exact_match_confidence(self, router):
        """Test confidence for exact matches."""
        assert router._extract_confidence("SIMPLE") == 1.0
        assert router._extract_confidence("MODERATE") == 1.0
        assert router._extract_confidence("COMPLEX") == 1.0
    
    def test_partial_match_confidence(self, router):
        """Test confidence for partial matches."""
        assert router._extract_confidence("The category is SIMPLE") == 0.7
        assert router._extract_confidence("This is MODERATE complexity") == 0.7
    
    def test_no_match_confidence(self, router):
        """Test confidence for non-matching responses."""
        assert router._extract_confidence("I don't know") == 0.0
        assert router._extract_confidence("UNCERTAIN") == 0.0


class TestRouteMethod:
    """Tests for the main route method."""
    
    @pytest.fixture
    def router(self, mock_config):
        mock_config.is_ollama_running.return_value = True
        return JeevesRouter(config=mock_config)
    
    @patch.object(JeevesRouter, '_execute_local_shell')
    def test_route_shell_command(self, mock_execute, router):
        """Test routing a shell command."""
        mock_execute.return_value = "file1.txt file2.txt"
        
        result = router.route("ls -la")
        
        assert result['destination'] == 'local'
        assert result['method'] == 'pattern_match'
        assert result['should_escalate'] is False
        mock_execute.assert_called_once_with("ls -la")
    
    @patch.object(JeevesRouter, '_read_local_file')
    def test_route_file_read(self, mock_read, router):
        """Test routing a file read request."""
        mock_read.return_value = "File content here"
        
        result = router.route("read README.md")
        
        assert result['destination'] == 'local'
        assert result['method'] == 'pattern_match'
        assert result['should_escalate'] is False
    
    @patch.object(JeevesRouter, '_classify_with_local_llm')
    @patch.object(JeevesRouter, '_generate_local_response')
    def test_route_simple_classification(self, mock_generate, mock_classify, router):
        """Test routing with SIMPLE classification."""
        mock_classify.return_value = {
            'classification': 'SIMPLE',
            'confidence': 1.0,
            'raw_response': 'SIMPLE'
        }
        mock_generate.return_value = "Local response"
        
        result = router.route("What time is it?")
        
        assert result['destination'] == 'local'
        assert result['method'] == 'llm_classification'
        assert result['should_escalate'] is False
    
    @patch.object(JeevesRouter, '_classify_with_local_llm')
    def test_route_complex_classification(self, mock_classify, router):
        """Test routing with COMPLEX classification."""
        mock_classify.return_value = {
            'classification': 'COMPLEX',
            'confidence': 1.0,
            'raw_response': 'COMPLEX'
        }
        
        result = router.route("Explain quantum physics")
        
        assert result['destination'] == 'cloud'
        assert result['method'] == 'llm_classification'
        assert result['should_escalate'] is True
    
    @patch.object(JeevesRouter, '_classify_with_local_llm')
    @patch.object(JeevesRouter, '_generate_local_response')
    def test_route_uncertain_response_fallback(self, mock_generate, mock_classify, router):
        """Test fallback to cloud when local response is uncertain."""
        mock_classify.return_value = {
            'classification': 'SIMPLE',
            'confidence': 1.0,
            'raw_response': 'SIMPLE'
        }
        mock_generate.return_value = "I don't know the answer"
        
        result = router.route("Some question")
        
        assert result['destination'] == 'cloud'
        assert result['method'] == 'fallback_uncertainty'
        assert result['should_escalate'] is True


class TestHandleMethod:
    """Tests for the handle convenience method."""
    
    @pytest.fixture
    def router(self, mock_config):
        mock_config.is_ollama_running.return_value = True
        return JeevesRouter(config=mock_config)
    
    @patch.object(JeevesRouter, '_execute_local_shell')
    def test_handle_local_result(self, mock_execute, router):
        """Test handle returning local result."""
        mock_execute.return_value = "output"
        
        result = router.handle("ls")
        
        assert result == "output"
    
    @patch.object(JeevesRouter, 'route')
    def test_handle_escalation(self, mock_route, router):
        """Test handle returning escalation marker."""
        mock_route.return_value = {
            'destination': 'cloud',
            'method': 'llm_classification',
            'should_escalate': True
        }
        
        result = router.handle("Complex question")
        
        assert "[JEEVES_ESCALATE]" in result


class TestClassificationWithLocalLLM:
    """Tests for LLM classification."""
    
    @pytest.fixture
    def router(self, mock_config):
        mock_config.is_ollama_running.return_value = True
        return JeevesRouter(config=mock_config)
    
    @patch('router.requests.post')
    def test_successful_classification(self, mock_post, router):
        """Test successful LLM classification."""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {'response': 'SIMPLE'}
        )
        
        result = router._classify_with_local_llm("test request")
        
        assert result['classification'] == 'SIMPLE'
        assert result['confidence'] == 1.0
    
    @patch('router.requests.post')
    def test_classification_timeout(self, mock_post, router):
        """Test classification timeout handling."""
        import requests
        mock_post.side_effect = requests.Timeout()
        
        result = router._classify_with_local_llm("test request")
        
        assert result['classification'] == 'UNCERTAIN'
        assert 'timeout' in result.get('error', '').lower()
    
    @patch('router.requests.post')
    def test_classification_http_error(self, mock_post, router):
        """Test classification HTTP error handling."""
        mock_post.return_value = Mock(status_code=500)
        
        result = router._classify_with_local_llm("test request")
        
        assert result['classification'] == 'UNCERTAIN'
    
    def test_classification_disabled(self, router, mock_config):
        """Test that classification can be disabled."""
        mock_config.config['routing']['use_local_llm'] = False
        
        result = router._classify_with_local_llm("test request")
        
        assert result['classification'] == 'UNCERTAIN'
        assert result['confidence'] == 0
