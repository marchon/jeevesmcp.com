# 🎩 Jeeves

**TL;DR:** Install a smart local LLM router in one line. Jeeves handles simple tasks locally (fast) and escalates complex requests to cloud AI automatically.

```bash
curl -fsSL https://raw.githubusercontent.com/marchon/jeevesmcp.com/main/install.sh | bash
```

---

<p align="center">
  <b>Your intelligent assistant that knows when to ask for help</b>
</p>

<p align="center">
  ⚡ Fast local execution &nbsp;•&nbsp; 🧠 Smart routing &nbsp;•&nbsp; ☁️ Auto cloud fallback &nbsp;•&nbsp; 🔧 Cross-platform
</p>

---

## 📋 Table of Contents

- [Quick Install](#quick-install)
- [What's New](#whats-new)
- [What is Jeeves?](#what-is-jeeves)
- [How It Works](#how-it-works)
- [Usage](#usage)
- [Configuration](#configuration)
- [Model Options](#model-options)
- [Platform Support](#platform-support)
- [LLM Interaction Logging](#llm-interaction-logging)
- [Troubleshooting](#troubleshooting)
- [Uninstall](#uninstall)

---

## 🚀 Quick Install

### One-Line Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/marchon/jeevesmcp.com/main/install.sh | bash
```

**This will:**
- ✅ Check/Install Ollama (local LLM engine)
- 📥 Download Jeeves to `~/.local/share/jeeves`
- 📦 Install Python dependencies
- 🚀 Start Ollama server
- ⚙️ Run interactive setup wizard with model selection

### Requirements

- Python 3.8+
- Linux, macOS, or Windows (WSL)
- ~2GB free space (for default model)

---

## ✨ What's New

### Version 0.1.0 Highlights

🔧 **Cross-Platform Support**
- Linux, macOS, Windows (WSL) with automatic platform detection
- Shell detection (Bash, Zsh, Fish, PowerShell)
- Terminal integration (iTerm2, GNOME Terminal, Windows Terminal)

🧠 **Model-Specific Optimizations**
- Custom prompts for each model family (Qwen, Llama, Phi, Gemma, DeepSeek)
- Optimized parameters per model size
- Family-specific chat formats (ChatML, Llama-3, etc.)

📝 **LLM Interaction Logging** (Optional, disabled by default)
- Debug and verify routing decisions
- Timestamp-based log files
- Complete audit trail: user request → LLM prompts → responses

---

## 🤔 What is Jeeves?

Jeeves is an **intelligent request router** that sits between you and your AI assistant (Kimi/Claude/etc). It uses a tiny local LLM to:

1. **⚡ Instantly execute** simple commands (shell, file operations)
2. **🧠 Classify** request complexity locally with model-optimized prompts
3. **☁️ Escalate** to cloud AI only when needed

**Why?** Most AI requests are simple ("ls -la", "read file.txt"). Jeeves handles these locally in milliseconds instead of waiting for cloud round-trips.

---

## 🔄 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                         USER REQUEST                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
              ┌─────────────▼─────────────┐
              │ 1. Pattern Matching       │ ◄── Instant (0ms)
              │    ls, cat, grep → LOCAL  │
              └─────────────┬─────────────┘
                            │ No match
              ┌─────────────▼─────────────┐
              │ 2. Local LLM Classifies   │ ◄── Fast (~100ms)
              │    Model-optimized prompt │
              │    SIMPLE → Try Local     │
              │    COMPLEX → Cloud        │
              └─────────────┬─────────────┘
                            │
              ┌─────────────▼─────────────┐
              │ 3. Validation             │
              │    Uncertain? → Cloud     │
              │    Good response → Return │
              └───────────────────────────┘
```

---

## 🎮 Usage

### CLI Commands

```bash
# Interactive mode (chat with Jeeves)
jeeves interactive

# Check everything is working
jeeves status

# Route a single request
jeeves route "list all Python files"

# Manage your models
jeeves models

# Switch to a different model
jeeves switch

# LLM interaction logging (default: off)
jeeves logging on              # Enable logging
jeeves logging off             # Disable logging
jeeves logging status          # Show status
jeeves logging list            # List recent logs
jeeves logging view --file LOG # View specific log
```

### Interactive Mode Commands

When in `jeeves interactive`, you can use:
- `/logging on` - Enable logging for this session
- `/logging off` - Disable logging
- `exit` or `quit` - Exit interactive mode

### In Python

```python
from jeeves import JeevesRouter

router = JeevesRouter()

# Simple shell command → Local (instant)
result = router.handle("ls -la")
print(result)  # Directory listing

# File operation → Local (instant)
result = router.handle("read README.md")
print(result)  # File contents

# Complex analysis → Escalates to Kimi
result = router.handle("Analyze this codebase architecture")
# Returns: "[JEEVES_ESCALATE] llm_classification"
# → Send this request to Kimi instead
```

---

## ⚙️ Configuration

Config location:
- **Linux:** `~/.config/jeeves/config.json`
- **macOS:** `~/Library/Application Support/jeeves/config.json`
- **Windows:** `%APPDATA%\jeeves\config.json`

```bash
# Re-run setup wizard
jeeves setup

# Edit config manually
nano ~/.config/jeeves/config.json
```

### Config Options

```json
{
  "ollama": {
    "host": "http://localhost:11434",
    "autostart": true,
    "autostart_with_kimi": true
  },
  "jeeves": {
    "default_model": "qwen2.5:1.5b",
    "timeout_seconds": 30
  },
  "routing": {
    "use_pattern_matching": true,
    "use_local_llm": true,
    "auto_fallback": true
  },
  "logging": {
    "enabled": false,
    "log_dir": null,
    "max_log_files": 100
  }
}
```

---

## 🤖 Model Options

| Model | Size | Speed | Best For |
|-------|------|-------|----------|
| `qwen2.5:0.5b` | 400MB | ⚡ Very Fast | Routing only, minimal RAM |
| **`qwen2.5:1.5b`** | 1GB | 🚀 Fast | **Recommended default** |
| `llama3.2:3b` | 2GB | 🚀 Fast | Better reasoning |
| `gemma2:2b` | 1.6GB | 🚀 Fast | Efficient, Google's model |
| `deepseek-r1:1.5b` | 1.1GB | 🚀 Fast | Step-by-step reasoning |

### Switch Models

```bash
jeeves switch
# Follow prompts to download and select a new model
```

### Model-Specific Optimizations

Jeeves automatically optimizes for each model family:

- **Qwen** (Alibaba): ChatML format with `<|im_start|>` tokens
- **Llama** (Meta): Llama-3 format with `<|start_header_id|>` tokens
- **Phi** (Microsoft): Phi chat format
- **Gemma** (Google): Gemma format with `<start_of_turn>` tokens
- **DeepSeek**: Standard format with reasoning optimization

Each model gets:
- Family-specific prompt templates
- Optimized temperature and max_tokens
- Appropriate stop sequences
- Model-specific confidence thresholds

---

## 💻 Platform Support

### Linux
- ✅ Ubuntu, Debian, Fedora, Arch, and more
- ✅ Bash, Zsh, Fish shell support
- ✅ GNOME Terminal, Konsole, Alacritty, etc.

### macOS
- ✅ Intel and Apple Silicon (M1/M2/M3)
- ✅ Terminal.app, iTerm2, Alacritty
- ✅ Bash, Zsh, Fish support

### Windows
- ✅ WSL2 (recommended)
- ⚠️ Native PowerShell (experimental)
- ✅ Windows Terminal integration

See [Platform Guide](docs/platforms.rst) for detailed setup instructions.

---

## 📝 LLM Interaction Logging

**Default: DISABLED** (for privacy)

Enable logging to debug routing decisions:

```bash
# Enable logging
jeeves logging on

# Run some commands...

# View recent logs
jeeves logging list
jeeves logging view --file LLM-LOG-02:09:26:14:30:25:123.log

# Disable when done
jeeves logging off
```

**What's logged:**
- User commands
- System context
- LLM decision prompts and responses
- Escalation details
- Final results

**Log format:** `LLM-LOG-MM:DD:YY:mm:ss:ms.log`

See [Logging Guide](docs/logging.rst) for details.

---

## 🐛 Troubleshooting

### "jeeves: command not found"

```bash
# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Or restart your terminal
source ~/.bashrc  # or ~/.zshrc
```

### "Ollama not running"

```bash
# Start Ollama manually
ollama serve

# Or enable autostart
jeeves setup
```

### Model download fails

```bash
# Pull manually
ollama pull qwen2.5:1.5b

# Check Ollama status
ollama list
```

### Slow responses

```bash
# Switch to faster model
jeeves switch
# Choose qwen2.5:0.5b for maximum speed
```

### Permission denied

```bash
# Fix ownership
sudo chown -R $USER:$USER ~/.local/share/jeeves
sudo chown -R $USER:$USER ~/.config/jeeves
```

---

## 🗑️ Uninstall

### Linux / macOS

```bash
# Remove Jeeves
rm -rf ~/.local/share/jeeves
rm -f ~/.local/bin/jeeves
rm -rf ~/.config/jeeves

# Optional: Remove Ollama
# Note: This removes ALL downloaded models too
rm -rf ~/.ollama
which ollama && rm "$(which ollama)"
```

### Windows

```powershell
# Remove Jeeves files
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\jeeves"
Remove-Item -Recurse -Force "$env:APPDATA\jeeves"

# Remove from PATH manually via System Properties
```

---

## 🏗️ Manual Installation

If the one-liner doesn't work:

### Linux / macOS

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Clone Jeeves
git clone https://github.com/marchon/jeevesmcp.com.git ~/.local/share/jeeves
cd ~/.local/share/jeeves

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create shortcut
mkdir -p ~/.local/bin
ln -sf ~/.local/share/jeeves/main.py ~/.local/bin/jeeves
chmod +x ~/.local/bin/jeeves

# 5. Run setup
jeeves setup
```

### Windows

```powershell
# 1. Download and install Ollama from https://ollama.com/download

# 2. Clone Jeeves
git clone https://github.com/marchon/jeevesmcp.com.git $env:LOCALAPPDATA\jeeves
cd $env:LOCALAPPDATA\jeeves

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run setup
python main.py setup
```

---

## 📁 Project Structure

```
jeeves/
├── main.py                 # CLI entry point
├── router.py               # Core routing logic with model optimizations
├── config.py               # Configuration management
├── platform_utils.py       # Cross-platform detection
├── model_configs.py        # Model-specific optimizations
├── llm_logger.py           # LLM interaction logging
├── install.sh              # One-line installer
├── run_tests.sh            # Test runner
├── tests/                  # Test suite
├── docs/                   # Sphinx documentation
├── models/
│   └── suggested_models.json
├── requirements.txt
└── README.md
```

---

## 📚 Documentation

- [Installation Guide](docs/installation.rst) - Platform-specific installation
- [Platform Support](docs/platforms.rst) - Linux, macOS, Windows details
- [Logging Guide](docs/logging.rst) - LLM interaction logging
- [Development Guide](docs/development.rst) - Contributing and architecture
- [API Reference](docs/api.rst) - Python API documentation

To build documentation locally:

```bash
cd docs
pip install -r requirements.txt
make html
# Open _build/html/index.html
```

---

## 🤝 How It Integrates with Kimi

Jeeves is designed to work **alongside** Kimi, not replace it:

```python
from jeeves import JeevesRouter
import kimi  # Your Kimi client

router = JeevesRouter()

# User asks something
request = "Analyze this code"
result = router.route(request)

if result['should_escalate']:
    # Complex request → Send to Kimi
    response = kimi.generate(request)
else:
    # Simple request → Use local result
    response = result['result']

print(response)
```

---

## 🧪 Testing

```bash
# Run all tests
./run_tests.sh

# Run only unit tests (no Ollama required)
./run_tests.sh --quick

# Run with coverage
./run_tests.sh --coverage
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Development Guide](docs/development.rst) for:
- Code style guidelines
- Testing requirements
- Architecture overview
- How to submit changes

---

## 📜 License

MIT License - See [LICENSE](LICENSE) file

---

<p align="center">
  Made with 🎩 by the Jeeves team
</p>

<p align="center">
  <a href="https://github.com/marchon/jeevesmcp.com">GitHub</a> •
  <a href="https://github.com/marchon/jeevesmcp.com/issues">Issues</a> •
  <a href="https://github.com/marchon/jeevesmcp.com/discussions">Discussions</a>
</p>
