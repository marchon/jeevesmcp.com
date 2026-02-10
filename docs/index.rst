Jeeves 🎩
=========

**Your intelligent assistant that knows when to ask for help.**

Jeeves is a smart request router that uses a tiny local LLM to handle simple tasks instantly while automatically escalating complex requests to cloud AI (Kimi, Claude, etc.). Stop waiting seconds for cloud round-trips when milliseconds will do.

----

TL;DR - Install in 10 Seconds
-----------------------------

.. code-block:: bash

   curl -fsSL https://raw.githubusercontent.com/marchon/jeevesmcp.com/main/install.sh | bash

That's it. Jeeves installs Ollama (if needed), downloads a small local model, and runs an interactive setup. You'll be routing requests in under a minute.

----

What Is Jeeves?
---------------

Jeeves is an **intelligent request router** that sits between you and your AI assistant. It decides whether to handle requests locally (fast, private, free) or send them to the cloud (powerful, capable).

Think of it as a smart receptionist: simple questions get answered immediately, complex ones get escalated to the expert.

What Does It Do?
----------------

**Three Core Functions:**

1. **Pattern Matching** (0ms)
   - Instantly recognizes shell commands: ``ls``, ``cat``, ``grep``, etc.
   - Handles file operations: ``read file.txt``, ``show me config.json``
   - Zero latency for common tasks

2. **Local LLM Classification** (~100ms)
   - Uses a tiny local model (1-2GB) to classify request complexity
   - Simple queries → Handle locally
   - Complex queries → Escalate to cloud

3. **Auto-Fallback** (Seamless)
   - Detects when local model is uncertain
   - Automatically escalates to your cloud AI
   - No manual intervention needed

What Does It Install?
---------------------

**Components:**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Component
     - Purpose
   * - **Ollama**
     - Local LLM engine (if not present)
   * - **Jeeves Core**
     - Router logic, config management, CLI
   * - **Local Model**
     - Your chosen small LLM (default: qwen2.5:1.5b, ~1GB)
   * - **Config Files**
     - User preferences in ``~/.config/jeeves/``

**Disk Space:** ~1-2GB total (depending on model choice)

----

How It Works
------------

The Routing Decision Tree
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

   User Request
        │
        ▼
   ┌─────────────────────────┐
   │ 1. Pattern Matching     │ ◄── Shell commands, file ops
   │    Match? → LOCAL       │     (0 milliseconds)
   └─────────────────────────┘
        │ No match
        ▼
   ┌─────────────────────────┐
   │ 2. Local LLM Classifies │ ◄── "Is this simple or complex?"
   │    SIMPLE → Try Local   │     (~100 milliseconds)
   │    COMPLEX → Cloud      │
   └─────────────────────────┘
        │
        ▼
   ┌─────────────────────────┐
   │ 3. Validation           │ ◄── Good response? Return it
   │    Uncertain? → Cloud   │     Bad response? Escalate
   └─────────────────────────┘

Example Flows
^^^^^^^^^^^^^

**Example 1: Simple Shell Command**

.. code-block:: bash

   User: "ls -la"
   
   Jeeves: Pattern match → LOCAL
   Result: Directory listing (instant)

**Example 2: File Read**

.. code-block:: bash

   User: "show me README.md"
   
   Jeeves: Pattern match → LOCAL
   Result: File contents (instant)

**Example 3: Ambiguous Request**

.. code-block:: bash

   User: "analyze this codebase"
   
   Jeeves: LLM classifies as COMPLEX
   Action: Escalate to Kimi/Claude
   Result: Cloud AI handles it

**Example 4: Uncertain Local Response**

.. code-block:: bash

   User: "explain quantum computing"
   
   Jeeves: Tries local model
   Local: "I'm not sure about the details..."
   Jeeves: Detects uncertainty → CLOUD
   Result: Cloud AI provides full explanation

----

Why You Should Have It
----------------------

Speed
^^^^^

.. list-table::
   :header-rows: 1

   * - Request Type
     - Cloud Only
     - With Jeeves
   * - ``ls -la``
     - 2-5 seconds
     - 50 milliseconds
   * - ``read config.txt``
     - 2-5 seconds
     - 20 milliseconds
   * - Simple grep
     - 2-5 seconds
     - 100 milliseconds

**80-99% faster** for routine tasks.

Cost
^^^^

- Local execution: **Free**
- Cloud API calls: **$$$**
- Jeeves filters out simple requests before they hit your API budget

Privacy
^^^^^^^

- File listings, directory contents, simple commands never leave your machine
- Only complex queries go to cloud
- Sensitive data stays local

Reliability
^^^^^^^^^^^

- Works offline for local tasks
- No network dependency for simple operations
- Graceful degradation if cloud is unavailable

Developer Experience
^^^^^^^^^^^^^^^^^^^^

- Stop waiting for cloud round-trips
- Stay in flow state
- Use AI for what it's good at (complexity), not trivialities

----

Configuration Guide
-------------------

Config File Location
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   ~/.config/jeeves/config.json

Configuration Options
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   {
     "ollama": {
       "host": "http://localhost:11434",
       "autostart": true,
       "autostart_with_kimi": true
     },
     "jeeves": {
       "default_model": "qwen2.5:1.5b",
       "timeout_seconds": 30,
       "fallback_threshold": 0.7
     },
     "routing": {
       "use_pattern_matching": true,
       "use_local_llm": true,
       "auto_fallback": true,
       "cloud_on_uncertainty": true
     }
   }

Option Reference
^^^^^^^^^^^^^^^^

**Ollama Settings:**

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - ``host``
     - ``http://localhost:11434``
     - Ollama server URL
   * - ``autostart``
     - ``true``
     - Start Ollama if not running
   * - ``autostart_with_kimi``
     - ``true``
     - Auto-start when Kimi starts

**Jeeves Settings:**

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - ``default_model``
     - ``qwen2.5:1.5b``
     - Local LLM to use
   * - ``timeout_seconds``
     - ``30``
     - Max wait for local model
   * - ``fallback_threshold``
     - ``0.7``
     - Confidence threshold

**Routing Settings:**

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Description
   * - ``use_pattern_matching``
     - ``true``
     - Fast pattern recognition
   * - ``use_local_llm``
     - ``true``
     - Enable LLM classification
   * - ``auto_fallback``
     - ``true``
     - Escalate on uncertainty
   * - ``cloud_on_uncertainty``
     - ``true``
     - Always escalate if unsure

Changing Configuration
^^^^^^^^^^^^^^^^^^^^^^

**Via CLI:**

.. code-block:: bash

   jeeves setup  # Re-run setup wizard

**Via Text Editor:**

.. code-block:: bash

   nano ~/.config/jeeves/config.json
   # Edit, save, restart Jeeves

Environment Variables
^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Variable
     - Description
   * - ``JEEVES_CONFIG``
     - Path to custom config file
   * - ``JEEVES_MODEL``
     - Override default model
   * - ``OLLAMA_HOST``
     - Override Ollama URL

----

More Suggestions & Tips
-----------------------

Model Selection Guide
^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Model
     - RAM
     - Speed
     - Best For
   * - ``qwen2.5:0.5b``
     - 1GB
     - ⚡ Very Fast
     - Routing only, minimal resources
   * - ``qwen2.5:1.5b`` ⭐
     - 2GB
     - 🚀 Fast
     - **Recommended default**
   * - ``llama3.2:3b``
     - 4GB
     - 🚀 Fast
     - Better reasoning
   * - ``deepseek-r1:1.5b``
     - 2GB
     - 🚀 Fast
     - Step-by-step logic

Switch models anytime:

.. code-block:: bash

   jeeves switch

Best Practices
^^^^^^^^^^^^^^

1. **Start Simple**: Use the default ``qwen2.5:1.5b`` model first
2. **Test Patterns**: Simple commands like ``ls``, ``cat`` should be instant
3. **Monitor Escalations**: If everything escalates, your threshold might be too high
4. **Adjust Timeout**: On slower machines, increase ``timeout_seconds`` to 60
5. **Keep Models Small**: For routing, you don't need large models

Integration Examples
^^^^^^^^^^^^^^^^^^^^

**With Kimi:**

.. code-block:: python

   from jeeves import JeevesRouter
   import kimi_client

   router = JeevesRouter()
   result = router.route("analyze this code")

   if result['should_escalate']:
       response = kimi_client.generate("analyze this code")
   else:
       response = result['result']

**With Claude:**

.. code-block:: python

   from jeeves import JeevesRouter
   import anthropic

   router = JeevesRouter()
   user_input = input("> ")
   
   result = router.route(user_input)
   
   if result['should_escalate']:
       client = anthropic.Anthropic()
       message = client.messages.create(
           model="claude-3-opus-20240229",
           messages=[{"role": "user", "content": user_input}]
       )

Common Use Cases
^^^^^^^^^^^^^^^^

1. **Development Workflow**
   - Quick file lookups: ``show me main.py``
   - Directory navigation: ``list all Python files``
   - Log tailing: ``show last 20 lines of error.log``

2. **System Administration**
   - Process checks: ``ps aux | grep python``
   - Disk usage: ``du -sh * | sort -h``
   - Service status: ``systemctl status nginx``

3. **Data Exploration**
   - File counts: ``how many files in this directory``
   - Size checks: ``what's the largest file here``
   - Quick greps: ``search for TODO in src/``

Troubleshooting Tips
^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Problem
     - Solution
   * - Slow responses
     - Switch to ``qwen2.5:0.5b`` model
   * - Too many escalations
     - Lower ``fallback_threshold`` to 0.5
   * - Ollama won't start
     - Check port 11434: ``lsof -i :11434``
   * - Model download fails
     - Try manual: ``ollama pull qwen2.5:1.5b``
   * - Pattern matching not working
     - Check ``use_pattern_matching: true`` in config

Feature Roadmap
^^^^^^^^^^^^^^^

- [ ] Custom pattern definitions
- [ ] Multi-model ensemble voting
- [ ] Response caching
- [ ] Web UI for configuration
- [ ] Plugin system for custom handlers
- [ ] Integration with more cloud providers

Getting Help
^^^^^^^^^^^^

- **Issues**: https://github.com/marchon/jeevesmcp.com/issues
- **Discussions**: https://github.com/marchon/jeevesmcp.com/discussions
- **Documentation**: You're reading it! 📖

----

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   :hidden:

   installation
   quickstart
   configuration
   api
   faq

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
