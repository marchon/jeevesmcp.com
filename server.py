#!/usr/bin/env python3
"""
Jeeves WebSocket Server - Persistent daemon for rapid request evaluation

Runs on a high port (default 18473) and maintains:
1. A loaded JeevesRouter instance for sub-millisecond local routing
2. Connection pools to upstream LLMs (Kimi, Claude, OpenAI) for fast cloud responses

Usage:
    python server.py start [--upstream]    # Start server (with optional upstream handling)
    python server.py stop                  # Stop the server
    python server.py status                # Check server status
    
Client usage:
    python client.py "ls -la"              # Send request via WebSocket
    python client.py --interactive         # Interactive mode
    python client.py --upstream "question" # Request with upstream handling
"""

import asyncio
import json
import sys
import argparse
import signal
import os
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError:
    print("❌ websockets library required. Install: pip install websockets")
    sys.exit(1)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from router import JeevesRouter
from config import JeevesConfig

# Try to import upstream pool
try:
    from upstream_pool import (
        UpstreamPoolManager, 
        UpstreamConfig, 
        LLMProvider,
        init_default_pools,
        get_pool_manager
    )
    HAS_UPSTREAM_POOL = True
except ImportError:
    HAS_UPSTREAM_POOL = False

# Server configuration
DEFAULT_PORT = 18473  # High port, unlikely to conflict
DEFAULT_HOST = "127.0.0.1"  # Local only for security
PID_FILE = Path.home() / ".local/share/jeeves/jeeves-server.pid"


class JeevesServer:
    """Persistent WebSocket server for Jeeves with upstream LLM support"""
    
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, enable_upstream: bool = True):
        self.host = host
        self.port = port
        self.enable_upstream = enable_upstream and HAS_UPSTREAM_POOL
        self.router: Optional[JeevesRouter] = None
        self.config: Optional[JeevesConfig] = None
        self.upstream_manager: Optional[UpstreamPoolManager] = None
        self.server = None
        self._shutdown_event = asyncio.Event()
        
    async def initialize(self):
        """Initialize the router, config, and upstream pools"""
        print("🎩 Jeeves Server: Initializing...")
        self.config = JeevesConfig()
        self.router = JeevesRouter()
        
        # Initialize upstream pools if enabled
        if self.enable_upstream:
            print("   Initializing upstream connection pools...")
            self.upstream_manager = await init_default_pools()
        
        print(f"✅ Jeeves Server: Ready on {self.host}:{self.port}")
        print(f"   Model: {self.config.config['jeeves']['default_model']}")
        print(f"   Logging: {'enabled' if self.config.config['logging']['enabled'] else 'disabled'}")
        print(f"   Upstream pools: {'enabled' if self.enable_upstream and self.upstream_manager and self.upstream_manager.pools else 'disabled'}")
        print(f"   PID: {os.getpid()}")
        print("   Press Ctrl+C to stop\n")
        
    async def handle_request(self, websocket: WebSocketServerProtocol, path: str = "/"):
        """Handle incoming WebSocket connections"""
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        
        try:
            async for message in websocket:
                try:
                    # Parse request
                    request_data = json.loads(message)
                    request_text = request_data.get('request', '').strip()
                    handle_upstream = request_data.get('handle_upstream', False)
                    
                    if not request_text:
                        response = {
                            'success': False,
                            'error': 'Empty request',
                            'result': None
                        }
                    else:
                        # Route the request using persistent router
                        route_result = self.router.route(request_text)
                        
                        # Check if we should handle upstream request
                        upstream_response = None
                        if (handle_upstream and 
                            route_result['should_escalate'] and 
                            self.upstream_manager and 
                            self.upstream_manager.pools):
                            
                            # Handle upstream request directly
                            upstream_result = await self.upstream_manager.send_request(request_text)
                            
                            if upstream_result.success:
                                upstream_response = {
                                    'content': upstream_result.content,
                                    'provider': upstream_result.provider,
                                    'model': upstream_result.model,
                                    'latency_ms': upstream_result.latency_ms,
                                    'tokens_used': upstream_result.tokens_used
                                }
                        
                        response = {
                            'success': True,
                            'destination': route_result['destination'],
                            'method': route_result['method'],
                            'should_escalate': route_result['should_escalate'],
                            'result': route_result.get('result'),
                            'log_file': route_result.get('log_file'),
                            'local': route_result['destination'] == 'local',
                            'upstream_handled': upstream_response is not None,
                            'upstream_response': upstream_response
                        }
                    
                    # Send response
                    await websocket.send(json.dumps(response))
                    
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'success': False,
                        'error': 'Invalid JSON',
                        'result': None
                    }))
                except Exception as e:
                    await websocket.send(json.dumps({
                        'success': False,
                        'error': str(e),
                        'result': None
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"⚠️  Client error ({client_info}): {e}")
            
    async def start(self):
        """Start the WebSocket server"""
        await self.initialize()
        
        # Save PID file
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        PID_FILE.write_text(str(os.getpid()))
        
        # Start server
        self.server = await websockets.serve(
            self.handle_request,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        )
        
        # Wait for shutdown signal
        await self._shutdown_event.wait()
        
    def stop(self):
        """Signal the server to stop"""
        self._shutdown_event.set()
        if self.server:
            self.server.close()
            
    async def cleanup(self):
        """Cleanup resources"""
        if self.server:
            await self.server.wait_closed()
        if self.upstream_manager:
            await self.upstream_manager.close_all()
        if PID_FILE.exists():
            PID_FILE.unlink()
        print("\n👋 Jeeves Server: Shutdown complete")


def is_server_running() -> Optional[int]:
    """Check if server is running, return PID if yes"""
    if not PID_FILE.exists():
        return None
    try:
        pid = int(PID_FILE.read_text().strip())
        # Check if process exists
        os.kill(pid, 0)
        return pid
    except (ValueError, OSError, ProcessLookupError):
        # Stale PID file
        PID_FILE.unlink(missing_ok=True)
        return None


async def start_server(host: str, port: int, enable_upstream: bool = True):
    """Start the server"""
    # Check if already running
    existing_pid = is_server_running()
    if existing_pid:
        print(f"⚠️  Jeeves Server already running (PID: {existing_pid})")
        print(f"   Connect with: python client.py --host {host} --port {port}")
        return
    
    server = JeevesServer(host, port, enable_upstream=enable_upstream)
    
    # Setup signal handlers
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, server.stop)
    
    try:
        await server.start()
    finally:
        await server.cleanup()


def stop_server():
    """Stop the running server"""
    pid = is_server_running()
    if not pid:
        print("⚠️  Jeeves Server is not running")
        return
    
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"🛑 Stopped Jeeves Server (PID: {pid})")
    except ProcessLookupError:
        print("⚠️  Server process not found (stale PID file)")
        PID_FILE.unlink(missing_ok=True)
    except PermissionError:
        print(f"❌ Permission denied. Try: kill {pid}")


def status_server():
    """Check server status"""
    pid = is_server_running()
    if pid:
        print(f"🎩 Jeeves Server: Running")
        print(f"   PID: {pid}")
        print(f"   URL: ws://{DEFAULT_HOST}:{DEFAULT_PORT}")
        print(f"   Connect: python client.py")
        print(f"   Upstream pools: {'available' if HAS_UPSTREAM_POOL else 'not installed'}")
        if HAS_UPSTREAM_POOL:
            print(f"   Set API keys to enable upstream handling:")
            print(f"     - KIMI_API_KEY or MOONSHOT_API_KEY")
            print(f"     - CLAUDE_API_KEY or ANTHROPIC_API_KEY")
            print(f"     - OPENAI_API_KEY")
    else:
        print("🎩 Jeeves Server: Stopped")
        print(f"   Start with: python server.py start")


def main():
    parser = argparse.ArgumentParser(
        description="Jeeves WebSocket Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python server.py start              # Start server on default port
    python server.py start --upstream   # Start with upstream LLM pools
    python server.py start --no-upstream # Start without upstream pools
    python server.py start --port 9999  # Start on custom port
    python server.py stop               # Stop server
    python server.py status             # Check status
        """
    )
    
    parser.add_argument(
        'command',
        choices=['start', 'stop', 'status'],
        help='Server command'
    )
    parser.add_argument(
        '--host',
        default=DEFAULT_HOST,
        help=f'Host to bind (default: {DEFAULT_HOST})'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=DEFAULT_PORT,
        help=f'Port to bind (default: {DEFAULT_PORT})'
    )
    parser.add_argument(
        '--upstream',
        dest='enable_upstream',
        action='store_true',
        default=True,
        help='Enable upstream LLM connection pools (default: enabled)'
    )
    parser.add_argument(
        '--no-upstream',
        dest='enable_upstream',
        action='store_false',
        help='Disable upstream LLM connection pools'
    )
    
    args = parser.parse_args()
    
    if args.command == 'start':
        print(f"🚀 Starting Jeeves Server on {args.host}:{args.port}...")
        if not HAS_UPSTREAM_POOL:
            print("   (upstream_pool.py not available, upstream disabled)")
            args.enable_upstream = False
        asyncio.run(start_server(args.host, args.port, args.enable_upstream))
    elif args.command == 'stop':
        stop_server()
    elif args.command == 'status':
        status_server()


if __name__ == "__main__":
    main()
