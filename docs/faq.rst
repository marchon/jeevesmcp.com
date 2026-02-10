Frequently Asked Questions
==========================

General Questions
-----------------

What is Jeeves?
^^^^^^^^^^^^^^^

Jeeves is an intelligent request router that decides whether to handle AI requests locally (fast, free) or send them to the cloud (powerful, capable). It uses a tiny local LLM to classify request complexity and routes accordingly.

Why should I use Jeeves?
^^^^^^^^^^^^^^^^^^^^^^^^

- **Speed**: 80-99% faster for routine tasks
- **Cost**: Free local execution for simple queries
- **Privacy**: Sensitive data stays local
- **Reliability**: Works offline for local tasks
- **Developer Experience**: Stay in flow state

How much does it cost?
^^^^^^^^^^^^^^^^^^^^^^

Jeeves is **free and open source**. Local execution uses your own hardware. Cloud escalation costs depend on your cloud AI provider (Kimi, Claude, etc.).

What platforms are supported?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Linux (x86_64, ARM64)
- macOS (Intel, Apple Silicon)
- Windows (via WSL2)

Installation
------------

Do I need a GPU?
^^^^^^^^^^^^^^^^

No. Jeeves uses small models (1-2GB) that run well on CPU. A GPU helps but is not required.

How much disk space do I need?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Minimum: 2GB (for Jeeves + 1 small model)
- Recommended: 5GB (for multiple models)

Do I need to install Ollama separately?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

No. The installer will install Ollama automatically if it's not present. You can also install it manually first.

Can I use Jeeves without internet?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Partially. Local tasks work offline. Cloud escalation requires internet.

The installer failed. What do I do?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Try manual installation:

1. Install Ollama: ``curl -fsSL https://ollama.com/install.sh | sh``
2. Clone Jeeves: ``git clone https://github.com/marchon/jeevesmcp.com.git ~/.local/share/jeeves``
3. Install deps: ``pip install -r ~/.local/share/jeeves/requirements.txt``
4. Create link: ``ln -s ~/.local/share/jeeves/main.py ~/.local/bin/jeeves``
5. Run setup: ``jeeves setup``

Configuration
-------------

Where is the config file?
^^^^^^^^^^^^^^^^^^^^^^^^^

``~/.config/jeeves/config.json``

How do I change the default model?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   jeeves switch

Or edit the config:

.. code-block:: json

   {
     "jeeves": {
       "default_model": "llama3.2:3b"
     }
   }

How do I disable pattern matching?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   {
     "routing": {
       "use_pattern_matching": false
     }
   }

How do I make everything go to the cloud?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Set ``use_local_llm`` to ``false``:

.. code-block:: json

   {
     "routing": {
       "use_local_llm": false
     }
   }

Models
------

Which model should I use?
^^^^^^^^^^^^^^^^^^^^^^^^^

**Quick answer**: Start with ``qwen2.5:1.5b`` (default)

**For maximum speed**: ``qwen2.5:0.5b`` (400MB)

**For better reasoning**: ``llama3.2:3b`` (2GB)

**For complex local tasks**: ``qwen2.5:7b`` (4.5GB)

Can I use my own fine-tuned model?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes, if it's compatible with Ollama. Import it:

.. code-block:: bash

   ollama create my-model -f Modelfile

Then set it as default:

.. code-block:: bash

   jeeves switch
   # Select my-model

How do I delete a model?
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   ollama rm model-name

Or use the model manager:

.. code-block:: bash

   jeeves models
   # Select "Remove model"

Routing & Behavior
------------------

Why did my request go to the cloud?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Possible reasons:

1. **Complex request**: LLM classified it as needing cloud capabilities
2. **Uncertainty**: Local model wasn't confident
3. **Pattern miss**: No shell/file pattern matched
4. **LLM disabled**: You've disabled local LLM

Check the routing reason with:

.. code-block:: bash

   jeeves route "your request"

Why is everything going local?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Possible reasons:

1. **Pattern match**: Request matched shell/file pattern
2. **High confidence**: Local LLM was very confident
3. **Fallback disabled**: ``auto_fallback`` is ``false``

Lower the fallback threshold:

.. code-block:: json

   {
     "jeeves": {
       "fallback_threshold": 0.5
     }
   }

How do I force cloud escalation?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Currently, you can't force it from CLI. The local LLM decides. However, you can:

1. Disable local LLM entirely
2. Rephrase request to sound more complex
3. Use the Python API to bypass routing

Can I add custom patterns?
^^^^^^^^^^^^^^^^^^^^^^^^^^

Not yet. This is on the roadmap. For now, use the Python API:

.. code-block:: python

   from jeeves import JeevesRouter
   
   router = JeevesRouter()
   
   # Custom logic
   if request.startswith("my-pattern"):
       result = handle_my_pattern(request)
   else:
       result = router.route(request)

Troubleshooting
---------------

Ollama won't start
^^^^^^^^^^^^^^^^^^

Check if port 11434 is in use:

.. code-block:: bash

   lsof -i :11434
   
   # Or on Linux
   netstat -tlnp | grep 11434

Kill the process or change Ollama's port:

.. code-block:: bash

   OLLAMA_HOST=localhost:11435 ollama serve

Model download is slow
^^^^^^^^^^^^^^^^^^^^^^

Ollama downloads can be slow. Try:

1. Using a different mirror
2. Downloading at off-peak hours
3. Using a smaller model

Local responses are too slow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Solutions:

1. Switch to a smaller model: ``jeeves switch`` → ``qwen2.5:0.5b``
2. Increase timeout: ``timeout_seconds: 60``
3. Check CPU usage: ``htop`` or ``top``
4. Close other applications

"Command not found: jeeves"
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add to PATH:

.. code-block:: bash

   export PATH="$HOME/.local/bin:$PATH"
   
   # Add to your shell profile
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc

Pattern matching not working
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Check it's enabled:

.. code-block:: bash

   jeeves status
   # Look for "Pattern matching: ✅ On"

If off, run setup again:

.. code-block:: bash

   jeeves setup

Integration
-----------

Does Jeeves work with Kimi?
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes! Jeeves is designed to work alongside Kimi:

.. code-block:: python

   from jeeves import JeevesRouter
   import kimi
   
   router = JeevesRouter()
   result = router.route(user_input)
   
   if result['should_escalate']:
       response = kimi.generate(user_input)
   else:
       response = result['result']

Does Jeeves work with Claude?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes! Same pattern:

.. code-block:: python

   from jeeves import JeevesRouter
   import anthropic
   
   router = JeevesRouter()
   result = router.route(user_input)
   
   if result['should_escalate']:
       client = anthropic.Anthropic()
       message = client.messages.create(
           model="claude-3-opus-20240229",
           messages=[{"role": "user", "content": user_input}]
       )
       response = message.content[0].text

Can I use Jeeves in my editor?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes. Examples:

**Vim:**

.. code-block:: vim

   " Explain current file
   :!jeeves route "explain %"

**VS Code:**

Create a task in ``tasks.json``:

.. code-block:: json

   {
     "label": "Ask Jeeves",
     "type": "shell",
     "command": "jeeves",
     "args": ["route", "${input:question}"]
   }

Can I use Jeeves from Python scripts?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes:

.. code-block:: python

   from jeeves import JeevesRouter
   
   router = JeevesRouter()
   
   # Simple usage
   result = router.handle("ls -la")
   
   # Advanced usage
   result = router.route("complex query")
   if result['should_escalate']:
       # Handle cloud escalation
       pass

Development
-----------

How do I contribute?
^^^^^^^^^^^^^^^^^^^^

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

See CONTRIBUTING.md (if available) for guidelines.

How do I report a bug?
^^^^^^^^^^^^^^^^^^^^^^

Open an issue: https://github.com/marchon/jeevesmcp.com/issues

Include:
- OS and version
- Python version
- Jeeves version
- Steps to reproduce
- Expected vs actual behavior

How do I request a feature?
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Open a discussion: https://github.com/marchon/jeevesmcp.com/discussions

Or an issue with the "feature request" label.

Can I fork Jeeves?
^^^^^^^^^^^^^^^^^^

Yes! Jeeves is MIT licensed. You can fork, modify, and distribute it.

Miscellaneous
-------------

Is Jeeves related to Ask Jeeves?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

No. The name is a nod to P.G. Wodehouse's character - a capable assistant who knows when to ask for help.

Why the top hat (🎩) in the logo?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Jeeves (the character) was a valet, often depicted wearing a formal suit and top hat. The emoji represents that elegance and capability.

What's the difference between Jeeves and Ollama?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Ollama**: Runs local LLMs (the engine)
- **Jeeves**: Routes requests between local and cloud (the router)

Jeeves uses Ollama for local execution.

Can I use Jeeves commercially?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Yes. MIT license allows commercial use.

Is there a paid version?
^^^^^^^^^^^^^^^^^^^^^^^^

No. Jeeves is completely free and open source.

Where can I get help?
^^^^^^^^^^^^^^^^^^^^^

- **Documentation**: You're reading it!
- **Issues**: https://github.com/marchon/jeevesmcp.com/issues
- **Discussions**: https://github.com/marchon/jeevesmcp.com/discussions
