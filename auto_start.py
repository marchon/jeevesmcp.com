#!/usr/bin/env python3
"""
Jeeves Auto-Start Module

Handles automatic initialization on first run:
- Enable logging by default
- Connect to existing Ollama/Kimi instances (don't restart if running)
- Start WebSocket server if not running
- Configure default model if needed

Usage:
    from auto_start import ensure_initialized
    ensure_initialized()  # Call at startup
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import JeevesConfig

# Auto-start configuration
AUTO_START_MARKER = Path.home() / ".local/share/jeeves/.auto_start_complete"
PID_FILE = Path.home() / ".local/share/jeeves/jeeves-server.pid"
OLLAMA_API_URL = "http://localhost:11434"


def is_ollama_running() -> bool:
    """Check if Ollama is already running"""
    try:
        import urllib.request
        req = urllib.request.Request(
            f"{OLLAMA_API_URL}/api/tags",
            method='GET',
            headers={'Accept': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.status == 200
    except:
        return False


def is_server_running() -> bool:
    """Check if Jeeves WebSocket server is running"""
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)  # Check if process exists
        return True
    except:
        # Stale PID file
        PID_FILE.unlink(missing_ok=True)
        return False


def get_running_ollama_instances() -> list:
    """Get list of running Ollama processes"""
    try:
        result = subprocess.run(
            ["pgrep", "-a", "ollama"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            return [line for line in lines if line]
    except:
        pass
    return []


def ensure_logging_enabled(config: JeevesConfig) -> bool:
    """Ensure logging is enabled in config"""
    try:
        if not config.config.get('logging', {}).get('enabled', False):
            print("📋 Auto-start: Enabling logging...")
            config.config['logging']['enabled'] = True
            config.save_config()
            print("✅ Logging enabled")
        return True
    except Exception as e:
        print(f"⚠️  Could not enable logging: {e}")
        return False


def ensure_ollama_running() -> bool:
    """
    Ensure Ollama is running.
    If already running, just connect. If not, start it.
    """
    # Check if already running
    if is_ollama_running():
        print("✅ Ollama is already running")
        running_instances = get_running_ollama_instances()
        if len(running_instances) > 1:
            print(f"   Found {len(running_instances)} Ollama processes (using existing)")
        return True
    
    # Check if Ollama is installed
    try:
        result = subprocess.run(
            ["which", "ollama"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("⚠️  Ollama not installed. Run: jeeves setup")
            return False
    except:
        return False
    
    # Start Ollama in background
    print("🚀 Starting Ollama...")
    try:
        # Start ollama serve in background
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # Wait for it to be ready
        for i in range(10):
            time.sleep(0.5)
            if is_ollama_running():
                print("✅ Ollama started successfully")
                return True
        
        print("⚠️  Ollama starting... (may take a moment)")
        return True
    except Exception as e:
        print(f"❌ Failed to start Ollama: {e}")
        return False


def ensure_server_running(prefer_upstream: bool = False) -> bool:
    """
    Ensure WebSocket server is running.
    If already running, connect to it. If not, start it.
    """
    if is_server_running():
        print("✅ Jeeves WebSocket server is already running")
        return True
    
    print("🚀 Starting Jeeves WebSocket server...")
    try:
        server_script = Path(__file__).parent / "server.py"
        
        # Check if we should enable upstream
        upstream_enabled = prefer_upstream and (
            os.environ.get('KIMI_API_KEY') or
            os.environ.get('MOONSHOT_API_KEY') or
            os.environ.get('CLAUDE_API_KEY') or
            os.environ.get('ANTHROPIC_API_KEY') or
            os.environ.get('OPENAI_API_KEY')
        )
        
        cmd = [sys.executable, str(server_script), "start"]
        if upstream_enabled:
            cmd.append("--upstream")
            print("   (with upstream LLM pools enabled)")
        
        # Start server in background
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        # Wait for it to start
        for i in range(10):
            time.sleep(0.3)
            if is_server_running():
                print("✅ Jeeves server started successfully")
                return True
        
        print("⏳ Server starting...")
        return True
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False


def ensure_default_model(config: JeevesConfig) -> bool:
    """Ensure a default model is configured and available"""
    default_model = config.config.get('jeeves', {}).get('default_model', 'qwen2.5:1.5b')
    
    # Check if model is installed
    try:
        import urllib.request
        req = urllib.request.Request(
            f"{OLLAMA_API_URL}/api/tags",
            method='GET',
            headers={'Accept': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            models = [m['name'] for m in data.get('models', [])]
            
            if default_model in models:
                print(f"✅ Default model ready: {default_model}")
                return True
            else:
                print(f"📦 Default model not found: {default_model}")
                print(f"   Install with: ollama pull {default_model}")
                return False
    except Exception as e:
        print(f"⚠️  Could not check models: {e}")
        return False


def ensure_initialized(
    enable_logging: bool = True,
    start_server: bool = True,
    prefer_upstream: bool = False,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Ensure Jeeves is fully initialized.
    
    This function handles automatic startup:
    - Enables logging if requested
    - Connects to existing Ollama or starts it
    - Starts WebSocket server if requested
    - Checks default model availability
    
    Args:
        enable_logging: Enable logging by default
        start_server: Start WebSocket server
        prefer_upstream: Enable upstream LLM pools if API keys available
        verbose: Print status messages
        
    Returns:
        Dict with initialization status
    """
    if not verbose:
        # Suppress output
        old_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
    
    try:
        print("🎩 Jeeves Auto-Start")
        print("-" * 40)
        
        config = JeevesConfig()
        results = {
            'logging_enabled': False,
            'ollama_running': False,
            'server_running': False,
            'model_ready': False,
            'upstream_available': False
        }
        
        # 1. Enable logging
        if enable_logging:
            results['logging_enabled'] = ensure_logging_enabled(config)
        
        # 2. Ensure Ollama is running (connect to existing if multiple)
        results['ollama_running'] = ensure_ollama_running()
        
        # 3. Start WebSocket server if requested
        if start_server:
            results['server_running'] = ensure_server_running(prefer_upstream)
        
        # 4. Check default model
        if results['ollama_running']:
            results['model_ready'] = ensure_default_model(config)
        
        # 5. Check upstream availability
        results['upstream_available'] = prefer_upstream and (
            os.environ.get('KIMI_API_KEY') or
            os.environ.get('MOONSHOT_API_KEY') or
            os.environ.get('CLAUDE_API_KEY') or
            os.environ.get('ANTHROPIC_API_KEY') or
            os.environ.get('OPENAI_API_KEY')
        )
        
        # Mark auto-start as complete
        AUTO_START_MARKER.parent.mkdir(parents=True, exist_ok=True)
        AUTO_START_MARKER.touch()
        
        print("-" * 40)
        print("✅ Jeeves initialization complete")
        print()
        
        return results
        
    finally:
        if not verbose:
            sys.stdout.close()
            sys.stdout = old_stdout


def is_initialized() -> bool:
    """Check if auto-initialization has been run"""
    return AUTO_START_MARKER.exists()


def reset_initialization():
    """Reset initialization marker (for testing)"""
    AUTO_START_MARKER.unlink(missing_ok=True)
    print("🔄 Initialization marker reset")


# Auto-run on import if JEEVES_AUTO_START env var is set
if os.environ.get('JEEVES_AUTO_START', '').lower() in ('1', 'true', 'yes'):
    ensure_initialized()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Jeeves Auto-Start")
    parser.add_argument('--no-logging', action='store_true', help='Skip enabling logging')
    parser.add_argument('--no-server', action='store_true', help='Skip starting WebSocket server')
    parser.add_argument('--upstream', action='store_true', help='Enable upstream LLM pools')
    parser.add_argument('--reset', action='store_true', help='Reset initialization marker')
    
    args = parser.parse_args()
    
    if args.reset:
        reset_initialization()
    else:
        ensure_initialized(
            enable_logging=not args.no_logging,
            start_server=not args.no_server,
            prefer_upstream=args.upstream,
            verbose=True
        )
