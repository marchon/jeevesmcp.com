"""
🎩 Jeeves - Your Intelligent Local/Cloud Router

Jeeves is an intelligent request router that uses a local LLM
for fast classification and simple tasks, automatically escalating
to Kimi (cloud) when the request is complex or uncertain.

Quick Start:
    from jeeves import JeevesRouter
    
    router = JeevesRouter()
    result = router.handle("ls -la")
    
    if result.startswith("[JEEVES_ESCALATE]"):
        # Send to Kimi
        pass
    else:
        # Use local result
        print(result)
"""

try:
    # Try relative imports (when imported as a package)
    from .router import JeevesRouter
    from .config import JeevesConfig, interactive_setup
except ImportError:
    # Fall back to absolute imports (when running directly)
    from router import JeevesRouter
    from config import JeevesConfig, interactive_setup

__version__ = "0.1.0"
__all__ = ["JeevesRouter", "JeevesConfig", "interactive_setup"]
