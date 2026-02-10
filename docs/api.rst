API Reference
=============

Python API
----------

JeevesRouter
^^^^^^^^^^^^

The main class for routing requests.

.. code-block:: python

   from jeeves import JeevesRouter

   router = JeevesRouter()

Constructor
~~~~~~~~~~~

.. py:class:: JeevesRouter(config=None)

   Initialize the router.

   :param config: Optional JeevesConfig instance. If not provided, loads from default location.
   :type config: JeevesConfig or None

   Example:

   .. code-block:: python

      # Use default config
      router = JeevesRouter()

      # Use custom config
      from jeeves import JeevesConfig
      config = JeevesConfig()
      config.config['jeeves']['default_model'] = 'qwen2.5:0.5b'
      router = JeevesRouter(config)

Methods
~~~~~~~

.. py:method:: JeevesRouter.route(request: str) -> dict

   Route a request and return routing information.

   :param str request: The user's request
   :return: Dictionary with routing details
   :rtype: dict

   Return dictionary structure:

   .. code-block:: python

      {
          'destination': 'local' or 'cloud',
          'method': 'pattern_match' or 'llm_classification' or 'fallback_uncertainty',
          'result': str,  # Only for local
          'should_escalate': bool,
          'classification': dict  # Only for LLM classification
      }

   Example:

   .. code-block:: python

      result = router.route("ls -la")
      
      if result['should_escalate']:
          print("Send to cloud:", result['method'])
      else:
          print("Local result:", result['result'])

.. py:method:: JeevesRouter.handle(request: str) -> str

   Convenience method that returns result or escalation marker.

   :param str request: The user's request
   :return: Result string or "[JEEVES_ESCALATE] <reason>"
   :rtype: str

   Example:

   .. code-block:: python

      result = router.handle("analyze this code")
      
      if result.startswith("[JEEVES_ESCALATE]"):
          # Send to cloud
          pass
      else:
          print(result)

JeevesConfig
^^^^^^^^^^^^

Configuration management class.

.. code-block:: python

   from jeeves import JeevesConfig

   config = JeevesConfig()

Constructor
~~~~~~~~~~~

.. py:class:: JeevesConfig()

   Load or create configuration.

   Config is stored at: ``~/.config/jeeves/config.json``

Methods
~~~~~~~

.. py:method:: JeevesConfig.load_config() -> dict

   Load configuration from file.

   :return: Configuration dictionary
   :rtype: dict

.. py:method:: JeevesConfig.save_config() -> bool

   Save current configuration to file.

   :return: True if successful
   :rtype: bool

.. py:method:: JeevesConfig.is_ollama_installed() -> bool

   Check if Ollama is installed.

   :return: True if installed
   :rtype: bool

.. py:method:: JeevesConfig.is_ollama_running() -> bool

   Check if Ollama server is running.

   :return: True if running
   :rtype: bool

.. py:method:: JeevesConfig.start_ollama() -> bool

   Start Ollama server in background.

   :return: True if started successfully
   :rtype: bool

.. py:method:: JeevesConfig.get_installed_models() -> list

   Get list of installed Ollama models.

   :return: List of model names
   :rtype: list[str]

.. py:method:: JeevesConfig.pull_model(model_name: str) -> bool

   Download a model from Ollama registry.

   :param str model_name: Name of model to download (e.g., "qwen2.5:1.5b")
   :return: True if successful
   :rtype: bool

CLI API
-------

Commands
^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``jeeves setup``
     - Run interactive setup wizard
   * - ``jeeves status``
     - Show Jeeves and Ollama status
   * - ``jeeves models``
     - Manage installed models
   * - ``jeeves switch``
     - Switch default model
   * - ``jeeves route "<request>"``
     - Route a single request
   * - ``jeeves interactive``
     - Start interactive mode
   * - ``jeeves --help``
     - Show help

Exit Codes
^^^^^^^^^^

.. list-table::
   :header-rows: 1

   * - Code
     - Meaning
   * - 0
     - Success
   * - 1
     - General error
   * - 2
     - Ollama not found
   * - 3
     - Ollama not running
   * - 4
     - Config error

Configuration Schema
--------------------

Full configuration file structure:

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
       "fallback_threshold": 0.7,
       "classification_prompt": "simple"
     },
     "routing": {
       "use_pattern_matching": true,
       "use_local_llm": true,
       "auto_fallback": true,
       "cloud_on_uncertainty": true
     },
     "installed_models": [],
     "last_setup": "2026-02-09 12:00:00"
   }

Schema Details
^^^^^^^^^^^^^^

**ollama**

.. list-table::
   :header-rows: 1

   * - Key
     - Type
     - Default
     - Description
   * - host
     - string
     - "http://localhost:11434"
     - Ollama server URL
   * - autostart
     - boolean
     - true
     - Auto-start Ollama if not running
   * - autostart_with_kimi
     - boolean
     - true
     - Start when Kimi starts

**jeeves**

.. list-table::
   :header-rows: 1

   * - Key
     - Type
     - Default
     - Description
   * - default_model
     - string
     - "qwen2.5:1.5b"
     - Default local LLM
   * - timeout_seconds
     - integer
     - 30
     - Timeout for local LLM calls
   * - fallback_threshold
     - float
     - 0.7
     - Confidence threshold (0-1)
   * - classification_prompt
     - string
     - "simple"
     - Prompt style for classification

**routing**

.. list-table::
   :header-rows: 1

   * - Key
     - Type
     - Default
     - Description
   * - use_pattern_matching
     - boolean
     - true
     - Enable pattern matching
   * - use_local_llm
     - boolean
     - true
     - Enable LLM classification
   * - auto_fallback
     - boolean
     - true
     - Auto-escalate on uncertainty
   * - cloud_on_uncertainty
     - boolean
     - true
     - Send to cloud if unsure

Routing Methods
---------------

Pattern Matching
^^^^^^^^^^^^^^^^

Fast regex-based matching for common commands.

**Shell Patterns:**

- ``ls``, ``ll``, ``cat``, ``grep``, ``find``
- ``cd``, ``pwd``, ``head``, ``tail``
- ``wc``, ``du``, ``df``, ``mkdir``, ``touch``
- ``rm``, ``cp``, ``mv``, ``chmod``, ``chown``
- ``ps``, ``top``, ``kill``, ``ping``, ``curl``
- ``git``, ``which``, ``echo``, ``export``
- ``whoami``, ``id``, ``uname``, ``date``
- ``uptime``, ``free``, ``netstat``, ``lsof``

**File Patterns:**

- ``read <file>``
- ``show <file>``
- ``cat <file>``
- ``display <file>``
- ``view <file>``
- ``list files in <dir>``

LLM Classification
^^^^^^^^^^^^^^^^^^

Local LLM classifies request complexity.

**Categories:**

- **SIMPLE**: Basic shell commands, file operations, simple queries
- **MODERATE**: Multi-step local operations, code analysis
- **COMPLEX**: Design decisions, creative tasks, deep reasoning
- **UNCERTAIN**: Unclear or ambiguous request

Fallback Triggers
^^^^^^^^^^^^^^^^^

Conditions that trigger escalation to cloud:

1. LLM classification is COMPLEX
2. LLM classification is UNCERTAIN
3. Local LLM response contains uncertainty markers
4. Local LLM response is too short (< 50 chars)
5. Local LLM times out
6. Pattern match fails and user has disabled LLM

Environment Variables
---------------------

.. list-table::
   :header-rows: 1

   * - Variable
     - Description
     - Example
   * - JEEVES_CONFIG
     - Path to config file
     - /path/to/config.json
   * - JEEVES_MODEL
     - Override default model
     - qwen2.5:0.5b
   * - OLLAMA_HOST
     - Ollama server URL
     - http://localhost:11434
   * - JEEVES_DEBUG
     - Enable debug logging
     - 1
