#!/usr/bin/env python3
"""
Jeeves WebSocket Client - Fast request routing via persistent server

Connects to the Jeeves WebSocket server for rapid request evaluation
without reloading Python for each request.

Usage:
    python client.py "ls -la"           # Single request
    python client.py --interactive      # Interactive mode
    python client.py --host 127.0.0.1 --port 18473 "pwd"
"""

import asyncio
import json
import sys
import argparse
import time
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import websockets
except ImportError:
    print("❌ websockets library required. Install: pip install websockets")
    sys.exit(1)

# Default connection settings
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 18473


class JeevesClient:
    """WebSocket client for Jeeves server"""
    
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}"
        self.websocket = None
        
    async def connect(self) -> bool:
        """Connect to the server"""
        try:
            self.websocket = await websockets.connect(self.uri)
            return True
        except ConnectionRefusedError:
            print(f"❌ Cannot connect to Jeeves Server at {self.uri}")
            print(f"   Is the server running? Start with: python server.py start")
            return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
            
    async def send_request(self, request: str, handle_upstream: bool = False) -> Optional[Dict[str, Any]]:
        """Send a request and get response"""
        if not self.websocket:
            return None
            
        message = json.dumps({
            'request': request,
            'handle_upstream': handle_upstream
        })
        await self.websocket.send(message)
        response = await self.websocket.recv()
        return json.loads(response)
        
    async def close(self):
        """Close connection"""
        if self.websocket:
            await self.websocket.close()
            
    def format_response(self, response: Dict[str, Any]) -> str:
        """Format the response for display"""
        if not response.get('success'):
            error = response.get('error', 'Unknown error')
            return f"❌ Error: {error}"
            
        # Check if upstream was handled by server
        if response.get('upstream_handled') and response.get('upstream_response'):
            upstream = response['upstream_response']
            content = upstream.get('content', '')
            provider = upstream.get('provider', 'unknown')
            model = upstream.get('model', 'unknown')
            latency = upstream.get('latency_ms', 0)
            log_file = response.get('log_file')
            log_suffix = f" | 📝 {Path(log_file).name}" if log_file else ""
            
            return f"{content}\n\n☁️  UPSTREAM → {provider.title()} ({model}){log_suffix}\n⏱️  LLM latency: {latency:.0f}ms"
            
        elif response.get('should_escalate'):
            # Upstream but not handled (no API keys configured)
            log_file = response.get('log_file')
            log_suffix = f" | 📝 {Path(log_file).name}" if log_file else ""
            return f"\n☁️  UPSTREAM → Primary AI (client must handle){log_suffix}"
        else:
            # Local
            result = response.get('result', 'No result')
            log_file = response.get('log_file')
            log_suffix = f" | 📝 {Path(log_file).name}" if log_file else ""
            return f"{result}\n\n✅ LOCAL → Jeeves{log_suffix}"


async def send_single_request(host: str, port: int, request: str, handle_upstream: bool = False):
    """Send a single request and display result"""
    client = JeevesClient(host, port)
    
    if not await client.connect():
        sys.exit(1)
        
    try:
        start_time = time.time()
        response = await client.send_request(request, handle_upstream=handle_upstream)
        elapsed_ms = (time.time() - start_time) * 1000
        
        if response:
            print(client.format_response(response))
            print(f"\n⏱️  Response time: {elapsed_ms:.2f}ms")
        else:
            print("❌ No response received")
            
    finally:
        await client.close()


async def interactive_mode(host: str, port: int, initial_handle_upstream: bool = False):
    """Run interactive mode"""
    client = JeevesClient(host, port)
    handle_upstream = initial_handle_upstream
    
    if not await client.connect():
        sys.exit(1)
        
    upstream_status = "(with upstream handling)" if handle_upstream else "(routing only)"
    print(f"""
    🎩 Jeeves WebSocket Client
    Connected to: {client.uri}
    {upstream_status}
    Type 'exit' or 'quit' to exit
    Type '/upstream on' or '/upstream off' to toggle upstream handling
    """)
    
    try:
        while True:
            try:
                request = input("You: ").strip()
                
                if request.lower() in ('exit', 'quit'):
                    break
                if not request:
                    continue
                
                # Toggle upstream handling
                if request.lower() == '/upstream on':
                    handle_upstream = True
                    print("✅ Upstream handling enabled")
                    continue
                if request.lower() == '/upstream off':
                    handle_upstream = False
                    print("✅ Upstream handling disabled (routing only)")
                    continue
                    
                start_time = time.time()
                response = await client.send_request(request, handle_upstream=handle_upstream)
                elapsed_ms = (time.time() - start_time) * 1000
                
                if response:
                    print(client.format_response(response))
                    print(f"⏱️  {elapsed_ms:.2f}ms")
                else:
                    print("❌ No response received")
                    
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                
    finally:
        await client.close()
        print("👋 Goodbye!")


def main():
    parser = argparse.ArgumentParser(
        description="Jeeves WebSocket Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python client.py "ls -la"              # Single request
    python client.py "what is python"      # Complex question
    python client.py --interactive         # Interactive mode
    python client.py --upstream "question" # Request with upstream handling
    python client.py --host 192.168.1.5    # Connect to remote server
        """
    )
    
    parser.add_argument(
        'request',
        nargs='?',
        help='Request to send (if not provided, uses interactive mode)'
    )
    parser.add_argument(
        '--host',
        default=DEFAULT_HOST,
        help=f'Server host (default: {DEFAULT_HOST})'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=DEFAULT_PORT,
        help=f'Server port (default: {DEFAULT_PORT})'
    )
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Interactive mode'
    )
    parser.add_argument(
        '--upstream', '-u',
        action='store_true',
        help='Enable upstream LLM handling (server must have API keys configured)'
    )
    
    args = parser.parse_args()
    
    if args.interactive or not args.request:
        # Interactive mode
        asyncio.run(interactive_mode(args.host, args.port, initial_handle_upstream=args.upstream))
    else:
        # Single request
        asyncio.run(send_single_request(args.host, args.port, args.request, handle_upstream=args.upstream))


if __name__ == "__main__":
    main()
