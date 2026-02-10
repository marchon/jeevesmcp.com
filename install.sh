#!/bin/bash
# Jeeves One-Line Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/yourusername/jeeves/main/install.sh | bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/marchon/jeeves.ai.git"
INSTALL_DIR="${HOME}/.local/share/jeeves"
BIN_DIR="${HOME}/.local/bin"

print_banner() {
    echo -e "${BLUE}"
    echo "    🎩 Jeeves Installer"
    echo "    Your intelligent assistant that knows when to ask for help"
    echo -e "${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ️  ${1}${NC}"
}

log_success() {
    echo -e "${GREEN}✅ ${1}${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠️  ${1}${NC}"
}

log_error() {
    echo -e "${RED}❌ ${1}${NC}"
}

check_command() {
    command -v "$1" >/dev/null 2>&1
}

install_ollama() {
    log_info "Ollama not found. Installing..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -fsSL https://ollama.com/install.sh | sh
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if check_command brew; then
            brew install ollama
        else
            curl -fsSL https://ollama.com/install.sh | sh
        fi
    else
        log_error "Unsupported OS. Please install Ollama manually: https://ollama.com/download"
        exit 1
    fi
    
    log_success "Ollama installed"
}

install_python_deps() {
    log_info "Installing Python dependencies..."
    
    cd "${INSTALL_DIR}"
    
    if check_command pip3; then
        pip3 install -q -r requirements.txt
    elif check_command pip; then
        pip install -q -r requirements.txt
    else
        log_error "pip not found. Please install Python and pip."
        exit 1
    fi
    
    log_success "Dependencies installed"
}

clone_repo() {
    log_info "Cloning Jeeves repository..."
    
    # Remove existing installation if present
    if [ -d "${INSTALL_DIR}" ]; then
        log_warn "Existing installation found. Updating..."
        rm -rf "${INSTALL_DIR}"
    fi
    
    # Create parent directory
    mkdir -p "$(dirname ${INSTALL_DIR})"
    
    # Clone repository
    if check_command git; then
        git clone --depth 1 "${REPO_URL}" "${INSTALL_DIR}"
    else
        log_error "git not found. Please install git."
        exit 1
    fi
    
    log_success "Repository cloned to ${INSTALL_DIR}"
}

install_jeeves() {
    log_info "Installing Jeeves CLI..."
    
    # Create bin directory
    mkdir -p "${BIN_DIR}"
    
    # Create wrapper script
    cat > "${BIN_DIR}/jeeves" << 'EOF'
#!/bin/bash
# Jeeves CLI wrapper

JEEVES_DIR="${HOME}/.local/share/jeeves"
PYTHON="$(command -v python3 || command -v python)"

if [ ! -d "${JEEVES_DIR}" ]; then
    echo "❌ Jeeves not found. Please reinstall."
    exit 1
fi

if [ -z "${PYTHON}" ]; then
    echo "❌ Python not found. Please install Python 3.8+."
    exit 1
fi

cd "${JEEVES_DIR}"
exec "${PYTHON}" main.py "$@"
EOF
    
    chmod +x "${BIN_DIR}/jeeves"
    
    log_success "Jeeves CLI installed to ${BIN_DIR}/jeeves"
}

add_to_path() {
    if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
        log_info "Adding ${BIN_DIR} to PATH..."
        
        SHELL_CONFIG=""
        if [[ "$SHELL" == *"zsh"* ]]; then
            SHELL_CONFIG="${HOME}/.zshrc"
        elif [[ "$SHELL" == *"bash"* ]]; then
            SHELL_CONFIG="${HOME}/.bashrc"
        fi
        
        if [ -n "$SHELL_CONFIG" ]; then
            echo "export PATH=\"${BIN_DIR}:\$PATH\"" >> "$SHELL_CONFIG"
            log_success "Added to ${SHELL_CONFIG}"
            log_warn "Please run: source ${SHELL_CONFIG}"
        else
            log_warn "Please add ${BIN_DIR} to your PATH manually"
        fi
    fi
}

start_ollama() {
    if ! pgrep -x "ollama" > /dev/null; then
        log_info "Starting Ollama server..."
        ollama serve &
        sleep 2
        
        # Wait for Ollama to be ready
        for i in {1..10}; do
            if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
                log_success "Ollama is running"
                return 0
            fi
            sleep 1
        done
        
        log_warn "Ollama may not have started properly. Continuing anyway..."
    else
        log_success "Ollama is already running"
    fi
}

run_setup() {
    log_info "Running Jeeves setup..."
    
    cd "${INSTALL_DIR}"
    
    if check_command python3; then
        python3 main.py setup
    elif check_command python; then
        python main.py setup
    else
        log_error "Python not found. Please install Python 3.8+."
        exit 1
    fi
}

main() {
    print_banner
    
    # Check Python
    log_info "Checking Python installation..."
    if ! check_command python3 && ! check_command python; then
        log_error "Python not found. Please install Python 3.8 or higher."
        exit 1
    fi
    log_success "Python found"
    
    # Check/Install Ollama
    log_info "Checking Ollama installation..."
    if ! check_command ollama; then
        install_ollama
    else
        log_success "Ollama found"
    fi
    
    # Clone repository
    clone_repo
    
    # Install Python dependencies
    install_python_deps
    
    # Install Jeeves CLI
    install_jeeves
    
    # Add to PATH
    add_to_path
    
    # Start Ollama
    start_ollama
    
    echo ""
    log_success "Jeeves installation complete!"
    echo ""
    
    # Run setup wizard
    run_setup
    
    echo ""
    log_success "Jeeves is ready to serve! 🎩"
    echo ""
    echo "Usage:"
    echo "  jeeves --help          Show help"
    echo "  jeeves status          Check status"
    echo "  jeeves interactive     Start interactive mode"
    echo ""
}

# Handle arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-setup)
            NO_SETUP=1
            shift
            ;;
        --help|-h)
            echo "Jeeves Installer"
            echo ""
            echo "Usage:"
            echo "  curl -fsSL https://.../install.sh | bash"
            echo ""
            echo "Options:"
            echo "  --no-setup    Skip the setup wizard"
            echo "  --help        Show this help"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

main
