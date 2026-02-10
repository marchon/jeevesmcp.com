Platform Support
================

Jeeves is designed to work seamlessly across different operating systems and shells. This guide covers platform-specific installation, configuration, and usage instructions.

Operating System Support
------------------------

Linux
^^^^^

**Fully Supported**

Linux is Jeeves' primary development platform with full feature support.

**Installation:**

.. code-block:: bash

   curl -fsSL https://raw.githubusercontent.com/marchon/jeevesmcp.com/main/install.sh | bash

**Shell Support:**

- ✅ Bash (default on most distros)
- ✅ Zsh (popular alternative)
- ✅ Fish (friendly interactive shell)

**Terminal Support:**

- ✅ GNOME Terminal
- ✅ Konsole (KDE)
- ✅ xfce4-terminal (XFCE)
- ✅ Alacritty
- ✅ kitty
- ✅ xterm

**Config Location:**

.. code-block:: text

   ~/.config/jeeves/config.json

**Auto-start Setup:**

Add to your shell config (``~/.bashrc`` or ``~/.zshrc``):

.. code-block:: bash

   # Start Jeeves with terminal
   if command -v jeeves &> /dev/null; then
       eval "$(jeeves shell-hook)"
   fi

macOS
^^^^^

**Fully Supported**

macOS has native support with excellent Terminal.app and iTerm2 integration.

**Installation:**

.. code-block:: bash

   curl -fsSL https://raw.githubusercontent.com/marchon/jeevesmcp.com/main/install.sh | bash

**Shell Support:**

- ✅ Zsh (default on macOS Catalina+)
- ✅ Bash (if installed)
- ✅ Fish

**Terminal Support:**

- ✅ Terminal.app (built-in)
- ✅ iTerm2 (recommended)
- ✅ Alacritty
- ✅ Hyper

**Config Location:**

.. code-block:: text

   ~/Library/Application Support/jeeves/config.json

**iTerm2 Integration:**

For automatic terminal launching:

.. code-block:: bash

   # Add to ~/.zshrc
   export JEEVES_TERMINAL=iterm2

**Apple Silicon (M1/M2/M3):**

Ollama runs natively on Apple Silicon for optimal performance:

.. code-block:: bash

   # Verify architecture
   arch
   # Should print: arm64

Windows
^^^^^^^

**Supported via WSL**

Jeeves works best on Windows through WSL2 (Windows Subsystem for Linux).

**WSL2 Installation:**

1. Install WSL2 if not already installed:

.. code-block:: powershell

   wsl --install

2. Inside WSL2, install Jeeves:

.. code-block:: bash

   curl -fsSL https://raw.githubusercontent.com/marchon/jeevesmcp.com/main/install.sh | bash

**PowerShell (Native):**

Native Windows PowerShell support is experimental:

.. code-block:: powershell

   # Install Ollama for Windows first
   # Download from: https://ollama.com/download

   # Clone Jeeves
   git clone https://github.com/marchon/jeevesmcp.com.git $env:LOCALAPPDATA\jeeves
   cd $env:LOCALAPPDATA\jeeves
   pip install -r requirements.txt

**Shell Support:**

- ✅ PowerShell (Windows native)
- ✅ Bash (via WSL)
- ✅ Zsh (via WSL)
- ⚠️ CMD (limited)

**Config Location:**

Native Windows:

.. code-block:: text

   %APPDATA%\jeeves\config.json

WSL:

.. code-block:: text

   ~/.config/jeeves/config.json

**Windows Terminal Integration:**

For the best experience, use Windows Terminal:

.. code-block:: json

   // Add to Windows Terminal settings.json
   {
       "guid": "{your-guid}",
       "name": "Jeeves",
       "commandline": "wsl -d Ubuntu jeeves interactive",
       "icon": "C:\\path\\to\\jeeves.ico"
   }

Shell-Specific Configuration
----------------------------

Bash
^^^^

**Config File:** ``~/.bashrc``

**Basic Setup:**

.. code-block:: bash

   # Add Jeeves to PATH
   export PATH="$HOME/.local/bin:$PATH"

   # Optional: Auto-start Jeeves
   if command -v jeeves &> /dev/null; then
       export JEEVES_AUTOSTART=1
   fi

**Alias Examples:**

.. code-block:: bash

   alias j="jeeves route"
   alias jeeves-status="jeeves status"
   alias jeeves-setup="jeeves setup"

Zsh
^^^

**Config File:** ``~/.zshrc`` (or ``~/.zprofile``)

**Basic Setup:**

.. code-block:: bash

   # Add Jeeves to PATH
   export PATH="$HOME/.local/bin:$PATH"

   # Optional: Enable completions
   eval "$(jeeves completions zsh)"

**Oh My Zsh Plugin:**

Add to plugins in ``~/.zshrc``:

.. code-block:: bash

   plugins=(... jeeves)

Fish
^^^^

**Config File:** ``~/.config/fish/config.fish``

**Basic Setup:**

.. code-block:: fish

   # Add Jeeves to PATH
   fish_add_path ~/.local/bin

   # Optional: Abbreviations
   abbr -a j 'jeeves route'
   abbr -a js 'jeeves status'

**Completions:**

Fish completions are auto-generated:

.. code-block:: fish

   jeeves completions fish > ~/.config/fish/completions/jeeves.fish

PowerShell
^^^^^^^^^^

**Config File:** ``$PROFILE``

Find your profile:

.. code-block:: powershell

   $PROFILE
   # Usually: C:\Users\<name>\Documents\PowerShell\Microsoft.PowerShell_profile.ps1

**Basic Setup:**

.. code-block:: powershell

   # Add Jeeves to PATH
   $env:PATH += ";$env:LOCALAPPDATA\jeeves\bin"

   # Optional: Alias
   Set-Alias -Name j -Value jeeves

**Profile Functions:**

.. code-block:: powershell

   function Jeeves-Status { jeeves status }
   function Jeeves-Setup { jeeves setup }
   Set-Alias -Name js -Value Jeeves-Status

Terminal Integration
--------------------

Launching Commands in New Terminal Windows
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Jeeves can open commands in new terminal windows when needed.

**Linux:**

.. code-block:: bash

   # Auto-detected terminal
   jeeves route "open new terminal"

   # Force specific terminal
   export JEEVES_TERMINAL=gnome-terminal  # or konsole, xfce4-terminal

**macOS:**

.. code-block:: bash

   # Terminal.app (default)
   jeeves route "open new terminal"

   # iTerm2
   export JEEVES_TERMINAL=iterm2

**Windows (PowerShell):**

.. code-block:: powershell

   # Windows Terminal
   $env:JEEVES_TERMINAL = "windows-terminal"

   # Legacy console
   $env:JEEVES_TERMINAL = "cmd"

Terminal Detection
^^^^^^^^^^^^^^^^^^

Jeeves automatically detects your terminal emulator:

.. list-table:: Supported Terminals
   :header-rows: 1

   * - Terminal
     - Linux
     - macOS
     - Windows
   * - GNOME Terminal
     - ✅
     - ❌
     - ❌
   * - Konsole
     - ✅
     - ❌
     - ❌
   * - iTerm2
     - ❌
     - ✅
     - ❌
   * - Terminal.app
     - ❌
     - ✅
     - ❌
   * - Windows Terminal
     - ❌
     - ❌
     - ✅
   * - Alacritty
     - ✅
     - ✅
     - ✅
   * - VS Code Terminal
     - ✅
     - ✅
     - ✅

Platform-Specific Paths
-----------------------

Jeeves adapts its paths based on your platform:

.. list-table:: Default Paths by Platform
   :header-rows: 1

   * - Path
     - Linux
     - macOS
     - Windows
   * - Install Directory
     - ``~/.local/share/jeeves``
     - ``~/.local/share/jeeves``
     - ``%LOCALAPPDATA%\jeeves``
   * - Config Directory
     - ``~/.config/jeeves``
     - ``~/Library/Application Support/jeeves``
     - ``%APPDATA%\jeeves``
   * - Binary Directory
     - ``~/.local/bin``
     - ``~/.local/bin``
     - ``%LOCALAPPDATA%\jeeves\bin``
   * - Log Files
     - ``~/.local/share/jeeves/logs``
     - ``~/Library/Logs/jeeves``
     - ``%LOCALAPPDATA%\jeeves\logs``

Platform Detection API
----------------------

Jeeves provides a platform detection module for scripts and integrations:

.. code-block:: python

   from platform_utils import PlatformInfo, get_platform_info

   # Get comprehensive platform info
   info = get_platform_info()

   print(f"OS: {info.os.value}")           # 'linux', 'macos', 'windows'
   print(f"Shell: {info.shell.value}")     # 'bash', 'zsh', 'powershell', etc.
   print(f"Terminal: {info.terminal.value}")  # 'gnome-terminal', 'iterm2', etc.

   # Check platform
   if info.os.value == 'linux':
       # Linux-specific code
       pass

   # Get platform paths
   config_dir = info.config_dir
   install_dir = info.get_install_dir()

   # Launch in new terminal
   from platform_utils import open_in_terminal
   open_in_terminal("ollama serve", title="Ollama Server")

Environment Variables
---------------------

Platform-specific environment variables:

.. list-table:: Environment Variables
   :header-rows: 1

   * - Variable
     - Description
     - Example
   * - ``JEEVES_CONFIG``
     - Override config directory
     - ``/path/to/config``
   * - ``JEEVES_TERMINAL``
     - Force terminal emulator
     - ``iterm2``, ``gnome-terminal``
   * - ``JEEVES_SHELL``
     - Override shell detection
     - ``bash``, ``zsh``, ``fish``
   * - ``OLLAMA_HOST``
     - Ollama server URL
     - ``http://localhost:11434``

Troubleshooting by Platform
---------------------------

Linux
^^^^^

**Issue:** "ollama: command not found"

.. code-block:: bash

   # Check if Ollama is in PATH
   which ollama

   # If not, add to ~/.bashrc
   export PATH="$HOME/.local/bin:$PATH"

**Issue:** Permission denied when installing

.. code-block:: bash

   # Fix ownership
   sudo chown -R $USER:$USER ~/.local/share/jeeves
   sudo chown -R $USER:$USER ~/.config/jeeves

macOS
^^^^^

**Issue:** "command not found: jeeves"

.. code-block:: bash

   # On Apple Silicon, check Rosetta
   arch -x86_64 jeeves status

   # Or use native ARM version
   arch -arm64 jeeves status

**Issue:** Ollama won't start

.. code-block:: bash

   # Check if Ollama.app is in Applications
   ls /Applications/Ollama.app

   # Or install via Homebrew
   brew install --cask ollama

Windows (WSL)
^^^^^^^^^^^^^

**Issue:** WSL can't find Windows Ollama

.. code-block:: bash

   # In WSL, access Windows Ollama
   export OLLAMA_HOST=http://$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):11434

**Issue:** Path translation problems

.. code-block:: bash

   # Convert Windows paths
   wslpath 'C:\Users\name\file.txt'

   # Convert WSL paths to Windows
   wslpath -w ~/.config/jeeves/config.json
