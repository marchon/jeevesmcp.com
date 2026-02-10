Installation
============

System Requirements
-------------------

**Minimum:**

- Python 3.8+
- 2GB RAM
- 2GB free disk space
- Linux or macOS (Windows via WSL)

**Recommended:**

- Python 3.10+
- 4GB RAM
- 5GB free disk space
- SSD storage

One-Line Install (Recommended)
------------------------------

.. code-block:: bash

   curl -fsSL https://raw.githubusercontent.com/marchon/jeevesmcp.com/main/install.sh | bash

This command:

1. Detects your operating system
2. Installs Ollama (if not present)
3. Downloads Jeeves to ``~/.local/share/jeeves``
4. Installs Python dependencies
5. Creates the ``jeeves`` command
6. Starts Ollama server
7. Runs interactive setup

Manual Installation
-------------------

If you prefer to install manually or the one-liner doesn't work:

Step 1: Install Ollama
^^^^^^^^^^^^^^^^^^^^^^

**Linux/macOS:**

.. code-block:: bash

   curl -fsSL https://ollama.com/install.sh | sh

**Windows:**

Download from https://ollama.com/download

Step 2: Clone Repository
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   git clone https://github.com/marchon/jeevesmcp.com.git ~/.local/share/jeeves
   cd ~/.local/share/jeeves

Step 3: Install Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   pip install -r requirements.txt

Or with a virtual environment (recommended):

.. code-block:: bash

   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

Step 4: Create Command
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   mkdir -p ~/.local/bin
   ln -sf ~/.local/share/jeeves/main.py ~/.local/bin/jeeves
   chmod +x ~/.local/bin/jeeves

Step 5: Add to PATH
^^^^^^^^^^^^^^^^^^^

Add to your shell profile (``~/.bashrc``, ``~/.zshrc``, etc.):

.. code-block:: bash

   export PATH="$HOME/.local/bin:$PATH"

Then reload:

.. code-block:: bash

   source ~/.bashrc  # or ~/.zshrc

Step 6: Run Setup
^^^^^^^^^^^^^^^^^

.. code-block:: bash

   jeeves setup

Verification
------------

Check that everything is working:

.. code-block:: bash

   jeeves status

Expected output:

.. code-block:: text

   🎩 Jeeves Status
   
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

Remove Jeeves completely:

.. code-block:: bash

   # Remove Jeeves files
   rm -rf ~/.local/share/jeeves
   rm -f ~/.local/bin/jeeves
   rm -rf ~/.config/jeeves

   # Optional: Remove Ollama (also removes all models)
   rm -rf ~/.ollama
   which ollama && rm "$(which ollama)"

Troubleshooting Installation
----------------------------

"Permission denied" errors
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Make sure scripts are executable
   chmod +x ~/.local/bin/jeeves
   chmod +x ~/.local/share/jeeves/install.sh

"Command not found: jeeves"
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Check if ~/.local/bin is in PATH
   echo $PATH | grep -q ".local/bin" && echo "✓ In PATH" || echo "✗ Not in PATH"
   
   # Add it
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc

Ollama installation fails
^^^^^^^^^^^^^^^^^^^^^^^^^

Try installing Ollama manually:

.. code-block:: bash

   # Check if Ollama is already installed
   which ollama
   
   # If not, install manually
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Start Ollama
   ollama serve

Model download fails
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Check Ollama is running
   curl http://localhost:11434/api/tags
   
   # Try pulling manually
   ollama pull qwen2.5:1.5b
   
   # Check disk space
   df -h ~

Python not found
^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Install Python 3
   # Ubuntu/Debian:
   sudo apt update && sudo apt install python3 python3-pip
   
   # macOS:
   brew install python3
   
   # Verify
   python3 --version
