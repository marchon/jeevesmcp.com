#!/bin/bash
# Jeeves One-Liner Install Script
# This can be run directly with:
# curl -fsSL https://raw.githubusercontent.com/marchon/jeevesmcp/main/install.sh | bash

set -e

JEEVES_REPO="https://github.com/marchon/jeevesmcp"
INSTALL_DIR="${HOME}/.local/share/jeeves"
BIN_DIR="${HOME}/.local/bin"

echo "🎩 Installing Jeeves..."

# Check Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+."
    exit 1
fi

# Install Ollama if not present
if ! command -v ollama &> /dev/null; then
    echo "📦 Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Clone repository
rm -rf "${INSTALL_DIR}"
mkdir -p "$(dirname ${INSTALL_DIR})"
git clone --depth 1 "${JEEVES_REPO}.git" "${INSTALL_DIR}" 2>/dev/null || {
    # Fallback: download as tarball if git fails
    echo "📥 Downloading Jeeves..."
    curl -fsSL "${JEEVES_REPO}/archive/refs/heads/main.tar.gz" | tar -xz -C "$(dirname ${INSTALL_DIR})"
    mv "$(dirname ${INSTALL_DIR})/jeeves-main" "${INSTALL_DIR}"
}

# Install Python dependencies
cd "${INSTALL_DIR}"
pip3 install -q -r requirements.txt 2>/dev/null || pip install -q -r requirements.txt

# Create jeeves command
mkdir -p "${BIN_DIR}"
cat > "${BIN_DIR}/jeeves" << EOF
#!/bin/bash
cd "${INSTALL_DIR}" && exec python3 main.py "\$@" 2>/dev/null || exec python main.py "\$@"
EOF
chmod +x "${BIN_DIR}/jeeves"

# Add to PATH if needed
if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    echo "export PATH=\"${BIN_DIR}:\$PATH\"" >> "${HOME}/.bashrc"
    echo "export PATH=\"${BIN_DIR}:\$PATH\"" >> "${HOME}/.zshrc" 2>/dev/null || true
fi

# Start Ollama if not running
if ! pgrep -x "ollama" > /dev/null; then
    echo "🚀 Starting Ollama..."
    ollama serve &
    sleep 3
fi

echo ""
echo "✅ Jeeves installed!"
echo ""
echo "Running setup..."
echo ""

# Run setup
exec "${BIN_DIR}/jeeves" setup
