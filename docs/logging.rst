LLM Interaction Logging
=======================

Jeeves can log all interactions between you, the local LLM, and any escalated requests to primary AI systems. This is useful for debugging, understanding routing decisions, and verifying system behavior.

**Default:** Logging is **DISABLED** to protect your privacy.

Log Format
----------

When enabled, Jeeves creates timestamped log files:

**Filename Format:** ``LLM-LOG-MM:DD:YY:mm:ss:ms.log``

Example: ``LLM-LOG-02:09:26:14:30:25:123.log``

**Location:**

- **Linux:** ``~/.local/share/jeeves/logs/``
- **macOS:** ``~/Library/Logs/jeeves/``
- **Windows:** ``%LOCALAPPDATA%\jeeves\logs\``

What's Logged
-------------

Each interaction creates a complete audit trail:

1. **User Command**
   - The original request from the user
   - Timestamp

2. **System Context**
   - Jeeves version
   - Active model
   - Routing configuration

3. **Jeeves Decision Process**
   - Classification prompt sent to local LLM
   - Model used for classification
   - Classification response (SIMPLE/MODERATE/COMPLEX/UNCERTAIN)
   - Confidence score

4. **Escalation Details** (if applicable)
   - Reason for escalation
   - Target AI system (Kimi, Claude, etc.)
   - Full context sent to target AI

5. **Responses**
   - Local LLM response (if handled locally)
   - Target AI response (if escalated)
   - Execution results for local commands

6. **Final Result**
   - Summary of routing decision
   - Final output

Enabling Logging
----------------

During Setup
^^^^^^^^^^^^

The setup wizard will ask if you want to enable logging::

   📝 Step 7: LLM Interaction Logging (optional)

   Jeeves can log all LLM interactions for debugging:
     - User commands
     - LLM decision prompts and responses
     - Escalations to primary AI
     - Execution results

   Log format: LLM-LOG-MM:DD:YY:mm:ss:ms.log
   Default: DISABLED (recommended for privacy)

   Enable LLM interaction logging? [y/N]:

Via CLI
^^^^^^^

Enable logging::

   jeeves logging on

   # Output:
   # ✅ LLM interaction logging enabled
   #    Logs will be saved to: ~/.local/share/jeeves/logs
   #
   #    Log format: LLM-LOG-MM:DD:YY:mm:ss:ms.log
   #    Contains: User command → System context → LLM prompts → Responses

Disable logging::

   jeeves logging off

   # Output:
   # 🛑 LLM interaction logging disabled

Check status::

   jeeves logging status

   # Output:
   # ==================================================
   #   📝 LLM Logging Status
   # ==================================================
   #
   # Enabled:          ❌ No
   # Log directory:    /home/user/.local/share/jeeves/logs
   # Total log files:  0

Managing Log Files
------------------

List Recent Logs
^^^^^^^^^^^^^^^^

::

   jeeves logging list

   # Output:
   # 📁 Recent log files (showing 3 of 15):
   # ------------------------------------------------------------
   #  1. LLM-LOG-02:09:26:14:30:25:123.log (2,456 bytes)
   #  2. LLM-LOG-02:09:26:14:28:15:891.log (1,892 bytes)
   #  3. LLM-LOG-02:09:26:14:25:44:567.log (3,124 bytes)

View a Specific Log
^^^^^^^^^^^^^^^^^^^

::

   jeeves logging view --file LLM-LOG-02:09:26:14:30:25:123.log

   # Output shows the full JSON log with all interaction details

Clear Old Logs
^^^^^^^^^^^^^^

Keep only the 10 most recent logs (default)::

   jeeves logging clear

   # Output:
   # 🗑️  Cleared 5 old log files
   #    Kept 10 most recent logs
   #    10 log files remaining

Keep a specific number::

   jeeves logging clear --keep 5

Interactive Mode
^^^^^^^^^^^^^^^^

While in interactive mode, you can toggle logging::

   You: /logging on
   ✅ LLM interaction logging enabled

   You: /logging off
   🛑 LLM interaction logging disabled

Log File Structure
------------------

Each log file is a JSON document with the following structure::

   {
     "timestamp": "2026-02-09T14:30:25.123456",
     "level": "SESSION_START",
     "user_command": "analyze this Python code",
     "events": [
       {
         "timestamp": "2026-02-09T14:30:25.234567",
         "level": "INFO",
         "type": "SYSTEM_CONTEXT",
         "data": {
           "jeeves_version": "0.1.0",
           "default_model": "qwen2.5:1.5b"
         }
       },
       {
         "timestamp": "2026-02-09T14:30:25.345678",
         "level": "DECISION",
         "type": "JEEVES_DECISION_PROMPT",
         "model": "qwen2.5:1.5b",
         "prompt": "You are a request classifier...",
         "context": {"temperature": 0.1, "num_predict": 10}
       },
       {
         "timestamp": "2026-02-09T14:30:26.456789",
         "level": "DECISION",
         "type": "JEEVES_DECISION_RESPONSE",
         "response": "COMPLEX",
         "classification": "COMPLEX",
         "confidence": 0.85
       },
       {
         "timestamp": "2026-02-09T14:30:26.567890",
         "level": "ESCALATION",
         "type": "LLM_ESCALATION",
         "reason": "COMPLEX",
         "target_llm": "Kimi",
         "full_context": {
           "system": "You are a helpful assistant",
           "messages": [...]
         }
       },
       {
         "timestamp": "2026-02-09T14:30:28.678901",
         "level": "RESPONSE",
         "type": "TARGET_LLM_RESPONSE",
         "target_llm": "Kimi",
         "response": "This code implements...",
         "metadata": {"tokens": 150, "latency_ms": 2500}
       },
       {
         "timestamp": "2026-02-09T14:30:28.789012",
         "level": "SESSION_END",
         "type": "FINAL_RESULT",
         "final_result": "[ESCALATED] Analysis: ...",
         "routing_decision": "ESCALATED"
       }
     ]
   }

Privacy Considerations
----------------------

**By default, logging is DISABLED.**

When you enable logging, the following information is recorded:

- ✅ All user commands/requests
- ✅ LLM prompts and responses
- ✅ System configuration
- ✅ File paths (if in commands)
- ✅ Command outputs (if executed locally)

**Best Practices:**

1. **Only enable when needed** - Use logging temporarily for debugging
2. **Review logs before sharing** - Logs may contain sensitive information
3. **Clear old logs regularly** - Use ``jeeves logging clear``
4. **Keep logs secure** - Log files are stored in your user directory

Configuration
-------------

Logging settings are stored in your config file::

   {
     "logging": {
       "enabled": false,
       "log_dir": null,
       "max_log_files": 100
     }
   }

**Options:**

- ``enabled`` (boolean): Whether logging is active
- ``log_dir`` (string | null): Custom log directory (null = use default)
- ``max_log_files`` (number): Maximum number of log files to keep

Troubleshooting
---------------

"Log files are getting too large"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

::

   # Clear old logs, keeping only recent ones
   jeeves logging clear --keep 5

   # Or disable logging entirely
   jeeves logging off

"Can't find log files"
^^^^^^^^^^^^^^^^^^^^^^

::

   # Check where logs are stored
   jeeves logging status

   # List recent logs with full paths
   jeeves logging list

"Logging not working"
^^^^^^^^^^^^^^^^^^^^^

1. Check that logging is enabled::

      jeeves logging status

2. Try toggling it::

      jeeves logging off
      jeeves logging on

3. Check the log directory permissions::

      ls -la ~/.local/share/jeeves/logs/

API Usage
---------

You can also use the logger programmatically::

   from llm_logger import LLMLogger, get_logger

   # Create logger
   logger = get_logger({"logging": {"enabled": True}})

   # Start a session
   logger.start_session("your command here")

   # Log events
   logger.log_jeeves_decision_prompt(prompt, model, context)
   logger.log_jeeves_decision_response(response, classification, confidence)
   logger.log_escalation(reason, target_llm, full_context)
   logger.log_target_llm_response(target_llm, response)

   # End session
   logger.end_session(final_result, routing_decision)

See ``llm_logger.py`` for full API documentation.
