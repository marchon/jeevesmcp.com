#!/usr/bin/env python3
"""
Jeeves CLI - Main entry point
Supports both direct mode and WebSocket server mode for rapid responses
"""

import sys
import argparse
import json
import asyncio
import time
import os
from pathlib import Path
from typing import Optional, Dict, Any

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

# Try to import WebSocket client
try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False

# Try to import auto-start
try:
    from auto_start import ensure_initialized, is_initialized
    HAS_AUTO_START = True
except ImportError:
    HAS_AUTO_START = False

# Server settings
DEFAULT_WS_HOST = "127.0.0.1"
DEFAULT_WS_PORT = 18473
PID_FILE = Path.home() / ".local/share/jeeves/jeeves-server.pid"

# Auto-start on first use (unless disabled)
if HAS_AUTO_START and not is_initialized() and not os.environ.get('JEEVES_NO_AUTO_START'):
    # Run auto-start silently for most commands
    import sys
    if len(sys.argv) <= 1 or sys.argv[1] not in ('--help', '-h', 'version'):
        ensure_initialized(verbose=False)


async def try_websocket_request(request: str, host: str = DEFAULT_WS_HOST, port: int = DEFAULT_WS_PORT) -> Optional[Dict[str, Any]]:
    """Try to send request via WebSocket, return None if server not available"""
    if not HAS_WEBSOCKETS:
        return None
        
    uri = f"ws://{host}:{port}"
    try:
        async with websockets.connect(uri, close_timeout=0.5) as websocket:
            await websocket.send(json.dumps({'request': request}))
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            return json.loads(response)
    except (ConnectionRefusedError, asyncio.TimeoutError, OSError):
        return None
    except Exception:
        return None


def format_response(result: Dict[str, Any]) -> str:
    """Format response with log file indicator"""
    log_file = result.get('log_file')
    log_suffix = f" | 📝 {Path(log_file).name}" if log_file else ""
    
    if result.get('should_escalate'):
        return f"\n☁️  UPSTREAM → Primary AI{log_suffix}"
    else:
        result_text = result.get('result', 'No result')
        return f"{result_text}\n\n✅ LOCAL → Jeeves{log_suffix}"


def is_server_running() -> bool:
    """Check if WebSocket server is running"""
    if not PID_FILE.exists():
        return False
    try:
        import os
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)
        return True
    except:
        return False


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
    """Route a single request - tries WebSocket first for speed"""
    if not args.request:
        print("Error: No request provided")
        sys.exit(1)
    
    request = ' '.join(args.request)
    start_time = time.time()
    
    # Try WebSocket server first (much faster)
    ws_response = asyncio.run(try_websocket_request(request))
    
    if ws_response:
        # Server was available, use WebSocket response
        elapsed_ms = (time.time() - start_time) * 1000
        print(format_response(ws_response))
        print(f"\n⏱️  Response time: {elapsed_ms:.2f}ms (via WebSocket)")
    else:
        # Fall back to direct mode (slower, loads Python each time)
        try:
            router = JeevesRouter()
            result = router.route(request)
            elapsed_ms = (time.time() - start_time) * 1000
            print(format_response(result))
            print(f"\n⏱️  Response time: {elapsed_ms:.2f}ms (direct mode)")
            if not is_server_running():
                print(f"\n💡 Tip: Start 'python server.py start' for faster responses")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


async def interactive_async(use_websocket: bool = True, handle_upstream: bool = False):
    """Interactive mode with WebSocket support"""
    router = None
    ws_connected = False
    websocket = None
    upstream_mode = handle_upstream
    
    # Try to connect via WebSocket first
    if use_websocket and HAS_WEBSOCKETS:
        try:
            uri = f"ws://{DEFAULT_WS_HOST}:{DEFAULT_WS_PORT}"
            websocket = await asyncio.wait_for(
                websockets.connect(uri, close_timeout=0.5),
                timeout=1.0
            )
            ws_connected = True
            print_banner()
            print(f"🚀 Interactive Mode (WebSocket - Fast)")
            print(f"   Connected to: {uri}")
        except:
            ws_connected = False
    
    # Fall back to direct mode
    if not ws_connected:
        router = JeevesRouter()
        print_banner()
        print("Interactive Mode (Direct - Slower)")
        if not is_server_running():
            print(f"💡 Tip: Start 'python server.py start' for faster responses")
    
    print("Type 'exit' or 'quit' to exit")
    if ws_connected:
        print("Type '/upstream on' or '/upstream off' to toggle upstream handling\n")
    else:
        print()
    
    try:
        while True:
            try:
                request = input("You: ").strip()
                
                if request.lower() in ('exit', 'quit'):
                    break
                if not request:
                    continue
                
                start_time = time.time()
                
                # Handle upstream toggle
                if request.lower() == '/upstream on':
                    if ws_connected:
                        upstream_mode = True
                        print("✅ Upstream handling enabled (server will call LLMs directly)")
                    else:
                        print("⚠️  Upstream handling requires WebSocket server with API keys configured")
                    continue
                
                if request.lower() == '/upstream off':
                    upstream_mode = False
                    print("✅ Upstream handling disabled (routing only)")
                    continue
                
                # Handle logging toggle
                if request.lower() == '/logging on':
                    if router and HAS_LOGGER:
                        logger = get_logger(router.config.config)
                        logger.enable_logging()
                        router.config.config['logging']['enabled'] = True
                        router.config.save_config()
                        router.logger = logger
                        print("✅ Logging enabled")
                    continue
                
                if request.lower() == '/logging off':
                    if router and HAS_LOGGER:
                        logger = get_logger(router.config.config)
                        logger.disable_logging()
                        router.config.config['logging']['enabled'] = False
                        router.config.save_config()
                        router.logger = None
                        print("✅ Logging disabled")
                    continue
                
                # Route the request
                if ws_connected and websocket:
                    await websocket.send(json.dumps({
                        'request': request,
                        'handle_upstream': upstream_mode
                    }))
                    response = await asyncio.wait_for(websocket.recv(), timeout=60.0 if upstream_mode else 30.0)
                    result = json.loads(response)
                    elapsed_ms = (time.time() - start_time) * 1000
                    print(format_response(result))
                    print(f"⏱️  {elapsed_ms:.2f}ms")
                else:
                    result = router.route(request)
                    elapsed_ms = (time.time() - start_time) * 1000
                    print(format_response(result))
                    print(f"⏱️  {elapsed_ms:.2f}ms")
                
                print()
                
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                
    finally:
        if websocket:
            await websocket.close()
        print("\n👋 Goodbye!")


def cmd_interactive(args):
    """Interactive mode - entry point"""
    asyncio.run(interactive_async(use_websocket=True, handle_upstream=getattr(args, 'upstream', False)))


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


def cmd_compliance(args):
    """Handle compliance logging commands"""
    try:
        from compliance_logger import ComplianceLogger, ComplianceLevel
    except ImportError:
        print("❌ Compliance logger not available")
        sys.exit(1)
    
    if args.compliance_command == 'enable':
        # Enable government compliance logging
        os.environ['JEEVES_COMPLIANCE_MODE'] = 'government'
        logger = ComplianceLogger(ComplianceLevel.GOVERNMENT)
        print("✅ Government compliance logging enabled")
        print(f"   Audit chain: {logger.chain_file}")
        print(f"   Session ID: {logger.session_id}")
        print("\n   All commands will now be logged with:")
        print("   - Immutable hash chaining")
        print("   - User and session tracking")
        print("   - Complete request/response capture")
        print("   - Processing step details")
        
    elif args.compliance_command == 'status':
        logger = ComplianceLogger()
        stats = logger.get_statistics()
        print("\n" + "="*60)
        print("  🔒 Government Compliance Status")
        print("="*60 + "\n")
        print(f"Compliance Level: {stats['compliance_level']}")
        print(f"Total Entries:    {stats['total_entries']}")
        print(f"Total Size:       {stats['total_size_bytes']:,} bytes")
        print(f"Session ID:       {stats['session_id']}")
        if stats['date_range']['earliest']:
            print(f"Date Range:       {stats['date_range']['earliest'][:10]} to {stats['date_range']['latest'][:10]}")
        print()
        
    elif args.compliance_command == 'verify':
        logger = ComplianceLogger()
        result = logger.verify_chain_integrity(args.date)
        print("\n" + "="*60)
        print("  🔍 Audit Chain Verification")
        print("="*60 + "\n")
        if result['valid']:
            print(f"✅ Chain integrity verified")
            print(f"   Entries checked: {result['entries_checked']}")
            print(f"   Date: {result['date']}")
            print(f"   No tampering detected")
        else:
            print(f"❌ Chain integrity violation detected!")
            print(f"   Entries checked: {result['entries_checked']}")
            print(f"   Violations: {len(result['violations'])}")
            for v in result['violations'][:5]:  # Show first 5
                print(f"   - Line {v['line']}: {v['type']}")
        print()
        
    elif args.compliance_command == 'export':
        logger = ComplianceLogger()
        output_file = logger.export_audit_log(
            start_date=args.start_date,
            end_date=args.end_date,
            format=args.format,
            output_file=args.output
        )
        print(f"\n✅ Audit log exported")
        print(f"   File: {output_file}")
        print(f"   Format: {args.format}")
        print()
        
    elif args.compliance_command == 'stats':
        logger = ComplianceLogger()
        stats = logger.get_statistics()
        print("\n" + "="*60)
        print("  📊 Compliance Statistics")
        print("="*60 + "\n")
        print(json.dumps(stats, indent=2))
        print()


def cmd_server_start(args):
    """Start the WebSocket server"""
    import subprocess
    import time
    
    if is_server_running():
        print("⚠️  Jeeves Server is already running")
        return
    
    print(f"🚀 Starting Jeeves WebSocket Server on port {DEFAULT_WS_PORT}...")
    
    # Start server in background
    server_script = Path(__file__).parent / "server.py"
    process = subprocess.Popen(
        [sys.executable, str(server_script), "start"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True
    )
    
    # Wait a moment to check if it started
    time.sleep(1)
    
    if is_server_running():
        print(f"✅ Jeeves Server started successfully!")
        print(f"   Connect with: jeeves route <request>")
        print(f"   Or: python client.py <request>")
    else:
        print("❌ Failed to start server")
        stdout, stderr = process.communicate(timeout=2)
        if stderr:
            print(f"Error: {stderr.decode()}")


def cmd_server_stop(args):
    """Stop the WebSocket server"""
    import os
    import signal
    
    if not is_server_running():
        print("⚠️  Jeeves Server is not running")
        return
    
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        print(f"🛑 Stopped Jeeves Server (PID: {pid})")
    except Exception as e:
        print(f"❌ Error stopping server: {e}")


def cmd_server_status(args):
    """Check server status"""
    if is_server_running():
        pid = int(PID_FILE.read_text().strip())
        print(f"🎩 Jeeves Server: Running")
        print(f"   PID: {pid}")
        print(f"   URL: ws://{DEFAULT_WS_HOST}:{DEFAULT_WS_PORT}")
        print(f"   Connect: jeeves route <request>")
    else:
        print("🎩 Jeeves Server: Stopped")
        print(f"   Start with: jeeves server start")


def cmd_init(args):
    """Initialize Jeeves (auto-start logging, server, connect to Ollama)"""
    if not HAS_AUTO_START:
        print("❌ Auto-start module not available")
        sys.exit(1)
    
    from auto_start import ensure_initialized, reset_initialization
    
    if args.reset:
        reset_initialization()
    else:
        ensure_initialized(
            enable_logging=not args.no_logging,
            start_server=not args.no_server,
            prefer_upstream=args.upstream,
            verbose=True
        )


def main():
    parser = argparse.ArgumentParser(
        description="🎩 Jeeves - Intelligent Local/Cloud Router",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  jeeves setup                    # Run initial setup
  jeeves init                     # Auto-start logging + server + Ollama
  jeeves init --upstream          # Init with upstream LLM pools
  jeeves list                     # Quick overview (models, status)
  jeeves status                   # Detailed Jeeves status
  jeeves models                   # Manage installed models
  jeeves switch                   # Switch default model
  jeeves route "ls -la"          # Route a single request
  jeeves interactive              # Start interactive mode
  jeeves server start             # Start WebSocket server (faster!)
  jeeves server stop              # Stop WebSocket server
  jeeves server status            # Check server status
  jeeves logging on               # Enable LLM interaction logging
  jeeves logging off              # Disable LLM interaction logging
  jeeves logging status           # Show logging status
  jeeves logging list             # List recent log files
  jeeves logging view --file FILE # View a specific log
  jeeves logging clear            # Clear old logs (keep 10 recent)

Government Compliance:
  jeeves compliance enable        # Enable government-grade audit logging
  jeeves compliance status        # Show compliance status
  jeeves compliance verify        # Verify audit chain integrity
  jeeves compliance export        # Export audit log for review
  jeeves compliance stats         # Show compliance statistics
  
Auto-Start:
  On first use, Jeeves automatically:
  - Enables logging
  - Connects to existing Ollama (or starts it)
  - Starts WebSocket server
  Set JEEVES_NO_AUTO_START=1 to disable
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup
    setup_parser = subparsers.add_parser('setup', help='Run setup wizard')
    setup_parser.set_defaults(func=cmd_setup)
    
    # Init (auto-start)
    init_parser = subparsers.add_parser('init', help='Initialize Jeeves (auto-start)')
    init_parser.add_argument('--no-logging', action='store_true', help='Skip enabling logging')
    init_parser.add_argument('--no-server', action='store_true', help='Skip starting WebSocket server')
    init_parser.add_argument('--upstream', '-u', action='store_true', help='Enable upstream LLM pools')
    init_parser.add_argument('--reset', action='store_true', help='Reset initialization and re-run')
    init_parser.set_defaults(func=cmd_init)
    
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
    interactive_parser.add_argument(
        '--upstream', '-u',
        action='store_true',
        help='Enable upstream LLM handling (server must have API keys configured)'
    )
    interactive_parser.set_defaults(func=cmd_interactive)
    
    # Server
    server_parser = subparsers.add_parser('server', help='Manage WebSocket server')
    server_parser.add_argument(
        'server_command',
        choices=['start', 'stop', 'status'],
        help='Server command'
    )
    server_parser.set_defaults(func=lambda args: {
        'start': cmd_server_start,
        'stop': cmd_server_stop,
        'status': cmd_server_status
    }[args.server_command](args))
    
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
    
    # Compliance (Government)
    compliance_parser = subparsers.add_parser('compliance', help='Government compliance logging')
    compliance_parser.add_argument(
        'compliance_command',
        choices=['enable', 'status', 'verify', 'export', 'stats'],
        help='Compliance command'
    )
    compliance_parser.add_argument('--date', help='Date to verify (YYYYMMDD)')
    compliance_parser.add_argument('--start-date', help='Export start date (YYYY-MM-DD)')
    compliance_parser.add_argument('--end-date', help='Export end date (YYYY-MM-DD)')
    compliance_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    compliance_parser.add_argument('--output', help='Output file for export')
    compliance_parser.set_defaults(func=cmd_compliance)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    args.func(args)


if __name__ == "__main__":
    main()
