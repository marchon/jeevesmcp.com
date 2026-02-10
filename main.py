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

# Try to import logger
try:
    from llm_logger import LLMLogger, get_logger
    HAS_LOGGER = True
except ImportError:
    HAS_LOGGER = False


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
    
    # Platform info if available
    try:
        from platform_utils import PlatformInfo
        platform_info = PlatformInfo()
        print(f"Platform:          {platform_info.get_os_display_name()}")
        print(f"Shell:             {platform_info.shell.value}")
        print(f"Terminal:          {platform_info.terminal.value}")
        print()
    except ImportError:
        pass
    
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
    
    # Logging status
    logging_enabled = config.config.get('logging', {}).get('enabled', False)
    print(f"\nLogging settings:")
    print(f"  LLM interaction logging: {'✅ On' if logging_enabled else '❌ Off'}")
    
    if HAS_LOGGER and logging_enabled:
        logger = get_logger(config.config)
        status = logger.get_log_status()
        print(f"  Log directory:     {status['log_directory']}")
        print(f"  Log files:         {status['log_count']}")
    
    print()


def cmd_list(args):
    """List everything - quick overview of Jeeves state"""
    config = JeevesConfig()
    
    print("\n" + "="*60)
    print("  🎩 Jeeves Overview")
    print("="*60)
    
    # Platform
    try:
        from platform_utils import PlatformInfo
        platform_info = PlatformInfo()
        print(f"\n💻 Platform: {platform_info.get_os_display_name()}")
        print(f"   Shell: {platform_info.shell.value}")
    except ImportError:
        pass
    
    # Ollama Status
    print(f"\n🤖 Ollama:")
    print(f"   Installed: {'✅' if config.is_ollama_installed() else '❌'}")
    print(f"   Running:   {'✅' if config.is_ollama_running() else '❌'}")
    
    # Models
    installed = config.get_installed_models()
    print(f"\n📦 Models ({len(installed)} installed):")
    default = config.config['jeeves']['default_model']
    for model in installed[:5]:  # Show first 5
        marker = "⭐" if model == default else "  "
        print(f"   {marker} {model}")
    if len(installed) > 5:
        print(f"   ... and {len(installed) - 5} more")
    
    # Settings
    print(f"\n⚙️  Settings:")
    print(f"   Pattern matching: {'✅' if config.config['routing']['use_pattern_matching'] else '❌'}")
    print(f"   Local LLM:        {'✅' if config.config['routing']['use_local_llm'] else '❌'}")
    print(f"   Auto-fallback:    {'✅' if config.config['routing']['auto_fallback'] else '❌'}")
    
    # Logging
    if HAS_LOGGER:
        logging_enabled = config.config.get('logging', {}).get('enabled', False)
        print(f"   Logging:          {'✅' if logging_enabled else '❌'}")
    
    # Quick actions
    print("\n🚀 Quick Actions:")
    print("   jeeves interactive     Start chatting")
    print("   jeeves models          Manage models")
    print("   jeeves status          Detailed status")
    print("   jeeves --help          All commands")
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
            print("\n☁️  Request would be sent to primary AI (cloud)")
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
        print("Interactive Mode - Type 'exit' or 'quit' to exit")
        print("Type '/logging on' or '/logging off' to toggle logging\n")
        
        while True:
            try:
                request = input("You: ").strip()
                
                # Handle special commands
                if request.lower() in ('exit', 'quit'):
                    break
                if not request:
                    continue
                
                # Handle logging toggle in interactive mode
                if request.lower() == '/logging on':
                    if HAS_LOGGER:
                        logger = get_logger(router.config.config)
                        logger.enable_logging()
                        router.config.config['logging']['enabled'] = True
                        router.config.save_config()
                        router.logger = logger
                    else:
                        print("❌ Logging module not available")
                    continue
                
                if request.lower() == '/logging off':
                    if HAS_LOGGER:
                        logger = get_logger(router.config.config)
                        logger.disable_logging()
                        router.config.config['logging']['enabled'] = False
                        router.config.save_config()
                        router.logger = None
                    else:
                        print("❌ Logging module not available")
                    continue
                
                result = router.route(request)
                
                if result['should_escalate']:
                    print(f"🤖 Jeeves → ☁️  Primary AI ({result['method']})")
                    print("   [Request escalated to primary AI for processing]")
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


def cmd_logging(args):
    """Control LLM interaction logging"""
    if not HAS_LOGGER:
        print("❌ Logging module not available")
        sys.exit(1)
    
    config = JeevesConfig()
    logger = get_logger(config.config)
    
    if args.logging_command == 'on':
        logger.enable_logging()
        config.config['logging']['enabled'] = True
        config.save_config()
        print("\n💡 Tip: Each request will now be logged to:")
        print(f"   {logger.log_dir}")
        print("\n   Log format: LLM-LOG-MM:DD:YY:mm:ss:ms.log")
        print("   Contains: User command → System context → LLM prompts → Responses")
        
    elif args.logging_command == 'off':
        logger.disable_logging()
        config.config['logging']['enabled'] = False
        config.save_config()
        
    elif args.logging_command == 'status':
        status = logger.get_log_status()
        print("\n" + "="*50)
        print("  📝 LLM Logging Status")
        print("="*50 + "\n")
        print(f"Enabled:          {'✅ Yes' if status['enabled'] else '❌ No'}")
        print(f"Log directory:    {status['log_directory']}")
        print(f"Total log files:  {status['log_count']}")
        if status['current_session']:
            print(f"Current session:  {status['current_session']}")
        print()
        
    elif args.logging_command == 'list':
        logs = logger.list_logs(limit=args.limit)
        print(f"\n📁 Recent log files (showing {min(len(logs), args.limit)} of {logger.get_log_status()['log_count']}):")
        print("-" * 60)
        for i, log_path in enumerate(logs, 1):
            log_name = Path(log_path).name
            size = Path(log_path).stat().st_size
            print(f"{i:2}. {log_name} ({size:,} bytes)")
        print()
        
    elif args.logging_command == 'view':
        if not args.log_file:
            print("❌ Error: Please specify a log file with --file")
            sys.exit(1)
        
        log_data = logger.read_log(args.log_file)
        if log_data:
            print("\n" + "="*60)
            print(f"  📄 Log: {args.log_file}")
            print("="*60 + "\n")
            print(json.dumps(log_data, indent=2))
            print()
        else:
            print(f"❌ Log file not found: {args.log_file}")
            sys.exit(1)
            
    elif args.logging_command == 'clear':
        deleted = logger.clear_logs(keep_recent=args.keep)
        print(f"\n🗑️  Cleared {deleted} old log files")
        print(f"   Kept {args.keep} most recent logs")
        remaining = logger.get_log_status()['log_count']
        print(f"   {remaining} log files remaining")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="🎩 Jeeves - Intelligent Local/Cloud Router",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  jeeves setup                    # Run initial setup
  jeeves list                     # Quick overview (models, status)
  jeeves status                   # Detailed Jeeves status
  jeeves models                   # Manage installed models
  jeeves switch                   # Switch default model
  jeeves route "ls -la"          # Route a single request
  jeeves interactive              # Start interactive mode
  jeeves logging on               # Enable LLM interaction logging
  jeeves logging off              # Disable LLM interaction logging
  jeeves logging status           # Show logging status
  jeeves logging list             # List recent log files
  jeeves logging view --file FILE # View a specific log
  jeeves logging clear            # Clear old logs (keep 10 recent)
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup
    setup_parser = subparsers.add_parser('setup', help='Run setup wizard')
    setup_parser.set_defaults(func=cmd_setup)
    
    # Status
    status_parser = subparsers.add_parser('status', help='Show Jeeves status')
    status_parser.set_defaults(func=cmd_status)
    
    # List
    list_parser = subparsers.add_parser('list', help='List Jeeves overview')
    list_parser.set_defaults(func=cmd_list)
    
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
    
    # Logging
    logging_parser = subparsers.add_parser('logging', help='Control LLM interaction logging')
    logging_parser.add_argument(
        'logging_command',
        choices=['on', 'off', 'status', 'list', 'view', 'clear'],
        help='Logging command'
    )
    logging_parser.add_argument('--limit', type=int, default=20, help='Number of logs to list (default: 20)')
    logging_parser.add_argument('--file', dest='log_file', help='Log file to view')
    logging_parser.add_argument('--keep', type=int, default=10, help='Number of recent logs to keep when clearing')
    logging_parser.set_defaults(func=cmd_logging)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    args.func(args)


if __name__ == "__main__":
    main()
