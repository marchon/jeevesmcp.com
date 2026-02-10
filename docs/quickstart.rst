Quick Start Guide
=================

This guide will get you up and running with Jeeves in 5 minutes.

First Run
---------

After installation, run the setup wizard:

.. code-block:: bash

   jeeves setup

You'll be prompted through:

1. **Ollama Configuration**
   - Confirm Ollama is running
   - Set autostart preferences

2. **Model Selection**
   - Choose from recommended models
   - Download if not installed

3. **Routing Preferences**
   - Enable/disable pattern matching
   - Enable/disable auto-fallback

Try Interactive Mode
--------------------

Start the interactive shell:

.. code-block:: bash

   jeeves interactive

Example session:

.. code-block:: text

   🎩 Jeeves Interactive Mode
   Type 'exit' or 'quit' to exit

   You: ls -la
   🤖 Jeeves (pattern_match)
   total 128
   drwxr-xr-x  12 user user  4096 Feb  9 10:00 .
   drwxr-xr-x   5 user user  4096 Feb  9 09:00 ..
   -rw-r--r--   1 user user  2200 Feb  9 10:00 README.md
   ...

   You: cat README.md
   🤖 Jeeves (pattern_match)
   # Jeeves
   Your intelligent assistant...

   You: explain quantum computing
   🤖 Jeeves → ☁️ Kimi (llm_classification)
      [Would be sent to Kimi for processing]

Your First Request
------------------

Route a single request:

.. code-block:: bash

   jeeves route "list all Python files"

Output:

.. code-block:: text

   Routing: local (pattern_match)

   main.py
   setup.py
   router.py
   config.py

Understanding the Output
------------------------

When Jeeves processes a request, it tells you:

- **Routing**: Where the request went (``local`` or ``cloud``)
- **Method**: How it decided (``pattern_match``, ``llm_classification``, etc.)

Examples:

.. list-table::
   :header-rows: 1

   * - Output
     - Meaning
   * - ``Routing: local (pattern_match)``
     - Recognized pattern, handled instantly
   * - ``Routing: local (llm_classification)``
     - Local LLM handled it
   * - ``Routing: cloud (llm_classification)``
     - Sent to cloud AI
   * - ``Routing: cloud (fallback_uncertainty)``
     - Local was unsure, escalated

Common Commands
---------------

Check Status
^^^^^^^^^^^^

.. code-block:: bash

   jeeves status

Shows:
- Ollama status
- Installed models
- Current configuration

Switch Models
^^^^^^^^^^^^^

.. code-block:: bash

   jeeves switch

Interactive model selection:
- See installed models
- Download new models
- Set default model

Manage Models
^^^^^^^^^^^^^

.. code-block:: bash

   jeeves models

Options:
- Install new models
- Remove old models
- Check model sizes
- Update from remote

Test Routing
^^^^^^^^^^^^

.. code-block:: bash

   # Should go local (fast)
   jeeves route "pwd"

   # Should go local (file op)
   jeeves route "ls -la"

   # Might escalate (complex)
   jeeves route "analyze this codebase"

Next Steps
----------

1. **Read the Configuration Guide**
   
   Customize Jeeves to your needs:
   
   .. code-block:: bash
   
      # Edit config
      nano ~/.config/jeeves/config.json

2. **Try Different Models**
   
   Experiment with speed vs. quality:
   
   .. code-block:: bash
   
      jeeves switch
      # Try qwen2.5:0.5b for maximum speed

3. **Integrate with Your Editor**
   
   Use Jeeves from Vim, VS Code, etc.:
   
   .. code-block:: vim
   
      " Vim example
      :!jeeves route "explain %"

4. **Python Integration**
   
   Use Jeeves in your Python scripts:
   
   .. code-block:: python
   
      from jeeves import JeevesRouter
      
      router = JeevesRouter()
      result = router.handle("your request")

Tips for New Users
------------------

1. **Start with defaults** - The default model (qwen2.5:1.5b) works well for most users
2. **Test simple commands first** - Try ``ls``, ``cat``, ``grep`` to verify it's working
3. **Watch the routing** - Notice which requests go local vs. cloud
4. **Adjust if needed** - If too many escalate, lower the fallback threshold
5. **Keep it simple** - Jeeves shines on routine tasks, not replacing cloud AI
