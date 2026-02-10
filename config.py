#!/usr/bin/env python3
"""
Jeeves Configuration Manager
Handles user preferences, Ollama integration, and model management
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Dict
import requests
import time

# Default configuration
DEFAULT_CONFIG = {
    "ollama": {
        "host": "http://localhost:11434",
        "autostart": True,
        "autostart_with_kimi": True,
    },
    "jeeves": {
        "default_model": "qwen2.5:1.5b",
        "fallback_threshold": 0.7,
        "timeout_seconds": 30,
        "classification_prompt": "simple",  # simple, detailed, or custom
    },
    "routing": {
        "use_pattern_matching": True,
        "use_local_llm": True,
        "auto_fallback": True,
        "cloud_on_uncertainty": True,
    },
    "installed_models": [],
    "last_setup": None,
}

# Suggested Jeeves models with descriptions
SUGGESTED_MODELS = {
    "ultra_fast": [
        {"name": "qwen2.5:0.5b", "size": "400MB", "speed": "Very Fast", "desc": "Minimal resource usage"},
        {"name": "phi3:mini", "size": "2.3GB", "speed": "Fast", "desc": "Good balance, Microsoft"},
    ],
    "balanced": [
        {"name": "qwen2.5:1.5b", "size": "1GB", "speed": "Fast", "desc": "Recommended starter"},
        {"name": "llama3.2:3b", "size": "2GB", "speed": "Fast", "desc": "Meta's latest small model"},
        {"name": "gemma2:2b", "size": "1.6GB", "speed": "Fast", "desc": "Google's efficient model"},
    ],
    "capable": [
        {"name": "qwen2.5:7b", "size": "4.5GB", "speed": "Moderate", "desc": "Better reasoning"},
        {"name": "llama3.2:8b", "size": "4.9GB", "speed": "Moderate", "desc": "Strong performance"},
        {"name": "deepseek-r1:1.5b", "size": "1.1GB", "speed": "Fast", "desc": "Reasoning capabilities"},
    ],
}


class JeevesConfig:
    """Manages Jeeves configuration and Ollama integration"""
    
    CONFIG_DIR = Path.home() / ".config" / "jeeves"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    REMOTE_MODELS_URL = "https://raw.githubusercontent.com/yourusername/jeeves/main/models/suggested_models.json"
    
    def __init__(self):
        self.config = self.load_config()
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> Dict:
        """Load configuration from file or return defaults"""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults for new fields
                    merged = DEFAULT_CONFIG.copy()
                    merged.update(config)
                    return merged
            except Exception as e:
                print(f"⚠️  Error loading config: {e}")
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Error saving config: {e}")
            return False
    
    def is_ollama_installed(self) -> bool:
        """Check if Ollama is installed on the system"""
        try:
            result = subprocess.run(
                ['which', 'ollama'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def is_ollama_running(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(
                f"{self.config['ollama']['host']}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def start_ollama(self) -> bool:
        """Start Ollama server in background"""
        try:
            # Check if already running
            if self.is_ollama_running():
                return True
            
            # Start Ollama
            subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            # Wait for it to be ready
            for i in range(10):
                time.sleep(0.5)
                if self.is_ollama_running():
                    return True
            
            return False
        except Exception as e:
            print(f"❌ Error starting Ollama: {e}")
            return False
    
    def get_installed_models(self) -> List[str]:
        """Get list of models installed in Ollama"""
        try:
            response = requests.get(
                f"{self.config['ollama']['host']}/api/tags",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]
                self.config['installed_models'] = models
                self.save_config()
                return models
        except Exception as e:
            print(f"⚠️  Could not fetch models: {e}")
        return self.config.get('installed_models', [])
    
    def pull_model(self, model_name: str, progress_callback=None) -> bool:
        """Download a model from Ollama registry"""
        try:
            print(f"⬇️  Downloading {model_name}...")
            
            # Stream the pull request to show progress
            response = requests.post(
                f"{self.config['ollama']['host']}/api/pull",
                json={"name": model_name, "stream": True},
                stream=True,
                timeout=300
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to pull model: HTTP {response.status_code}")
                return False
            
            # Process streaming response
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if 'status' in data:
                            if progress_callback:
                                progress_callback(data['status'])
                            elif 'completed' in data and 'total' in data:
                                pct = (data['completed'] / data['total']) * 100
                                print(f"\r  Progress: {pct:.1f}%", end='', flush=True)
            
            print(f"\n✅ Successfully installed {model_name}")
            self.get_installed_models()  # Refresh list
            return True
            
        except Exception as e:
            print(f"\n❌ Error pulling model: {e}")
            return False
    
    def remove_model(self, model_name: str) -> bool:
        """Remove a model from Ollama"""
        try:
            result = subprocess.run(
                ['ollama', 'rm', model_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                print(f"✅ Removed {model_name}")
                self.get_installed_models()  # Refresh list
                return True
            else:
                print(f"❌ Failed to remove: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error removing model: {e}")
            return False
    
    def fetch_remote_suggestions(self) -> Dict:
        """Fetch suggested models from remote git repository"""
        try:
            response = requests.get(self.REMOTE_MODELS_URL, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return {}
    
    def get_all_suggested_models(self) -> Dict:
        """Get combined list of suggested models (built-in + remote)"""
        # Start with built-in suggestions
        all_models = SUGGESTED_MODELS.copy()
        
        # Try to fetch remote suggestions
        remote = self.fetch_remote_suggestions()
        if remote:
            # Merge remote models into categories
            for category, models in remote.items():
                if category in all_models:
                    # Add new models that aren't already in the list
                    existing_names = {m['name'] for m in all_models[category]}
                    for model in models:
                        if model['name'] not in existing_names:
                            all_models[category].append(model)
                else:
                    all_models[category] = models
        
        return all_models


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_model_table(models: List[Dict], installed: List[str]):
    """Print models in a formatted table"""
    print(f"{'Model':<25} {'Size':<10} {'Speed':<12} {'Status':<12} Description")
    print("-" * 80)
    for m in models:
        status = "✅ Installed" if m['name'] in installed else "⬜ Not installed"
        print(f"{m['name']:<25} {m['size']:<10} {m['speed']:<12} {status:<12} {m['desc']}")
    print()


def interactive_setup(config: JeevesConfig):
    """Run interactive setup wizard"""
    print_header("🎩 Jeeves Setup Wizard")
    print("Your intelligent assistant that knows when to ask for help.\n")
    
    # Step 1: Check Ollama installation
    print("📋 Step 1: Checking Ollama installation...")
    
    if not config.is_ollama_installed():
        print("\n❌ Ollama is not installed.")
        print("\nTo install Ollama:")
        print("  macOS/Linux: curl -fsSL https://ollama.com/install.sh | sh")
        print("  Windows: Download from https://ollama.com/download")
        print("\nPlease install Ollama and run setup again.")
        return False
    
    print("✅ Ollama is installed")
    
    # Step 2: Check if Ollama is running
    print("\n📋 Step 2: Checking Ollama server status...")
    
    if config.is_ollama_running():
        print("✅ Ollama server is running")
    else:
        print("⚠️  Ollama server is not running")
        
        start = input("\nWould you like to start Ollama now? [Y/n]: ").strip().lower()
        if start in ('', 'y', 'yes'):
            print("🚀 Starting Ollama server...")
            if config.start_ollama():
                print("✅ Ollama server started successfully")
            else:
                print("❌ Failed to start Ollama server")
                return False
        else:
            print("⚠️  Cannot continue without Ollama running")
            return False
    
    # Step 3: Autostart configuration
    print("\n📋 Step 3: Autostart configuration...")
    
    autostart = input("Should Jeeves automatically start Ollama when needed? [Y/n]: ").strip().lower()
    config.config['ollama']['autostart'] = autostart in ('', 'y', 'yes')
    
    if config.config['ollama']['autostart']:
        kimi_auto = input("Should Ollama also start automatically when Kimi starts? [Y/n]: ").strip().lower()
        config.config['ollama']['autostart_with_kimi'] = kimi_auto in ('', 'y', 'yes')
    
    # Step 4: Model selection
    print_header("🤖 Step 4: Select your Jeeves model")
    print("Jeeves uses a local LLM for fast classification and simple tasks.\n")
    
    # Show suggested models
    installed = config.get_installed_models()
    suggestions = config.get_all_suggested_models()
    
    print("🚀 Ultra Fast (minimal resources):")
    print_model_table(suggestions['ultra_fast'], installed)
    
    print("⚖️  Balanced (recommended):")
    print_model_table(suggestions['balanced'], installed)
    
    print("🧠 More Capable (better reasoning):")
    print_model_table(suggestions['capable'], installed)
    
    # Ask user to select
    while True:
        default_model = config.config['jeeves']['default_model']
        choice = input(f"\nEnter model name to use (default: {default_model}): ").strip()
        
        if not choice:
            choice = default_model
        
        # Check if model is installed
        if choice not in installed:
            download = input(f"  {choice} is not installed. Download now? [Y/n]: ").strip().lower()
            if download in ('', 'y', 'yes'):
                if config.pull_model(choice):
                    config.config['jeeves']['default_model'] = choice
                    break
                else:
                    print("❌ Failed to download model. Please try another.")
            else:
                print("Please select an installed model or choose to download one.")
        else:
            config.config['jeeves']['default_model'] = choice
            print(f"✅ Selected {choice}")
            break
    
    # Step 5: Routing preferences
    print_header("⚙️  Step 5: Routing preferences")
    
    print("Jeeves can route requests in multiple ways:\n")
    print("1. Pattern matching (fastest) - Recognize shell commands instantly")
    print("2. Local LLM classification - Let local model decide complexity")
    print("3. Auto-fallback - Escalate to Kimi if local model is uncertain\n")
    
    use_patterns = input("Enable pattern matching for common commands? [Y/n]: ").strip().lower()
    config.config['routing']['use_pattern_matching'] = use_patterns in ('', 'y', 'yes')
    
    use_classifier = input("Enable local LLM classification? [Y/n]: ").strip().lower()
    config.config['routing']['use_local_llm'] = use_classifier in ('', 'y', 'yes')
    
    auto_fallback = input("Auto-escalate to Kimi when uncertain? [Y/n]: ").strip().lower()
    config.config['routing']['auto_fallback'] = auto_fallback in ('', 'y', 'yes')
    
    # Step 6: Advanced options
    print_header("🔧 Step 6: Advanced options (optional)")
    
    change_timeout = input("Change local LLM timeout? (current: 30s) [y/N]: ").strip().lower()
    if change_timeout in ('y', 'yes'):
        timeout = input("Enter timeout in seconds: ").strip()
        if timeout.isdigit():
            config.config['jeeves']['timeout_seconds'] = int(timeout)
    
    # Save configuration
    config.config['last_setup'] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    if config.save_config():
        print_header("✅ Setup Complete!")
        print(f"Configuration saved to: {config.CONFIG_FILE}")
        print(f"\n🎩 Jeeves is ready to serve!")
        print(f"   Default model: {config.config['jeeves']['default_model']}")
        print(f"   Ollama autostart: {'enabled' if config.config['ollama']['autostart'] else 'disabled'}")
        print(f"   Auto-fallback: {'enabled' if config.config['routing']['auto_fallback'] else 'disabled'}")
        print(f"\n   Run 'jeeves --help' to get started")
        return True
    else:
        print("❌ Failed to save configuration")
        return False


def switch_model(config: JeevesConfig):
    """Interactive model switching"""
    print_header("🔄 Switch Jeeves Model")
    
    installed = config.get_installed_models()
    
    if not installed:
        print("No models installed. Run setup first.")
        return
    
    print("Installed models:")
    for i, model in enumerate(installed, 1):
        current = " (current)" if model == config.config['jeeves']['default_model'] else ""
        print(f"  {i}. {model}{current}")
    
    print("\n  A. Install new model")
    print("  B. Back\n")
    
    choice = input("Select option: ").strip().lower()
    
    if choice == 'a':
        # Show suggested models
        suggestions = config.get_all_suggested_models()
        all_suggestions = []
        for category, models in suggestions.items():
            all_suggestions.extend(models)
        
        print("\nSuggested models:")
        print_model_table(all_suggestions[:10], installed)
        
        model_name = input("Enter model name to install: ").strip()
        if model_name:
            config.pull_model(model_name)
            use_it = input(f"\nUse {model_name} as default? [Y/n]: ").strip().lower()
            if use_it in ('', 'y', 'yes'):
                config.config['jeeves']['default_model'] = model_name
                config.save_config()
                print(f"✅ Switched to {model_name}")
    
    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(installed):
            config.config['jeeves']['default_model'] = installed[idx]
            config.save_config()
            print(f"✅ Switched to {installed[idx]}")


def manage_models(config: JeevesConfig):
    """Model management menu"""
    while True:
        print_header("📦 Model Management")
        
        installed = config.get_installed_models()
        print(f"Installed models: {len(installed)}")
        for model in installed:
            current = " ★" if model == config.config['jeeves']['default_model'] else ""
            print(f"  • {model}{current}")
        
        print("\nOptions:")
        print("  1. Install model")
        print("  2. Remove model")
        print("  3. Set default model")
        print("  4. Update model list from remote")
        print("  5. Back to main menu")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '1':
            model_name = input("Enter model name to install (e.g., llama3.2:3b): ").strip()
            if model_name:
                config.pull_model(model_name)
        
        elif choice == '2':
            model_name = input("Enter model name to remove: ").strip()
            if model_name:
                config.remove_model(model_name)
        
        elif choice == '3':
            switch_model(config)
        
        elif choice == '4':
            print("Fetching remote suggestions...")
            remote = config.fetch_remote_suggestions()
            if remote:
                print(f"✅ Found {sum(len(v) for v in remote.values())} new suggestions")
            else:
                print("⚠️  Could not fetch remote suggestions")
        
        elif choice == '5':
            break


def main():
    """Main entry point for configuration"""
    config = JeevesConfig()
    
    if len(sys.argv) < 2:
        print("Usage: jeeves-config [setup|switch-model|manage-models|status]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "setup":
        interactive_setup(config)
    
    elif command == "switch-model":
        switch_model(config)
    
    elif command == "manage-models":
        manage_models(config)
    
    elif command == "status":
        print_header("🎩 Jeeves Status")
        print(f"Config file: {config.CONFIG_FILE}")
        print(f"Ollama installed: {'✅' if config.is_ollama_installed() else '❌'}")
        print(f"Ollama running: {'✅' if config.is_ollama_running() else '❌'}")
        print(f"Default model: {config.config['jeeves']['default_model']}")
        print(f"Installed models: {len(config.get_installed_models())}")
        print(f"Last setup: {config.config.get('last_setup', 'Never')}")
    
    else:
        print(f"Unknown command: {command}")
        print("Available: setup, switch-model, manage-models, status")


if __name__ == "__main__":
    main()
