#!/bin/bash
#
# Jeeves Test Suite Runner
# Ensures dependencies are installed and runs all tests
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "========================================"
    echo "  $1"
    echo "========================================"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Virtual environment path
VENV_DIR=".venv"

# ============================================
# Step 1: Setup Virtual Environment
# ============================================
print_header "Step 1: Setting up Virtual Environment"

if [ ! -d "$VENV_DIR" ]; then
    print_warning "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created"
else
    print_success "Virtual environment exists"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# ============================================
# Step 2: Install/Upgrade Dependencies
# ============================================
print_header "Step 2: Installing Dependencies"

print_warning "Upgrading pip..."
pip install --upgrade pip -q

print_warning "Installing production dependencies..."
pip install -r requirements.txt -q
print_success "Production dependencies installed"

print_warning "Installing test dependencies..."
pip install pytest pytest-cov pytest-asyncio responses -q
print_success "Test dependencies installed"

# ============================================
# Step 3: Check and Install Ollama
# ============================================
print_header "Step 3: Checking Ollama Installation"

check_ollama_installed() {
    if command -v ollama &> /dev/null; then
        return 0
    else
        return 1
    fi
}

check_ollama_running() {
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        return 0
    else
        return 1
    fi
}

if check_ollama_installed; then
    print_success "Ollama is installed"
    ollama --version 2>/dev/null || echo "   (version check skipped)"
else
    print_warning "Ollama is not installed. Installing now..."
    
    # Detect OS and install accordingly
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        print_warning "Installing Ollama for Linux..."
        curl -fsSL https://ollama.com/install.sh | sh
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            print_warning "Installing Ollama via Homebrew..."
            brew install ollama
        else
            print_warning "Installing Ollama for macOS..."
            curl -fsSL https://ollama.com/install.sh | sh
        fi
    else
        print_error "Unsupported OS. Please install Ollama manually from https://ollama.com/download"
        exit 1
    fi
    
    if check_ollama_installed; then
        print_success "Ollama installed successfully"
    else
        print_error "Failed to install Ollama. Please install manually."
        exit 1
    fi
fi

# Check if Ollama is running
if check_ollama_running; then
    print_success "Ollama server is running"
else
    print_warning "Ollama server is not running. Starting it now..."
    ollama serve &
    OLLAMA_PID=$!
    
    # Wait for Ollama to be ready
    for i in {1..30}; do
        if check_ollama_running; then
            print_success "Ollama server started successfully"
            break
        fi
        sleep 1
    done
    
    if ! check_ollama_running; then
        print_error "Failed to start Ollama server"
        exit 1
    fi
fi

# ============================================
# Step 4: Check for Default Model
# ============================================
print_header "Step 4: Checking Default Model"

DEFAULT_MODEL="qwen2.5:1.5b"

if ollama list 2>/dev/null | grep -q "$DEFAULT_MODEL"; then
    print_success "Default model ($DEFAULT_MODEL) is available"
else
    print_warning "Default model ($DEFAULT_MODEL) not found. Pulling now..."
    print_warning "This may take a few minutes depending on your connection..."
    ollama pull "$DEFAULT_MODEL"
    print_success "Model pulled successfully"
fi

# ============================================
# Step 5: Run Tests
# ============================================
print_header "Step 5: Running Test Suite"

# Default pytest arguments
PYTEST_ARGS="-v --tb=short"

# Parse command line arguments
SKIP_INTEGRATION=true
COVERAGE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --all|-a)
            SKIP_INTEGRATION=false
            shift
            ;;
        --coverage|-c)
            COVERAGE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --all, -a       Run all tests including integration tests"
            echo "  --coverage, -c  Generate coverage report"
            echo "  --help, -h      Show this help message"
            echo ""
            echo "Any additional arguments are passed to pytest."
            exit 0
            ;;
        *)
            # Pass through to pytest
            PYTEST_ARGS="$PYTEST_ARGS $1"
            shift
            ;;
    esac
done

# Add coverage if requested
if [ "$COVERAGE" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=. --cov-report=term-missing --cov-report=html:coverage_html"
fi

# Skip integration tests by default
if [ "$SKIP_INTEGRATION" = true ]; then
    PYTEST_ARGS="$PYTEST_ARGS -m 'not integration'"
fi

# Run pytest
echo "Running: pytest $PYTEST_ARGS tests/"
echo ""
eval "pytest $PYTEST_ARGS tests/"

TEST_EXIT_CODE=$?

# ============================================
# Step 6: Summary
# ============================================
print_header "Test Summary"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    print_success "All tests passed!"
    if [ "$COVERAGE" = true ]; then
        echo ""
        echo "Coverage report generated in: coverage_html/index.html"
    fi
    exit 0
else
    print_error "Some tests failed. Exit code: $TEST_EXIT_CODE"
    exit $TEST_EXIT_CODE
fi
