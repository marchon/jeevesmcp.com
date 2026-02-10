#!/usr/bin/env python3
"""
Jeeves Test Suite Runner - Python Version

Ensures dependencies are installed and runs all tests.
This is a cross-platform alternative to run_tests.sh.

Usage:
    python run_tests.py              # Run all unit tests
    python run_tests.py --all        # Run all tests including integration
    python run_tests.py --quick      # Run only quick unit tests
    python run_tests.py --help       # Show help
"""

import subprocess
import sys
import os
import platform
import time
import venv
from pathlib import Path


# Colors for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color
    
    @classmethod
    def disable(cls):
        cls.RED = ''
        cls.GREEN = ''
        cls.YELLOW = ''
        cls.BLUE = ''
        cls.NC = ''


def print_header(text):
    print(f"{Colors.BLUE}")
    print("=" * 60)
    print(f"  {text}")
    print("=" * 60)
    print(f"{Colors.NC}")


def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.NC}")


def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.NC}")


def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.NC}")


def run_command(cmd, check=True, capture_output=False, timeout=None, shell=False):
    """Run a shell command and return the result."""
    try:
        if isinstance(cmd, str) and not shell:
            cmd = cmd.split()
        
        result = subprocess.run(
            cmd,
            shell=shell,
            check=check,
            capture_output=capture_output,
            text=True,
            timeout=timeout
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            raise
        return e
    except subprocess.TimeoutExpired:
        print_error(f"Command timed out: {cmd}")
        return None


def get_venv_python():
    """Get the Python executable path in the virtual environment."""
    venv_dir = Path(".venv")
    if platform.system() == "Windows":
        return venv_dir / "Scripts" / "python.exe"
    else:
        return venv_dir / "bin" / "python"


def get_venv_pip():
    """Get the pip executable path in the virtual environment."""
    venv_dir = Path(".venv")
    if platform.system() == "Windows":
        return venv_dir / "Scripts" / "pip.exe"
    else:
        return venv_dir / "bin" / "pip"


def setup_virtual_environment():
    """Create and setup virtual environment."""
    print_header("Step 1: Setting up Virtual Environment")
    
    venv_dir = Path(".venv")
    
    if not venv_dir.exists():
        print_warning("Creating virtual environment...")
        venv.create(venv_dir, with_pip=True)
        print_success("Virtual environment created")
    else:
        print_success("Virtual environment exists")
    
    return venv_dir


def install_dependencies(venv_python):
    """Install required Python packages."""
    print_header("Step 2: Installing Dependencies")
    
    pip_cmd = str(get_venv_pip())
    
    # Upgrade pip
    print_warning("Upgrading pip...")
    run_command([pip_cmd, "install", "--upgrade", "pip", "-q"])
    
    # Install production dependencies
    print_warning("Installing production dependencies...")
    run_command([pip_cmd, "install", "-r", "requirements.txt", "-q"])
    print_success("Production dependencies installed")
    
    # Install test dependencies
    print_warning("Installing test dependencies...")
    test_deps = ["pytest", "pytest-cov", "pytest-asyncio", "responses"]
    run_command([pip_cmd, "install"] + test_deps + ["-q"])
    print_success("Test dependencies installed")
    
    return True


def check_ollama_installed():
    """Check if Ollama is installed."""
    result = run_command(["which", "ollama"], check=False, capture_output=True)
    return result.returncode == 0


def check_ollama_running():
    """Check if Ollama server is running."""
    try:
        import urllib.request
        import urllib.error
        try:
            with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as response:
                return response.status == 200
        except urllib.error.URLError:
            return False
    except Exception:
        return False


def install_ollama():
    """Install Ollama based on the OS."""
    system = platform.system()
    
    if system == "Linux":
        print_warning("Installing Ollama for Linux...")
        result = run_command(
            "curl -fsSL https://ollama.com/install.sh | sh",
            check=False,
            timeout=300,
            shell=True
        )
        return result.returncode == 0 if result else False
    elif system == "Darwin":
        # Check if brew is available
        result = run_command(["which", "brew"], check=False, capture_output=True)
        if result.returncode == 0:
            print_warning("Installing Ollama via Homebrew...")
            result = run_command(["brew", "install", "ollama"], check=False, timeout=120)
            return result.returncode == 0 if result else False
        else:
            print_warning("Installing Ollama for macOS...")
            result = run_command(
                "curl -fsSL https://ollama.com/install.sh | sh",
                check=False,
                timeout=300,
                shell=True
            )
            return result.returncode == 0 if result else False
    else:
        print_error(f"Unsupported OS: {system}")
        print_error("Please install Ollama manually from https://ollama.com/download")
        return False


def start_ollama():
    """Start Ollama server."""
    print_warning("Starting Ollama server...")
    
    # Start Ollama in background
    if platform.system() == "Windows":
        subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
    
    # Wait for it to be ready
    for i in range(30):
        if check_ollama_running():
            return True
        time.sleep(1)
    
    return False


def setup_ollama():
    """Check and setup Ollama."""
    print_header("Step 3: Checking Ollama Installation")
    
    if check_ollama_installed():
        print_success("Ollama is installed")
        try:
            result = run_command(["ollama", "--version"], capture_output=True)
            if result:
                print(f"   {result.stdout.strip()}")
        except Exception:
            pass
    else:
        print_warning("Ollama is not installed. Installing now...")
        if install_ollama():
            print_success("Ollama installed successfully")
        else:
            print_error("Failed to install Ollama")
            return False
    
    # Check if running
    if check_ollama_running():
        print_success("Ollama server is running")
    else:
        print_warning("Ollama server is not running")
        if start_ollama():
            print_success("Ollama server started successfully")
        else:
            print_error("Failed to start Ollama server")
            return False
    
    return True


def check_default_model():
    """Check and pull default model if needed."""
    print_header("Step 4: Checking Default Model")
    
    DEFAULT_MODEL = "qwen2.5:1.5b"
    
    try:
        result = run_command(["ollama", "list"], capture_output=True)
        if result and DEFAULT_MODEL in result.stdout:
            print_success(f"Default model ({DEFAULT_MODEL}) is available")
            return True
    except Exception:
        pass
    
    print_warning(f"Default model ({DEFAULT_MODEL}) not found")
    print_warning("Pulling model (this may take a few minutes)...")
    
    result = run_command(["ollama", "pull", DEFAULT_MODEL], check=False, timeout=600)
    if result and result.returncode == 0:
        print_success("Model pulled successfully")
        return True
    else:
        print_error("Failed to pull model")
        return False


def run_tests(args, venv_python):
    """Run the test suite."""
    print_header("Step 5: Running Test Suite")
    
    pytest_args = ["-v", "--tb=short"]
    
    if args.coverage:
        pytest_args.extend(["--cov=.", "--cov-report=term-missing", "--cov-report=html:coverage_html"])
    
    if args.all:
        # Run all tests including integration
        pytest_args.append("tests/")
    else:
        # Default: run unit tests only (no integration)
        pytest_args.extend(["-m", "not integration", "tests/"])
    
    # Add any extra arguments
    if args.pytest_args:
        pytest_args.extend(args.pytest_args)
    
    # Run pytest using venv python
    cmd = [str(venv_python), "-m", "pytest"] + pytest_args
    print(f"Running: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    
    if args.coverage and result.returncode == 0:
        print("\n")
        print_success("Coverage report generated in: coverage_html/index.html")
    
    return result.returncode


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Jeeves Test Suite Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py              # Run unit tests only
  python run_tests.py --all        # Run all tests including integration
  python run_tests.py --no-setup   # Skip dependency/setup checks
  python run_tests.py --coverage   # Generate coverage report
        """
    )
    
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Run all tests including integration tests"
    )
    parser.add_argument(
        "--no-setup", "-n",
        action="store_true",
        help="Skip dependency and Ollama setup"
    )
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    parser.add_argument(
        "pytest_args",
        nargs="*",
        help="Additional arguments to pass to pytest"
    )
    
    args = parser.parse_args()
    
    # Disable colors if requested or not in terminal
    if args.no_color or not sys.stdout.isatty():
        Colors.disable()
    
    # Setup phase
    venv_dir = None
    venv_python = None
    
    if not args.no_setup:
        # Setup virtual environment
        venv_dir = setup_virtual_environment()
        venv_python = get_venv_python()
        
        # Install dependencies
        if not install_dependencies(venv_python):
            return 1
        
        # Setup Ollama
        if not setup_ollama():
            print_warning("Continuing without Ollama (some tests may be skipped)")
        
        # Check default model
        if not check_default_model():
            print_warning("Continuing without default model (some tests may be skipped)")
    else:
        # Use system Python if no setup
        venv_python = sys.executable
    
    # Run tests
    exit_code = run_tests(args, venv_python)
    
    # Summary
    print_header("Test Summary")
    if exit_code == 0:
        print_success("All tests passed!")
    else:
        print_error(f"Some tests failed. Exit code: {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
