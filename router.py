#!/usr/bin/env python3
"""
Jeeves - Intelligent Request Router
Routes requests between local LLM and Kimi based on complexity
"""

import re
import requests
import subprocess
import json
import sys
import os
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from config import JeevesConfig


class JeevesRouter:
    """
    Main router class that decides whether to handle requests locally
    or escalate to Kimi (cloud)
    """
    
    # Fast patterns that immediately go to local execution
    SHELL_PATTERNS = [
        r'^ls\b',
        r'^ll\b',
        r'^cat\b',
        r'^grep\b',
        r'^find\b',
        r'^cd\b',
        r'^pwd$',
        r'^head\b',
        r'^tail\b',
        r'^wc\b',
        r'^du\b',
        r'^df\b',
        r'^mkdir\b',
        r'^touch\b',
        r'^rm\b',
        r'^cp\b',
        r'^mv\b',
        r'^chmod\b',
        r'^chown\b',
        r'^ps\b',
        r'^top\b',
        r'^htop\b',
        r'^kill\b',
        r'^pkill\b',
        r'^ping\b',
        r'^curl\b',
        r'^wget\b',
        r'^tar\b',
        r'^zip\b',
        r'^unzip\b',
        r'^git\b',
        r'^which\b',
        r'^whereis\b',
        r'^echo\b',
        r'^printenv\b',
        r'^env$',
        r'^export\b',
        r'^unset\b',
        r'^alias\b',
        r'^unalias\b',
        r'^history\b',
        r'^clear$',
        r'^exit$',
        r'^whoami$',
        r'^id$',
        r'^uname\b',
        r'^hostname$',
        r'^date$',
        r'^cal\b',
        r'^uptime$',
        r'^free\b',
        r'^vmstat\b',
        r'^iostat\b',
        r'^netstat\b',
        r'^ss\b',
        r'^lsof\b',
        r'^fuser\b',
        r'^df\b',
        r'^mount\b',
        r'^umount\b',
    ]
    
    # File operation patterns
    FILE_PATTERNS = [
        (r'^read (?:file )?["\']?(.+?)["\']?$', 'read_file'),
        (r'^show (?:me )?(?:the )?(?:content of )?["\']?(.+?)["\']?$', 'read_file'),
        (r'^open (?:file )?["\']?(.+?)["\']?$', 'read_file'),
        (r'^cat (?:file )?["\']?(.+?)["\']?$', 'read_file'),
        (r'^display (?:file )?["\']?(.+?)["\']?$', 'read_file'),
        (r'^view (?:file )?["\']?(.+?)["\']?$', 'read_file'),
        (r'^list (?:files )?(?:in )?["\']?(.+?)["\']?$', 'list_dir'),
        (r'^what(?:\'s| is) in ["\']?(.+?)["\']?$', 'list_dir'),
        (r'^search for ["\']?(.+?)["\']? in ["\']?(.+?)["\']?$', 'search_in_file'),
    ]
    
    # Uncertainty markers in local LLM responses
    UNCERTAINTY_MARKERS = [
        "i don't know",
        "i'm not sure",
        "i cannot",
        "i can't",
        "uncertain",
        "unclear",
        "don't understand",
        "confused",
        "unsure",
        "ambiguous",
        "beyond my capabilities",
        "beyond my ability",
        "unable to",
        "cannot help",
        "can't help",
        "not able to",
        "difficult to",
        "too complex",
        "too complicated",
    ]
    
    def __init__(self, config: Optional[JeevesConfig] = None):
        self.config = config or JeevesConfig()
        self._ensure_ollama_running()
    
    def _ensure_ollama_running(self):
        """Ensure Ollama is running, start if configured to autostart"""
        if not self.config.is_ollama_running():
            if self.config.config['ollama']['autostart']:
                print("🚀 Jeeves is starting Ollama...")
                if not self.config.start_ollama():
                    raise RuntimeError("Could not start Ollama. Please start it manually: ollama serve")
            else:
                raise RuntimeError("Ollama is not running. Start it with: ollama serve")
    
    def _matches_shell_pattern(self, request: str) -> bool:
        """Check if request matches a known shell command pattern"""
        if not self.config.config['routing']['use_pattern_matching']:
            return False
        
        request_lower = request.strip().lower()
        for pattern in self.SHELL_PATTERNS:
            if re.match(pattern, request_lower, re.IGNORECASE):
                return True
        return False
    
    def _matches_file_pattern(self, request: str) -> Optional[Tuple[str, str]]:
        """Check if request matches a file operation pattern"""
        if not self.config.config['routing']['use_pattern_matching']:
            return None
        
        request_lower = request.strip().lower()
        for pattern, action in self.FILE_PATTERNS:
            match = re.match(pattern, request_lower, re.IGNORECASE)
            if match:
                return (action, match.groups())
        return None
    
    def _classify_with_local_llm(self, request: str) -> Dict[str, Any]:
        """Use local LLM to classify request complexity"""
        if not self.config.config['routing']['use_local_llm']:
            return {'classification': 'UNCERTAIN', 'confidence': 0}
        
        model = self.config.config['jeeves']['default_model']
        timeout = self.config.config['jeeves']['timeout_seconds']
        
        # Classification prompt
        prompt = f"""You are a request classifier. Classify the following user request.

Request: "{request}"

Respond with EXACTLY one of these categories:
- SIMPLE: Basic shell commands, file operations, simple queries
- MODERATE: Multi-step local operations, code analysis, structured data
- COMPLEX: Design decisions, creative tasks, reasoning, analysis requiring deep thought

If you are uncertain or the request is unclear, respond with: UNCERTAIN

Your response must be ONLY the category word (SIMPLE, MODERATE, COMPLEX, or UNCERTAIN).

Classification:"""

        try:
            response = requests.post(
                f"{self.config.config['ollama']['host']}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 10}
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                classification = result.get('response', '').strip().upper()
                
                # Clean up classification
                for valid in ['SIMPLE', 'MODERATE', 'COMPLEX', 'UNCERTAIN']:
                    if valid in classification:
                        return {
                            'classification': valid,
                            'raw_response': result.get('response', ''),
                            'confidence': self._extract_confidence(classification)
                        }
                
                return {'classification': 'UNCERTAIN', 'raw_response': classification, 'confidence': 0}
            
            return {'classification': 'UNCERTAIN', 'error': f'HTTP {response.status_code}', 'confidence': 0}
            
        except requests.Timeout:
            return {'classification': 'UNCERTAIN', 'error': 'timeout', 'confidence': 0}
        except Exception as e:
            return {'classification': 'UNCERTAIN', 'error': str(e), 'confidence': 0}
    
    def _extract_confidence(self, response: str) -> float:
        """Extract confidence score from classification response"""
        # Simple heuristic: direct matches are high confidence
        direct_matches = ['SIMPLE', 'MODERATE', 'COMPLEX']
        for match in direct_matches:
            if response.strip() == match:
                return 1.0
        
        # Contains but not exact match
        for match in direct_matches:
            if match in response:
                return 0.7
        
        return 0.0
    
    def _is_uncertain_response(self, response: str) -> bool:
        """Check if local LLM response indicates uncertainty"""
        response_lower = response.lower()
        return any(marker in response_lower for marker in self.UNCERTAINTY_MARKERS)
    
    def _execute_local_shell(self, command: str) -> str:
        """Execute a shell command locally"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.getcwd()
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr}"
            
            if result.returncode != 0:
                output += f"\n[exit code: {result.returncode}]"
            
            return output if output else "(no output)"
            
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 60 seconds"
        except Exception as e:
            return f"Error executing command: {e}"
    
    def _read_local_file(self, filepath: str) -> str:
        """Read a file locally"""
        try:
            path = Path(filepath).expanduser()
            if not path.exists():
                return f"Error: File '{filepath}' not found"
            
            if path.is_dir():
                return f"Error: '{filepath}' is a directory. Use 'ls {filepath}' to list contents."
            
            # Check file size
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > 10:
                return f"Error: File '{filepath}' is {size_mb:.1f}MB (max 10MB for local reading)"
            
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            return content
            
        except Exception as e:
            return f"Error reading file: {e}"
    
    def _list_local_directory(self, dirpath: str = '.') -> str:
        """List directory contents locally"""
        try:
            path = Path(dirpath).expanduser()
            if not path.exists():
                return f"Error: Directory '{dirpath}' not found"
            
            if not path.is_dir():
                return f"Error: '{dirpath}' is not a directory"
            
            items = []
            for item in sorted(path.iterdir()):
                item_type = "📁" if item.is_dir() else "📄"
                size = ""
                if item.is_file():
                    size_bytes = item.stat().st_size
                    if size_bytes < 1024:
                        size = f" {size_bytes}B"
                    elif size_bytes < 1024 * 1024:
                        size = f" {size_bytes/1024:.1f}KB"
                    else:
                        size = f" {size_bytes/(1024*1024):.1f}MB"
                items.append(f"{item_type} {item.name}{size}")
            
            return "\n".join(items) if items else "(empty directory)"
            
        except Exception as e:
            return f"Error listing directory: {e}"
    
    def _generate_local_response(self, request: str) -> str:
        """Generate a response using the local LLM"""
        model = self.config.config['jeeves']['default_model']
        timeout = self.config.config['jeeves']['timeout_seconds']
        
        prompt = f"""You are Jeeves, a helpful assistant. Respond to the user's request concisely.

User: {request}

Jeeves:"""

        try:
            response = requests.post(
                f"{self.config.config['ollama']['host']}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7}
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                return f"Error: Local LLM returned HTTP {response.status_code}"
                
        except requests.Timeout:
            return "Error: Local LLM timed out"
        except Exception as e:
            return f"Error with local LLM: {e}"
    
    def route(self, request: str) -> Dict[str, Any]:
        """
        Main routing method - decides where to send the request
        
        Returns dict with:
        - destination: 'local' or 'cloud'
        - method: how it was routed (pattern, classification, fallback)
        - result: the response (if local)
        - should_escalate: whether to send to Kimi
        """
        
        # Step 1: Pattern matching (fastest)
        if self._matches_shell_pattern(request):
            print("🎯 Jeeves: Recognized shell command")
            result = self._execute_local_shell(request)
            return {
                'destination': 'local',
                'method': 'pattern_match',
                'result': result,
                'should_escalate': False
            }
        
        # Step 2: File operation patterns
        file_match = self._matches_file_pattern(request)
        if file_match:
            action, groups = file_match
            print(f"🎯 Jeeves: Recognized file operation ({action})")
            
            if action == 'read_file':
                result = self._read_local_file(groups[0])
            elif action == 'list_dir':
                result = self._list_local_directory(groups[0])
            else:
                result = f"File operation '{action}' not yet implemented"
            
            return {
                'destination': 'local',
                'method': 'pattern_match',
                'result': result,
                'should_escalate': False
            }
        
        # Step 3: Local LLM classification
        if self.config.config['routing']['use_local_llm']:
            print("🤔 Jeeves: Classifying request...")
            classification = self._classify_with_local_llm(request)
            
            category = classification.get('classification', 'UNCERTAIN')
            confidence = classification.get('confidence', 0)
            
            print(f"   Classification: {category} (confidence: {confidence:.2f})")
            
            # Handle based on classification
            if category == 'SIMPLE' and confidence >= 0.7:
                # Try to handle locally
                result = self._generate_local_response(request)
                
                # Check if response indicates uncertainty
                if self.config.config['routing']['auto_fallback'] and self._is_uncertain_response(result):
                    print("⚠️  Jeeves: Uncertain about response, escalating to Kimi")
                    return {
                        'destination': 'cloud',
                        'method': 'fallback_uncertainty',
                        'classification': classification,
                        'should_escalate': True
                    }
                
                return {
                    'destination': 'local',
                    'method': 'llm_classification',
                    'classification': classification,
                    'result': result,
                    'should_escalate': False
                }
            
            elif category == 'MODERATE' and confidence >= 0.8:
                # Try local first, but be ready to escalate
                result = self._generate_local_response(request)
                
                if len(result) < 50 or self._is_uncertain_response(result):
                    print("⚠️  Jeeves: Response seems incomplete, escalating to Kimi")
                    return {
                        'destination': 'cloud',
                        'method': 'fallback_incomplete',
                        'classification': classification,
                        'should_escalate': True
                    }
                
                return {
                    'destination': 'local',
                    'method': 'llm_classification',
                    'classification': classification,
                    'result': result,
                    'should_escalate': False
                }
            
            else:
                # COMPLEX or UNCERTAIN - go to cloud
                print("☁️  Jeeves: Routing to Kimi for best results")
                return {
                    'destination': 'cloud',
                    'method': 'llm_classification',
                    'classification': classification,
                    'should_escalate': True
                }
        
        # Default: escalate to cloud
        print("☁️  Jeeves: Routing to Kimi")
        return {
            'destination': 'cloud',
            'method': 'default',
            'should_escalate': True
        }
    
    def handle(self, request: str) -> str:
        """
        Convenience method that routes and returns the result
        If escalated to cloud, returns a message indicating so
        """
        result = self.route(request)
        
        if result['should_escalate']:
            return f"[JEEVES_ESCALATE] {result['method']}"
        
        return result.get('result', 'No result')


# Simple CLI interface
def main():
    """Simple CLI for testing Jeeves routing"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: jeeves-router <request>")
        print("       jeeves-router --interactive")
        sys.exit(1)
    
    if sys.argv[1] == '--interactive':
        # Interactive mode
        try:
            router = JeevesRouter()
            print("🎩 Jeeves Interactive Mode")
            print("Type 'exit' or 'quit' to exit\n")
            
            while True:
                try:
                    request = input("You: ").strip()
                    if request.lower() in ('exit', 'quit'):
                        break
                    if not request:
                        continue
                    
                    result = router.route(request)
                    
                    if result['should_escalate']:
                        print(f"🤖 Jeeves → Kimi: {result['method']}")
                        print("   [Would be sent to Kimi]")
                    else:
                        print(f"🤖 Jeeves: {result['method']}")
                        print(f"\n{result.get('result', 'No result')}")
                    
                    print()
                    
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    
        except Exception as e:
            print(f"Failed to initialize Jeeves: {e}")
            sys.exit(1)
    
    else:
        # Single request mode
        request = ' '.join(sys.argv[1:])
        
        try:
            router = JeevesRouter()
            result = router.route(request)
            
            print(f"Routing: {result['destination']} ({result['method']})")
            
            if result['should_escalate']:
                print("\n[Request would be sent to Kimi]")
            else:
                print(f"\n{result.get('result', 'No result')}")
                
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
