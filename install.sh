#!/bin/bash
# Jeeves One-Line Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/marchon/jeevesmcp.com/main/install.sh | bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/marchon/jeevesmcp.com.git"
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

detect_platform() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

detect_shell() {
    if [[ "$SHELL" == *"zsh"* ]]; then
        echo "zsh"
    elif [[ "$SHELL" == *"bash"* ]]; then
        echo "bash"
    elif [[ "$SHELL" == *"fish"* ]]; then
        echo "fish"
    else
        echo "unknown"
    fi
}

get_shell_config() {
    local shell=$1
    case "$shell" in
        zsh)
            echo "${HOME}/.zshrc"
            ;;
        bash)
            echo "${HOME}/.bashrc"
            ;;
        fish)
            echo "${HOME}/.config/fish/config.fish"
            ;;
        *)
            echo ""
            ;;
    esac
}

install_ollama() {
    log_info "Ollama not found. Installing..."
    
    local platform=$(detect_platform)
    
    case "$platform" in
        linux)
            log_info "Installing Ollama on Linux..."
            curl -fsSL https://ollama.com/install.sh | sh
            ;;
        macos)
            if check_command brew; then
                log_info "Installing Ollama via Homebrew..."
                # Handle potential mlx conflicts gracefully
                brew install ollama 2>&1 || {
                    log_warn "Homebrew install had warnings, trying to link..."
                    brew link --overwrite ollama 2>/dev/null || true
                }
                
                # Start Ollama service
                log_info "Starting Ollama service..."
                brew services start ollama 2>/dev/null || {
                    log_warn "Could not start Ollama service automatically"
                    log_info "You can start it later with: brew services start ollama"
                }
            else
                log_info "Homebrew not found. Installing Ollama directly..."
                curl -fsSL https://ollama.com/install.sh | sh
            fi
            ;;
        *)
            log_error "Unsupported OS: $OSTYPE"
            log_info "Please install Ollama manually: https://ollama.com/download"
            exit 1
            ;;
    esac
    
    log_success "Ollama installed"
}

check_ollama_running() {
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

install_python_deps() {
    log_info "Installing Python dependencies..."
    
    cd "${INSTALL_DIR}"
    
    local python_cmd=""
    if check_command python3; then
        python_cmd="python3"
    elif check_command python; then
        python_cmd="python"
    fi
    
    if [ -z "$python_cmd" ]; then
        log_error "Python not found. Please install Python 3.8+."
        exit 1
    fi
    
    # Check Python version
    local py_version=$($python_cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
    local major=$(echo "$py_version" | cut -d. -f1)
    local minor=$(echo "$py_version" | cut -d. -f2)
    
    if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 8 ]); then
        log_error "Python 3.8+ required. Found: $py_version"
        exit 1
    fi
    
    log_info "Using Python $py_version"
    
    if check_command pip3; then
        pip3 install -q -r requirements.txt
    elif check_command pip; then
        pip install -q -r requirements.txt
    else
        log_error "pip not found. Please install pip."
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
    local shell=$(detect_shell)
    local shell_config=$(get_shell_config "$shell")
    
    if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
        log_info "Adding ${BIN_DIR} to PATH..."
        
        case "$shell" in
            zsh|bash)
                if [ -n "$shell_config" ]; then
                    echo "export PATH=\"${BIN_DIR}:\$PATH\"" >> "$shell_config"
                    log_success "Added to ${shell_config}"
                    log_info "Please run: source ${shell_config}"
                else
                    log_warn "Please add ${BIN_DIR} to your PATH manually"
                fi
                ;;
            fish)
                mkdir -p "$(dirname "$shell_config")"
                echo "fish_add_path ${BIN_DIR}" >> "$shell_config"
                log_success "Added to ${shell_config}"
                log_info "Please run: source ${shell_config}"
                ;;
            *)
                log_warn "Unknown shell. Please add ${BIN_DIR} to your PATH manually"
                log_info "Add this line to your shell config:"
                log_info "  export PATH=\"${BIN_DIR}:\$PATH\""
                ;;
        esac
    fi
}

start_ollama() {
    if check_ollama_running; then
        log_success "Ollama is already running"
        return 0
    fi
    
    log_info "Starting Ollama server..."
    
    # Try to start Ollama
    if check_command ollama; then
        ollama serve > /dev/null 2>&1 &
        sleep 2
        
        # Wait for Ollama to be ready
        local max_attempts=30
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if check_ollama_running; then
                log_success "Ollama is running"
                return 0
            fi
            sleep 1
            attempt=$((attempt + 1))
        done
        
        log_warn "Ollama may not have started properly"
        log_info "You can start it manually with: ollama serve"
    else
        log_error "Ollama command not found after installation"
        exit 1
    fi
}

run_setup() {
    log_info "Running Jeeves setup..."
    
    cd "${INSTALL_DIR}"
    
    # Check if stdin is a terminal
    if [ -t 0 ]; then
        # Interactive mode - run setup normally
        if check_command python3; then
            python3 main.py setup
        elif check_command python; then
            python main.py setup
        else
            log_error "Python not found. Please install Python 3.8+."
            exit 1
        fi
    else
        # Non-interactive mode (piped input) - can't run setup
        log_warn "Cannot run interactive setup in non-interactive mode"
        log_info "Please run setup manually after installation:"
        log_info "  jeeves setup"
        log_info ""
        log_info "Or install with default settings by running:"
        log_info "  curl -fsSL .../install.sh | bash -s -- --no-setup"
        log_info "  jeeves setup  # Run this separately in your terminal"
    fi
}

uninstall() {
    log_warn "Uninstalling Jeeves..."
    
    # Remove installation directory
    if [ -d "${INSTALL_DIR}" ]; then
        rm -rf "${INSTALL_DIR}"
        log_success "Removed ${INSTALL_DIR}"
    fi
    
    # Remove CLI wrapper
    if [ -f "${BIN_DIR}/jeeves" ]; then
        rm -f "${BIN_DIR}/jeeves"
        log_success "Removed ${BIN_DIR}/jeeves"
    fi
    
    # Remove config (ask first)
    local config_dir="${HOME}/.config/jeeves"
    if [ -d "$config_dir" ]; then
        read -p "Remove configuration directory ${config_dir}? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$config_dir"
            log_success "Removed ${config_dir}"
        fi
    fi
    
    log_success "Jeeves has been uninstalled"
    log_info "Note: Ollama was not removed. To uninstall Ollama:"
    log_info "  macOS: brew uninstall ollama"
    log_info "  Linux: rm -rf ~/.ollama and remove ollama binary"
}

print_help() {
    echo "🎩 Jeeves Installer"
    echo ""
    echo "Usage:"
    echo "  curl -fsSL https://.../install.sh | bash"
    echo ""
    echo "Options:"
    echo "  --no-setup    Skip the setup wizard"
    echo "  --uninstall   Remove Jeeves"
    echo "  --help        Show this help"
    echo ""
    echo "After installation:"
    echo "  jeeves --help          Show Jeeves help"
    echo "  jeeves status          Check Jeeves status"
    echo "  jeeves interactive     Start interactive mode"
}

main() {
    print_banner
    
    # Check Python
    log_info "Checking Python installation..."
    if ! check_command python3 && ! check_command python; then
        log_error "Python not found. Please install Python 3.8 or higher."
        log_info "Visit: https://www.python.org/downloads/"
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
    
    # Check if Ollama is running
    if ! check_ollama_running; then
        start_ollama
    fi
    
    # Clone repository
    clone_repo
    
    # Install Python dependencies
    install_python_deps
    
    # Install Jeeves CLI
    install_jeeves
    
    # Add to PATH
    add_to_path
    
    echo ""
    log_success "Jeeves installation complete!"
    echo ""
    
    # Run setup wizard
    if [ -z "$NO_SETUP" ]; then
        run_setup
    else
        log_info "Skipping setup wizard (--no-setup)"
        log_info "Run 'jeeves setup' to configure later"
    fi
    
    echo ""
    log_success "Jeeves is ready to serve! 🎩"
    echo ""
    
    # If setup didn't run (non-interactive), remind user
    if [ -n "$NO_SETUP" ] || [ ! -t 0 ]; then
        log_info "To complete setup, please run:"
        log_info "  jeeves setup"
        log_info ""
    fi
    
    echo "Quick start:"
    echo "  jeeves --help          Show help"
    echo "  jeeves status          Check status"
    echo "  jeeves interactive     Start interactive mode"
    echo "  jeeves setup           Run setup wizard"
    echo ""
    
    # Platform-specific notes
    local platform=$(detect_platform)
    case "$platform" in
        macos)
            log_info "macOS users: If jeeves command not found, run:"
            log_info "  source ~/.zshrc  (or ~/.bashrc)"
            ;;
    esac
}

# Handle arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-setup)
            NO_SETUP=1
            shift
            ;;
        --uninstall)
            uninstall
            exit 0
            ;;
        --help|-h)
            print_help
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

main
