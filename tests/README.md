# Jeeves Test Suite

This directory contains the comprehensive test suite for Jeeves - the intelligent request router.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Pytest fixtures and configuration
├── test_router.py           # Tests for JeevesRouter (38 tests)
├── test_config.py           # Tests for JeevesConfig (22 tests)
├── test_main.py             # Tests for CLI main module (20 tests)
├── test_integration.py      # Integration tests (11 tests)
├── requirements-test.txt    # Test dependencies
└── README.md                # This file
```

## Running Tests

### Quick Start

Run all unit tests (excludes integration tests):
```bash
./run_tests.sh
```

Or using Python:
```bash
python3 run_tests.py
```

### Run Options

```bash
# Run all tests including integration tests (requires Ollama)
./run_tests.sh --all

# Run with coverage report
./run_tests.sh --coverage

# Run specific test file
python3 -m pytest tests/test_router.py -v

# Run specific test
python3 -m pytest tests/test_router.py::TestShellPatternMatching::test_simple_shell_commands -v

# Run only quick tests (skip integration and slow tests)
python3 run_tests.py --quick
```

### Manual Setup

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r tests/requirements-test.txt

# Run tests
pytest tests/ -v
```

## Test Categories

### Unit Tests (80 tests)

These tests mock external dependencies (Ollama, network requests) and run quickly.

**test_router.py** - Tests for routing logic:
- Router initialization
- Shell pattern matching
- File operation pattern matching
- Local shell execution
- File operations (read, list)
- Uncertainty detection
- Confidence extraction
- Route method behavior
- Handle method behavior
- LLM classification

**test_config.py** - Tests for configuration management:
- Config initialization
- Config loading and saving
- Ollama installation checks
- Ollama server status
- Starting Ollama
- Model management (list, pull, remove)
- Remote model suggestions
- Interactive setup

**test_main.py** - Tests for CLI interface:
- Banner printing
- Setup command
- Status command
- Models command
- Switch command
- Route command
- Interactive mode
- Main entry point
- Argument parsing

### Integration Tests (11 tests)

These tests require Ollama to be installed and running. They test actual functionality with real dependencies.

**test_integration.py**:
- Ollama connection tests
- Router with real Ollama
- Real shell command execution
- Real file operations
- Config persistence
- Error handling with real scenarios

## Test Markers

- `integration` - Tests that require Ollama (marked with `@pytest.mark.integration`)
- `slow` - Tests that take longer to run

## Fixtures

Common fixtures are defined in `conftest.py`:

- `mock_config` - Mock JeevesConfig for testing
- `temp_directory` - Temporary directory for file operations
- `sample_shell_commands` - Sample shell commands for pattern testing
- `sample_file_commands` - Sample file commands for pattern testing
- `mock_ollama_response` - Mock Ollama API responses

## Coverage

To generate a coverage report:

```bash
# HTML report
pytest tests/ --cov=. --cov-report=html:coverage_html

# View report
open coverage_html/index.html
```

Current coverage: ~40% (focusing on critical paths)

## Adding New Tests

When adding new functionality:

1. Create test classes named `Test<FeatureName>`
2. Use descriptive test names like `test_<what>_<condition>`
3. Use fixtures from `conftest.py` where appropriate
4. Mock external dependencies (Ollama, network, filesystem)
5. Mark integration tests with `@pytest.mark.integration`
6. Run the full test suite before committing

## Troubleshooting

**"pytest not found"**
```bash
pip install pytest pytest-cov responses
```

**"Ollama not running" (for integration tests)**
```bash
ollama serve
```

**Import errors**
- Make sure you're running from the project root
- Virtual environment should be activated

**Virtual environment issues**
```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r tests/requirements-test.txt
```

## Continuous Integration

For CI/CD pipelines, use:

```bash
# Run only unit tests (no Ollama required)
pytest tests/ -m "not integration" -v

# Run with JUnit XML output
pytest tests/ -m "not integration" --junitxml=test-results.xml
```
