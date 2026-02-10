#!/usr/bin/env python3
"""
LLM Interaction Logger for Jeeves

Logs all interactions between user, Jeeves router, and LLMs for debugging
and verification purposes. Log files use timestamp-based naming.

Log Format: LLM-LOG-MM:DD:YY:mm:ss:ms.log
Location: ~/.local/share/jeeves/logs/ (Linux/macOS) or %LOCALAPPDATA%/jeeves/logs/ (Windows)
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum


class LogLevel(Enum):
    """Log levels for LLM interactions"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    DECISION = "DECISION"
    ESCALATION = "ESCALATION"
    RESPONSE = "RESPONSE"
    ERROR = "ERROR"


class LLMLogger:
    """
    Logger for LLM interactions with timestamp-based file naming.
    
    Each interaction creates a new log file with format: LLM-LOG-MM:DD:YY:mm:ss:ms.log
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LLM logger.
        
        Args:
            config: Configuration dictionary with 'logging_enabled' key
        """
        self.config = config or {}
        self.enabled = self.config.get('logging', {}).get('enabled', False)
        self.log_dir = self._get_log_dir()
        self.current_log_file: Optional[Path] = None
        self._ensure_log_dir()
    
    def _get_log_dir(self) -> Path:
        """Get platform-appropriate log directory"""
        # Try to use platform_utils if available
        try:
            from platform_utils import PlatformInfo
            info = PlatformInfo()
            if info.os.value == 'windows':
                base = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local'))
                return base / 'jeeves' / 'logs'
            elif info.os.value == 'macos':
                return Path.home() / 'Library/Logs/jeeves'
            else:
                return Path.home() / '.local/share/jeeves/logs'
        except ImportError:
            # Fallback
            return Path.home() / '.local/share/jeeves/logs'
    
    def _ensure_log_dir(self):
        """Create log directory if it doesn't exist"""
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_log_filename(self) -> str:
        """
        Generate log filename with timestamp format: LLM-LOG-MM:DD:YY:mm:ss:ms.log
        
        Returns:
            Filename string in format LLM-LOG-MM:DD:YY:mm:ss:ms.log
        """
        now = datetime.now()
        # Format: MM:DD:YY:mm:ss:ms
        timestamp = now.strftime("%m:%d:%y:%H:%M:%S:") + f"{now.microsecond // 1000:03d}"
        return f"LLM-LOG-{timestamp}.log"
    
    def _get_log_file_path(self) -> Path:
        """Get path for new log file"""
        filename = self._generate_log_filename()
        return self.log_dir / filename
    
    def start_session(self, user_command: str) -> Optional[Path]:
        """
        Start a new logging session for a user command.
        
        Args:
            user_command: The original user input/command
            
        Returns:
            Path to log file if logging enabled, None otherwise
        """
        if not self.enabled:
            return None
        
        self.current_log_file = self._get_log_file_path()
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "SESSION_START",
            "user_command": user_command,
            "events": []
        }
        
        self._write_log(log_entry)
        return self.current_log_file
    
    def log_system_context(self, context: Dict[str, Any]):
        """
        Log system context information.
        
        Args:
            context: Dictionary containing system state, config, etc.
        """
        if not self.enabled or not self.current_log_file:
            return
        
        self._append_event({
            "timestamp": datetime.now().isoformat(),
            "level": LogLevel.INFO.value,
            "type": "SYSTEM_CONTEXT",
            "data": context
        })
    
    def log_jeeves_decision_prompt(self, prompt: str, model: str, context: Dict[str, Any]):
        """
        Log the decision prompt sent to Jeeves' local LLM.
        
        Args:
            prompt: The full prompt sent to the LLM
            model: The model name being used
            context: Additional context (temperature, max_tokens, etc.)
        """
        if not self.enabled or not self.current_log_file:
            return
        
        self._append_event({
            "timestamp": datetime.now().isoformat(),
            "level": LogLevel.DECISION.value,
            "type": "JEEVES_DECISION_PROMPT",
            "model": model,
            "prompt": prompt,
            "context": context
        })
    
    def log_jeeves_decision_response(self, response: str, classification: str, confidence: Optional[float] = None):
        """
        Log the response from Jeeves' local LLM.
        
        Args:
            response: Raw response from LLM
            classification: Parsed classification (SIMPLE/MODERATE/COMPLEX/UNCERTAIN)
            confidence: Confidence score if available
        """
        if not self.enabled or not self.current_log_file:
            return
        
        self._append_event({
            "timestamp": datetime.now().isoformat(),
            "level": LogLevel.DECISION.value,
            "type": "JEEVES_DECISION_RESPONSE",
            "response": response,
            "classification": classification,
            "confidence": confidence
        })
    
    def log_escalation(self, reason: str, target_llm: str, full_context: Dict[str, Any]):
        """
        Log escalation to another LLM (cloud AI).
        
        Args:
            reason: Why escalation occurred (COMPLEX/UNCERTAIN/ERROR)
            target_llm: Name of target LLM (e.g., "Kimi", "Claude", "GPT-4")
            full_context: Complete context being sent to target LLM
        """
        if not self.enabled or not self.current_log_file:
            return
        
        self._append_event({
            "timestamp": datetime.now().isoformat(),
            "level": LogLevel.ESCALATION.value,
            "type": "LLM_ESCALATION",
            "reason": reason,
            "target_llm": target_llm,
            "full_context": full_context
        })
    
    def log_target_llm_response(self, target_llm: str, response: str, metadata: Optional[Dict] = None):
        """
        Log the response received from the target (escalated) LLM.
        
        Args:
            target_llm: Name of the LLM that responded
            response: Full response from the LLM
            metadata: Additional metadata (tokens used, latency, etc.)
        """
        if not self.enabled or not self.current_log_file:
            return
        
        self._append_event({
            "timestamp": datetime.now().isoformat(),
            "level": LogLevel.RESPONSE.value,
            "type": "TARGET_LLM_RESPONSE",
            "target_llm": target_llm,
            "response": response,
            "metadata": metadata or {}
        })
    
    def log_local_execution(self, command: str, result: str, execution_time_ms: float):
        """
        Log local command execution (shell commands, file operations).
        
        Args:
            command: The command that was executed
            result: Result/output of the command
            execution_time_ms: Execution time in milliseconds
        """
        if not self.enabled or not self.current_log_file:
            return
        
        self._append_event({
            "timestamp": datetime.now().isoformat(),
            "level": LogLevel.INFO.value,
            "type": "LOCAL_EXECUTION",
            "command": command,
            "result": result,
            "execution_time_ms": execution_time_ms
        })
    
    def log_error(self, error_type: str, error_message: str, traceback: Optional[str] = None):
        """
        Log an error that occurred during processing.
        
        Args:
            error_type: Type of error (ROUTING_ERROR/LLM_ERROR/EXECUTION_ERROR)
            error_message: Error message
            traceback: Full traceback if available
        """
        if not self.enabled or not self.current_log_file:
            return
        
        self._append_event({
            "timestamp": datetime.now().isoformat(),
            "level": LogLevel.ERROR.value,
            "type": "ERROR",
            "error_type": error_type,
            "error_message": error_message,
            "traceback": traceback
        })
    
    def end_session(self, final_result: str, routing_decision: str):
        """
        End the logging session with final result summary.
        
        Args:
            final_result: The final result returned to user
            routing_decision: LOCAL/ESCALATED/ERROR
        """
        if not self.enabled or not self.current_log_file:
            return
        
        self._append_event({
            "timestamp": datetime.now().isoformat(),
            "level": "SESSION_END",
            "type": "FINAL_RESULT",
            "final_result": final_result,
            "routing_decision": routing_decision
        })
        
        self.current_log_file = None
    
    def _write_log(self, data: Dict):
        """Write initial log data to file"""
        if self.current_log_file:
            with open(self.current_log_file, 'w') as f:
                json.dump(data, f, indent=2)
    
    def _append_event(self, event: Dict):
        """Append an event to the current log file"""
        if not self.current_log_file or not self.current_log_file.exists():
            return
        
        try:
            with open(self.current_log_file, 'r') as f:
                log_data = json.load(f)
            
            if "events" not in log_data:
                log_data["events"] = []
            
            log_data["events"].append(event)
            
            with open(self.current_log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error writing to log: {e}")
    
    def enable_logging(self):
        """Enable logging"""
        self.enabled = True
        if self.config.get('logging') is None:
            self.config['logging'] = {}
        self.config['logging']['enabled'] = True
        print("✅ LLM interaction logging enabled")
        print(f"   Logs will be saved to: {self.log_dir}")
    
    def disable_logging(self):
        """Disable logging"""
        self.enabled = False
        if self.config.get('logging') is None:
            self.config['logging'] = {}
        self.config['logging']['enabled'] = False
        print("🛑 LLM interaction logging disabled")
    
    def get_log_status(self) -> Dict[str, Any]:
        """Get current logging status"""
        return {
            "enabled": self.enabled,
            "log_directory": str(self.log_dir),
            "log_count": len(list(self.log_dir.glob("LLM-LOG-*.log"))) if self.log_dir.exists() else 0,
            "current_session": str(self.current_log_file) if self.current_log_file else None
        }
    
    def list_logs(self, limit: int = 20) -> list:
        """
        List available log files.
        
        Args:
            limit: Maximum number of logs to return (most recent first)
            
        Returns:
            List of log file paths
        """
        if not self.log_dir.exists():
            return []
        
        logs = sorted(
            self.log_dir.glob("LLM-LOG-*.log"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        return [str(log) for log in logs[:limit]]
    
    def read_log(self, log_filename: str) -> Optional[Dict]:
        """
        Read a specific log file.
        
        Args:
            log_filename: Name of log file (e.g., "LLM-LOG-02:09:26:14:30:25:123.log")
            
        Returns:
            Log data as dictionary or None if not found
        """
        log_path = self.log_dir / log_filename
        if not log_path.exists():
            return None
        
        try:
            with open(log_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error reading log: {e}")
            return None
    
    def clear_logs(self, keep_recent: int = 10) -> int:
        """
        Clear old log files, keeping most recent ones.
        
        Args:
            keep_recent: Number of recent logs to keep
            
        Returns:
            Number of files deleted
        """
        if not self.log_dir.exists():
            return 0
        
        logs = sorted(
            self.log_dir.glob("LLM-LOG-*.log"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        deleted = 0
        for log in logs[keep_recent:]:
            try:
                log.unlink()
                deleted += 1
            except Exception:
                pass
        
        return deleted


# Singleton instance
_logger_instance: Optional[LLMLogger] = None


def get_logger(config: Optional[Dict] = None) -> LLMLogger:
    """Get or create singleton logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = LLMLogger(config)
    return _logger_instance


def reset_logger():
    """Reset logger instance (useful for testing)"""
    global _logger_instance
    _logger_instance = None


if __name__ == "__main__":
    # Demo/test
    print("=== LLM Logger Demo ===\n")
    
    # Create logger with logging enabled
    logger = LLMLogger({"logging": {"enabled": True}})
    
    # Simulate a session
    logger.start_session("analyze this Python code")
    
    logger.log_system_context({
        "jeeves_version": "0.1.0",
        "default_model": "qwen2.5:1.5b",
        "pattern_matching": True
    })
    
    logger.log_jeeves_decision_prompt(
        prompt="Classify this request: 'analyze this Python code'",
        model="qwen2.5:1.5b",
        context={"temperature": 0.7, "max_tokens": 100}
    )
    
    logger.log_jeeves_decision_response(
        response="COMPLEX",
        classification="COMPLEX",
        confidence=0.85
    )
    
    logger.log_escalation(
        reason="COMPLEX",
        target_llm="Kimi",
        full_context={
            "system": "You are a helpful assistant",
            "messages": [{"role": "user", "content": "analyze this Python code"}]
        }
    )
    
    logger.log_target_llm_response(
        target_llm="Kimi",
        response="This code implements a sorting algorithm...",
        metadata={"tokens": 150, "latency_ms": 2500}
    )
    
    logger.end_session(
        final_result="[ESCALATED] Analysis: This code implements...",
        routing_decision="ESCALATED"
    )
    
    print("\n=== Log Status ===")
    status = logger.get_log_status()
    print(f"Enabled: {status['enabled']}")
    print(f"Log directory: {status['log_directory']}")
    print(f"Total logs: {status['log_count']}")
    
    print("\n=== Recent Logs ===")
    for log in logger.list_logs(limit=5):
        print(f"  - {Path(log).name}")
