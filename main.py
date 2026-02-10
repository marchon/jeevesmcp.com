#!/usr/bin/env python3
"""
Jeeves CLI - Main entry point
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from router import JeevesRouter
from config import JeevesConfig, interactive_setup, switch_model, manage_models


def print_banner():
    print("""
    🎩 Jeeves v0.1.0
    Your intelligent assistant that knows when to ask for help
    """)


def cmd_setup(args):
    """Run setup wizard"""
    config = JeevesConfig()
    interactive_setup(config)


def cmd_status(args):
    """Show Jeeves status"""
    config = JeevesConfig()
    
    print("\n" + "="*50)
    print("  🎩 Jeeves Status")
    print("="*50 + "\n")
    
    print(f"Config file:       {config.CONFIG_FILE}")
    print(f"Ollama installed:  {'✅ Yes' if config.is_ollama_installed() else '❌ No'}")
    print(f"Ollama running:    {'✅ Yes' if config.is_ollama_running() else '❌ No'}")
    print(f"Default model:     {config.config['jeeves']['default_model']}")
    print(f"Installed models:  {len(config.get_installed_models())}")
    print(f"Last setup:        {config.config.get('last_setup', 'Never')}")
    print(f"\nRouting settings:")
    print(f"  Pattern matching:   {'✅ On' if config.config['routing']['use_pattern_matching'] else '❌ Off'}")
    print(f"  Local LLM:          {'✅ On' if config.config['routing']['use_local_llm'] else '❌ Off'}")
    print(f"  Auto-fallback:      {'✅ On' if config.config['routing']['auto_fallback'] else '❌ Off'}")
    print()


def cmd_models(args):
    """Manage models"""
    config = JeevesConfig()
    manage_models(config)


def cmd_switch(args):
    """Switch default model"""
    config = JeevesConfig()
    switch_model(config)


def cmd_route(args):
    """Route a single request"""
    if not args.request:
        print("Error: No request provided")
        sys.exit(1)
    
    request = ' '.join(args.request)
    
    try:
        router = JeevesRouter()
        result = router.route(request)
        
        print(f"\nRouting: {result['destination']} ({result['method']})")
        
        if result['should_escalate']:
            print("\n☁️  Request would be sent to Kimi (cloud)")
        else:
            print("\n🤖 Local response:")
            print("-" * 50)
            print(result.get('result', 'No result'))
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_interactive(args):
    """Interactive mode"""
    try:
        router = JeevesRouter()
        print_banner()
        print("Interactive Mode - Type 'exit' or 'quit' to exit\n")
        
        while True:
            try:
                request = input("You: ").strip()
                if request.lower() in ('exit', 'quit'):
                    break
                if not request:
                    continue
                
                result = router.route(request)
                
                if result['should_escalate']:
                    print(f"🤖 Jeeves → ☁️  Kimi ({result['method']})")
                    print("   [Would be sent to Kimi for processing]")
                else:
                    print(f"🤖 Jeeves ({result['method']})")
                    print(f"\n{result.get('result', 'No result')}")
                
                print()
                
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
                
    except Exception as e:
        print(f"Failed to initialize Jeeves: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="🎩 Jeeves - Intelligent Local/Cloud Router",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  jeeves setup                    # Run initial setup
  jeeves status                   # Check Jeeves status
  jeeves models                   # Manage installed models
  jeeves switch                   # Switch default model
  jeeves route "ls -la"          # Route a single request
  jeeves interactive              # Start interactive mode
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup
    setup_parser = subparsers.add_parser('setup', help='Run setup wizard')
    setup_parser.set_defaults(func=cmd_setup)
    
    # Status
    status_parser = subparsers.add_parser('status', help='Show Jeeves status')
    status_parser.set_defaults(func=cmd_status)
    
    # Models
    models_parser = subparsers.add_parser('models', help='Manage models')
    models_parser.set_defaults(func=cmd_models)
    
    # Switch
    switch_parser = subparsers.add_parser('switch', help='Switch default model')
    switch_parser.set_defaults(func=cmd_switch)
    
    # Route
    route_parser = subparsers.add_parser('route', help='Route a request')
    route_parser.add_argument('request', nargs='+', help='The request to route')
    route_parser.set_defaults(func=cmd_route)
    
    # Interactive
    interactive_parser = subparsers.add_parser('interactive', help='Interactive mode')
    interactive_parser.set_defaults(func=cmd_interactive)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    args.func(args)


if __name__ == "__main__":
    main()
