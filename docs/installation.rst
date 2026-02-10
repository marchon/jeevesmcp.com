Installation
============

System Requirements
-------------------

**Minimum:**

- Python 3.8+
- 2GB RAM
- 2GB free disk space
- Linux, macOS, or Windows (via WSL)

**Recommended:**

- Python 3.10+
- 4GB RAM
- 5GB free disk space
- SSD storage

Quick Install
-------------

Linux / macOS
^^^^^^^^^^^^^

**One-line install:**

.. code-block:: bash

   curl -fsSL https://raw.githubusercontent.com/marchon/jeevesmcp.com/main/install.sh | bash

This command will:

1. Detect your operating system and shell
2. Install Ollama (if not present)
3. Download Jeeves to the appropriate directory
4. Install Python dependencies
5. Create the ``jeeves`` command
6. Start Ollama server
7. Run interactive setup

Windows (PowerShell)
^^^^^^^^^^^^^^^^^^^^

**PowerShell install (experimental):**

.. code-block:: powershell

   irm https://raw.githubusercontent.com/marchon/jeevesmcp.com/main/install.ps1 | iex

Or manually:

1. Download and install Ollama from https://ollama.com/download
2. Clone the repository
3. Install Python dependencies

Windows (WSL)
^^^^^^^^^^^^^

**Recommended for Windows users:**

1. Install WSL2 if not already installed:

.. code-block:: powershell

   wsl --install

2. Inside WSL2, run the Linux install:

.. code-block:: bash

   curl -fsSL https://raw.githubusercontent.com/marchon/jeevesmcp.com/main/install.sh | bash

Platform Detection
------------------

Jeeves automatically detects your platform and adapts accordingly:

.. code-block:: bash

   # Check detected platform
   jeeves status

   # Example output:
   # 🎩 Jeeves Status
   # Platform: Linux
   # Shell: bash
   # Terminal: gnome-terminal
   # Config: ~/.config/jeeves/config.json

Manual Installation
-------------------

If you prefer to install manually or the one-liner doesn't work:

Step 1: Install Ollama
^^^^^^^^^^^^^^^^^^^^^^

Linux
^^^^^

.. code-block:: bash

   curl -fsSL https://ollama.com/install.sh | sh

macOS
^^^^^

**Option 1: Install script**

.. code-block:: bash

   curl -fsSL https://ollama.com/install.sh | sh

**Option 2: Homebrew**

.. code-block:: bash

   brew install --cask ollama

**Option 3: Download app**

Download from https://ollama.com/download

Windows
^^^^^^^

Download the installer from https://ollama.com/download

Or use winget:

.. code-block:: powershell

   winget install Ollama.Ollama

Step 2: Clone Repository
^^^^^^^^^^^^^^^^^^^^^^^^

Linux / macOS
^^^^^^^^^^^^^

.. code-block:: bash

   git clone https://github.com/marchon/jeevesmcp.com.git ~/.local/share/jeeves
   cd ~/.local/share/jeeves

Windows
^^^^^^^

.. code-block:: powershell

   git clone https://github.com/marchon/jeevesmcp.com.git $env:LOCALAPPDATA\jeeves
   cd $env:LOCALAPPDATA\jeeves

Step 3: Install Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Linux / macOS
^^^^^^^^^^^^^

**Direct install:**

.. code-block:: bash

   pip install -r requirements.txt

**With virtual environment (recommended):**

.. code-block:: bash

   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

Windows
^^^^^^^

**Direct install:**

.. code-block:: powershell

   pip install -r requirements.txt

**With virtual environment (recommended):**

.. code-block:: powershell

   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt

Step 4: Create Command
^^^^^^^^^^^^^^^^^^^^^^

Linux / macOS
^^^^^^^^^^^^^

.. code-block:: bash

   mkdir -p ~/.local/bin
   ln -sf ~/.local/share/jeeves/main.py ~/.local/bin/jeeves
   chmod +x ~/.local/bin/jeeves

Windows
^^^^^^^

.. code-block:: powershell

   # Create bin directory
   New-Item -ItemType Directory -Force -Path "$env:LOCALAPPDATA\jeeves\bin"

   # Create wrapper script
   $wrapper = @"
   @echo off
   python "$env:LOCALAPPDATA\jeeves\main.py" %*
   "@
   Set-Content -Path "$env:LOCALAPPDATA\jeeves\bin\jeeves.cmd" -Value $wrapper

   # Add to PATH
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:LOCALAPPDATA\jeeves\bin", "User")

Step 5: Add to PATH
^^^^^^^^^^^^^^^^^^^

Bash
^^^^

Add to ``~/.bashrc``:

.. code-block:: bash

   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc

Zsh
^^^

Add to ``~/.zshrc``:

.. code-block:: bash

   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc

Fish
^^^^

.. code-block:: fish

   fish_add_path ~/.local/bin

PowerShell
^^^^^^^^^^

Add to your profile:

.. code-block:: powershell

   $binPath = "$env:LOCALAPPDATA\jeeves\bin"
   $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
   [Environment]::SetEnvironmentVariable("Path", "$currentPath;$binPath", "User")

Step 6: Run Setup
^^^^^^^^^^^^^^^^^

.. code-block:: bash

   jeeves setup

Platform-Specific Notes
-----------------------

Linux
^^^^^

**Supported distributions:**

- Ubuntu 20.04+
- Debian 11+
- Fedora 35+
- Arch Linux
- Any distribution with Python 3.8+

**Terminal integration:**

Jeeves auto-detects:
- GNOME Terminal
- Konsole (KDE)
- xfce4-terminal
- Alacritty
- kitty
- xterm

**Shell support:**

- Bash (default)
- Zsh
- Fish

macOS
^^^^^

**Apple Silicon (M1/M2/M3):**

Ollama runs natively on Apple Silicon for best performance:

.. code-block:: bash

   # Verify you're running ARM native
   arch  # Should output: arm64

**Terminal integration:**

Jeeves supports:
- Terminal.app (built-in)
- iTerm2 (recommended)
- Alacritty
- Hyper

Set your preferred terminal:

.. code-block:: bash

   export JEEVES_TERMINAL=iterm2  # or terminal.app

Windows
^^^^^^^

**WSL2 (Recommended):**

For the best Windows experience, use WSL2:

1. Install WSL2: ``wsl --install``
2. Choose Ubuntu or your preferred distro
3. Follow the Linux installation steps

**Accessing Windows Ollama from WSL:**

If you installed Ollama on Windows (not in WSL):

.. code-block:: bash

   # Get Windows host IP
   export OLLAMA_HOST=http://$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):11434

**Windows Terminal Integration:**

Create a Jeeves profile in Windows Terminal settings:

.. code-block:: json

   {
       "guid": "{unique-guid}",
       "name": "Jeeves",
       "commandline": "wsl -d Ubuntu -e jeeves interactive",
       "icon": "C:\\path\\to\\jeeves.ico",
       "startingDirectory": "%USERPROFILE%"
   }

Verification
------------

Check that everything is working:

.. code-block:: bash

   jeeves status

Expected output:

.. code-block:: text

   🎩 Jeeves Status
   
   Platform:          Linux
   Shell:             bash
   Terminal:          gnome-terminal
   
   Config file:       ~/.config/jeeves/config.json
   Ollama installed:  ✅ Yes
   Ollama running:    ✅ Yes
   Default model:     qwen2.5:1.5b
   Installed models:  3
   
   Routing settings:
     Pattern matching:   ✅ On
     Local LLM:          ✅ On
     Auto-fallback:      ✅ On

Updating
--------

To update to the latest version:

.. code-block:: bash

   cd ~/.local/share/jeeves
   git pull origin main
   pip install -r requirements.txt

Uninstallation
--------------

Linux / macOS
^^^^^^^^^^^^^

.. code-block:: bash

   # Remove Jeeves files
   rm -rf ~/.local/share/jeeves
   rm -f ~/.local/bin/jeeves
   rm -rf ~/.config/jeeves

   # Optional: Remove Ollama (also removes all models)
   rm -rf ~/.ollama
   which ollama && rm "$(which ollama)"

Windows
^^^^^^^

.. code-block:: powershell

   # Remove Jeeves files
   Remove-Item -Recurse -Force "$env:LOCALAPPDATA\jeeves"
   Remove-Item -Recurse -Force "$env:APPDATA\jeeves"

   # Remove from PATH (manual step)
   # Edit Environment Variables and remove jeeves paths

Troubleshooting Installation
----------------------------

"Permission denied" errors
^^^^^^^^^^^^^^^^^^^^^^^^^^

Linux / macOS
^^^^^^^^^^^^^

.. code-block:: bash

   # Make sure scripts are executable
   chmod +x ~/.local/bin/jeeves
   chmod +x ~/.local/share/jeeves/install.sh

   # Fix ownership
   sudo chown -R $USER:$USER ~/.local/share/jeeves

Windows
^^^^^^^

.. code-block:: powershell

   # Run as Administrator if needed
   # Or check file permissions in Properties

"Command not found: jeeves"
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Bash
^^^^

.. code-block:: bash

   # Check if ~/.local/bin is in PATH
   echo $PATH | grep -q ".local/bin" && echo "✓ In PATH" || echo "✗ Not in PATH"
   
   # Add it
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc

Zsh
^^^

.. code-block:: bash

   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc

PowerShell
^^^^^^^^^^

.. code-block:: powershell

   # Check PATH
   $env:Path -split ";" | Select-String "jeeves"
   
   # Add permanently
   [Environment]::SetEnvironmentVariable(
       "Path",
       $env:Path + ";$env:LOCALAPPDATA\jeeves\bin",
       "User"
   )

Ollama installation fails
^^^^^^^^^^^^^^^^^^^^^^^^^

Linux / macOS
^^^^^^^^^^^^^

Try installing Ollama manually:

.. code-block:: bash

   # Check if Ollama is already installed
   which ollama
   
   # If not, install manually
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Start Ollama
   ollama serve

Windows
^^^^^^^

1. Download from https://ollama.com/download
2. Run the installer
3. Ollama should start automatically
4. Verify: ``ollama list`` in PowerShell

Model download fails
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Check Ollama is running
   curl http://localhost:11434/api/tags
   
   # Try pulling manually
   ollama pull qwen2.5:1.5b
   
   # Check disk space
   df -h ~  # Linux/macOS
   # or
   Get-PSDrive C  # Windows PowerShell

Python not found
^^^^^^^^^^^^^^^^

Ubuntu/Debian
^^^^^^^^^^^^^

.. code-block:: bash

   sudo apt update && sudo apt install python3 python3-pip

Fedora
^^^^^^

.. code-block:: bash

   sudo dnf install python3 python3-pip

macOS
^^^^^

.. code-block:: bash

   # Using Homebrew
   brew install python3
   
   # Or download from python.org

Windows
^^^^^^^

.. code-block:: powershell

   # Using winget
   winget install Python.Python.3.11
   
   # Or download from python.org

Verify:

.. code-block:: bash

   python3 --version
