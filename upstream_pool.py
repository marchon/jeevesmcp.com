#!/usr/bin/env python3
"""
Upstream LLM Connection Pool

Maintains persistent HTTP connections to cloud LLM providers
for improved throughput and concurrent request handling.

Supported providers:
- Kimi (Moonshot AI)
- Claude (Anthropic)
- OpenAI
- Custom OpenAI-compatible endpoints
"""

import json
import time
import asyncio
import aiohttp
import threading
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue
from concurrent.futures import ThreadPoolExecutor


class LLMProvider(Enum):
    """Supported LLM providers"""
    KIMI = "kimi"
    CLAUDE = "claude"
    OPENAI = "openai"
    CUSTOM = "custom"


@dataclass
class UpstreamConfig:
    """Configuration for upstream LLM connection"""
    provider: LLMProvider
    api_key: str
    base_url: Optional[str] = None
    model: str = "default"
    max_connections: int = 10
    timeout: float = 30.0
    max_retries: int = 3
    
    def __post_init__(self):
        # Set default base URLs
        if self.base_url is None:
            urls = {
                LLMProvider.KIMI: "https://api.moonshot.cn/v1",
                LLMProvider.CLAUDE: "https://api.anthropic.com/v1",
                LLMProvider.OPENAI: "https://api.openai.com/v1",
            }
            self.base_url = urls.get(self.provider, "")


@dataclass
class UpstreamResponse:
    """Response from upstream LLM"""
    success: bool
    content: str
    provider: str
    model: str
    latency_ms: float
    tokens_used: Optional[int] = None
    error: Optional[str] = None
    raw_response: Optional[Dict] = None


class UpstreamConnectionPool:
    """
    Connection pool for upstream LLM providers.
    
    Maintains persistent HTTP connections and supports:
    - Concurrent requests
    - Connection reuse
    - Automatic retries
    - Request queueing
    """
    
    def __init__(self, config: UpstreamConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()
        self._request_count = 0
        self._error_count = 0
        self._total_latency = 0.0
        
    async def initialize(self):
        """Initialize the connection pool"""
        if self.session is None or self.session.closed:
            # Create connector with connection pooling
            connector = aiohttp.TCPConnector(
                limit=self.config.max_connections,
                limit_per_host=self.config.max_connections,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            
            # Create session with persistent connections
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self._get_headers()
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers for provider"""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        
        # Provider-specific headers
        if self.config.provider == LLMProvider.CLAUDE:
            headers["anthropic-version"] = "2023-06-01"
        
        return headers
    
    async def send_request(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> UpstreamResponse:
        """
        Send request to upstream LLM
        
        Args:
            message: User message
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            
        Returns:
            UpstreamResponse with result or error
        """
        await self.initialize()
        
        start_time = time.time()
        
        # Build request payload based on provider
        payload = self._build_payload(message, system_prompt, temperature, max_tokens)
        
        # Send with retries
        for attempt in range(self.config.max_retries):
            try:
                endpoint = self._get_endpoint()
                
                async with self.session.post(
                    endpoint,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = self._parse_response(data)
                        
                        latency_ms = (time.time() - start_time) * 1000
                        self._request_count += 1
                        self._total_latency += latency_ms
                        
                        return UpstreamResponse(
                            success=True,
                            content=result,
                            provider=self.config.provider.value,
                            model=self.config.model,
                            latency_ms=latency_ms,
                            tokens_used=data.get('usage', {}).get('total_tokens'),
                            raw_response=data
                        )
                    else:
                        error_text = await response.text()
                        if attempt < self.config.max_retries - 1:
                            await asyncio.sleep(0.5 * (attempt + 1))
                            continue
                        
                        self._error_count += 1
                        return UpstreamResponse(
                            success=False,
                            content="",
                            provider=self.config.provider.value,
                            model=self.config.model,
                            latency_ms=(time.time() - start_time) * 1000,
                            error=f"HTTP {response.status}: {error_text}"
                        )
                        
            except asyncio.TimeoutError:
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                
                self._error_count += 1
                return UpstreamResponse(
                    success=False,
                    content="",
                    provider=self.config.provider.value,
                    model=self.config.model,
                    latency_ms=(time.time() - start_time) * 1000,
                    error="Request timeout"
                )
            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                
                self._error_count += 1
                return UpstreamResponse(
                    success=False,
                    content="",
                    provider=self.config.provider.value,
                    model=self.config.model,
                    latency_ms=(time.time() - start_time) * 1000,
                    error=str(e)
                )
        
        # Should not reach here
        return UpstreamResponse(
            success=False,
            content="",
            provider=self.config.provider.value,
            model=self.config.model,
            latency_ms=(time.time() - start_time) * 1000,
            error="Max retries exceeded"
        )
    
    def _build_payload(
        self,
        message: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Build request payload for provider"""
        
        if self.config.provider == LLMProvider.CLAUDE:
            payload = {
                "model": self.config.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": message}]
            }
            if system_prompt:
                payload["system"] = system_prompt
            return payload
        
        else:  # Kimi, OpenAI, Custom (OpenAI-compatible)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})
            
            return {
                "model": self.config.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
    
    def _get_endpoint(self) -> str:
        """Get API endpoint for provider"""
        endpoints = {
            LLMProvider.KIMI: f"{self.config.base_url}/chat/completions",
            LLMProvider.CLAUDE: f"{self.config.base_url}/messages",
            LLMProvider.OPENAI: f"{self.config.base_url}/chat/completions",
            LLMProvider.CUSTOM: f"{self.config.base_url}/chat/completions",
        }
        return endpoints.get(self.config.provider, "")
    
    def _parse_response(self, data: Dict) -> str:
        """Parse response from provider"""
        try:
            if self.config.provider == LLMProvider.CLAUDE:
                # Claude format
                content_blocks = data.get('content', [])
                return ''.join(block.get('text', '') for block in content_blocks)
            else:
                # OpenAI-compatible format (Kimi, OpenAI)
                choices = data.get('choices', [])
                if choices:
                    return choices[0].get('message', {}).get('content', '')
                return ''
        except Exception as e:
            return f"[Error parsing response: {e}]"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        avg_latency = self._total_latency / self._request_count if self._request_count > 0 else 0
        return {
            "provider": self.config.provider.value,
            "model": self.config.model,
            "requests": self._request_count,
            "errors": self._error_count,
            "avg_latency_ms": round(avg_latency, 2),
            "error_rate": round(self._error_count / max(self._request_count, 1) * 100, 2)
        }
    
    async def close(self):
        """Close connection pool"""
        if self.session and not self.session.closed:
            await self.session.close()


class UpstreamPoolManager:
    """
    Manager for multiple upstream connection pools.
    
    Supports multiple providers and load balancing.
    """
    
    def __init__(self):
        self.pools: Dict[str, UpstreamConnectionPool] = {}
        self._default_provider: Optional[str] = None
    
    def add_pool(self, name: str, config: UpstreamConfig, default: bool = False):
        """Add a connection pool"""
        self.pools[name] = UpstreamConnectionPool(config)
        if default or self._default_provider is None:
            self._default_provider = name
    
    async def send_request(
        self,
        message: str,
        provider: Optional[str] = None,
        **kwargs
    ) -> UpstreamResponse:
        """Send request to specified or default provider"""
        pool_name = provider or self._default_provider
        
        if pool_name not in self.pools:
            return UpstreamResponse(
                success=False,
                content="",
                provider="none",
                model="none",
                latency_ms=0,
                error=f"Provider '{pool_name}' not configured"
            )
        
        pool = self.pools[pool_name]
        return await pool.send_request(message, **kwargs)
    
    async def send_concurrent(
        self,
        messages: List[str],
        provider: Optional[str] = None,
        **kwargs
    ) -> List[UpstreamResponse]:
        """Send multiple requests concurrently"""
        tasks = [
            self.send_request(msg, provider, **kwargs)
            for msg in messages
        ]
        return await asyncio.gather(*tasks)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get stats for all pools"""
        return {
            name: pool.get_stats()
            for name, pool in self.pools.items()
        }
    
    async def close_all(self):
        """Close all connection pools"""
        await asyncio.gather(*[
            pool.close() for pool in self.pools.values()
        ])


# Global pool manager instance
_pool_manager: Optional[UpstreamPoolManager] = None


def get_pool_manager() -> UpstreamPoolManager:
    """Get or create global pool manager"""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = UpstreamPoolManager()
    return _pool_manager


async def init_default_pools():
    """Initialize default connection pools from environment/config"""
    import os
    
    manager = get_pool_manager()
    
    # Check for Kimi API key
    kimi_key = os.environ.get('KIMI_API_KEY') or os.environ.get('MOONSHOT_API_KEY')
    if kimi_key:
        manager.add_pool(
            'kimi',
            UpstreamConfig(
                provider=LLMProvider.KIMI,
                api_key=kimi_key,
                model=os.environ.get('KIMI_MODEL', 'moonshot-v1-8k'),
                max_connections=10
            ),
            default=True
        )
        print(f"✅ Upstream pool: Kimi configured")
    
    # Check for Claude API key
    claude_key = os.environ.get('CLAUDE_API_KEY') or os.environ.get('ANTHROPIC_API_KEY')
    if claude_key:
        manager.add_pool(
            'claude',
            UpstreamConfig(
                provider=LLMProvider.CLAUDE,
                api_key=claude_key,
                model=os.environ.get('CLAUDE_MODEL', 'claude-3-sonnet-20240229'),
                max_connections=10
            ),
            default=not kimi_key  # Default if no Kimi
        )
        print(f"✅ Upstream pool: Claude configured")
    
    # Check for OpenAI API key
    openai_key = os.environ.get('OPENAI_API_KEY')
    if openai_key:
        manager.add_pool(
            'openai',
            UpstreamConfig(
                provider=LLMProvider.OPENAI,
                api_key=openai_key,
                model=os.environ.get('OPENAI_MODEL', 'gpt-4'),
                max_connections=10
            ),
            default=not kimi_key and not claude_key
        )
        print(f"✅ Upstream pool: OpenAI configured")
    
    if not manager.pools:
        print("⚠️  No upstream LLM pools configured. Set API keys in environment.")
    
    return manager


# Example usage
if __name__ == "__main__":
    async def demo():
        # Initialize pools
        manager = await init_default_pools()
        
        if not manager.pools:
            print("No pools configured. Demo requires API keys.")
            return
        
        # Single request
        print("\n--- Single Request ---")
        response = await manager.send_request("What is the capital of France?")
        print(f"Success: {response.success}")
        print(f"Content: {response.content[:100]}...")
        print(f"Latency: {response.latency_ms:.2f}ms")
        
        # Concurrent requests
        print("\n--- Concurrent Requests ---")
        questions = [
            "What is Python?",
            "Explain machine learning",
            "What is the speed of light?"
        ]
        
        start = time.time()
        responses = await manager.send_concurrent(questions)
        total_time = (time.time() - start) * 1000
        
        for q, r in zip(questions, responses):
            print(f"Q: {q[:30]}...")
            print(f"  Success: {r.success}, Latency: {r.latency_ms:.2f}ms")
        print(f"Total time: {total_time:.2f}ms (vs ~{sum(r.latency_ms for r in responses):.0f}ms sequential)")
        
        # Stats
        print("\n--- Pool Stats ---")
        print(json.dumps(manager.get_stats(), indent=2))
        
        await manager.close_all()
    
    asyncio.run(demo())
