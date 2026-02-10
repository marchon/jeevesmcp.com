# 🎩 Jeeves

**TL;DR:** Install a smart local LLM router in one line. Jeeves handles simple tasks locally (fast) and escalates complex requests to cloud AI automatically.

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/jeeves/main/install.sh | bash
```

---

<p align="center">
  <b>Your intelligent assistant that knows when to ask for help</b>
</p>

<p align="center">
  ⚡ Fast local execution &nbsp;•&nbsp; 🧠 Smart routing &nbsp;•&nbsp; ☁️ Auto cloud fallback
</p>

---

## 📋 Table of Contents

- [Quick Install](#quick-install)
- [What is Jeeves?](#what-is-jeeves)
- [How It Works](#how-it-works)
- [Usage](#usage)
- [Configuration](#configuration)
- [Model Options](#model-options)
- [Troubleshooting](#troubleshooting)
- [Uninstall](#uninstall)

---

## 🚀 Quick Install

### One-Line Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/jeeves/main/install.sh | bash
```

**This will:**
- ✅ Install Ollama (local LLM engine) if not present
- 📥 Download Jeeves to `~/.local/share/jeeves`
- 📦 Install Python dependencies
- 🚀 Start Ollama server
- ⚙️ Run interactive setup wizard to choose your model

### Requirements

- Python 3.8+
- Linux or macOS (Windows via WSL)
- ~2GB free space (for default model)

---

## 🤔 What is Jeeves?

Jeeves is an **intelligent request router** that sits between you and your AI assistant (Kimi/Claude/etc). It uses a tiny local LLM to:

1. **⚡ Instantly execute** simple commands (shell, file operations)
2. **🧠 Classify** request complexity locally
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

### After Installation

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
```

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

Config location: `~/.config/jeeves/config.json`

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

---

## 🗑️ Uninstall

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

---

## 🏗️ Manual Installation

If the one-liner doesn't work:

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Clone Jeeves
git clone https://github.com/YOUR_USERNAME/jeeves.git ~/.local/share/jeeves
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

---

## 📁 Project Structure

```
jeeves/
├── install.sh              # One-line installer
├── main.py                 # CLI entry point
├── router.py               # Core routing logic
├── config.py               # Configuration management
├── models/
│   └── suggested_models.json  # Recommended models
├── requirements.txt        # Python deps
└── README.md              # This file
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

## 📜 License

MIT License - See [LICENSE](LICENSE) file

---

<p align="center">
  Made with 🎩 by the Jeeves team
</p>

<p align="center">
  <a href="https://github.com/YOUR_USERNAME/jeeves">GitHub</a> •
  <a href="https://github.com/YOUR_USERNAME/jeeves/issues">Issues</a> •
  <a href="https://github.com/YOUR_USERNAME/jeeves/discussions">Discussions</a>
</p>
