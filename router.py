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
import time
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from config import JeevesConfig

# Try to import logger, but make it optional
try:
    from llm_logger import LLMLogger, get_logger
    HAS_LOGGER = True
except ImportError:
    HAS_LOGGER = False

# Try to import model configs for optimization
try:
    from model_configs import (
        format_classification_prompt,
        format_response_prompt,
        get_classification_params,
        get_response_params,
        get_confidence_thresholds,
        get_model_capabilities,
        detect_model_family,
    )
    HAS_MODEL_CONFIGS = True
except ImportError:
    HAS_MODEL_CONFIGS = False


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
        self.logger = None
        if HAS_LOGGER:
            self.logger = get_logger(self.config.config)
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
        """Use local LLM to classify request complexity with model-specific optimization"""
        if not self.config.config['routing']['use_local_llm']:
            return {'classification': 'UNCERTAIN', 'confidence': 0}
        
        model = self.config.config['jeeves']['default_model']
        timeout = self.config.config['jeeves']['timeout_seconds']
        
        # Get model-specific prompt and parameters
        if HAS_MODEL_CONFIGS:
            prompt = format_classification_prompt(model, request)
            params = get_classification_params(model)
            capabilities = get_model_capabilities(model)
        else:
            # Fallback to generic prompt
            prompt = f"""You are a request classifier. Classify the following user request.

Request: "{request}"

Respond with EXACTLY one of these categories:
- SIMPLE: Basic shell commands, file operations, simple queries
- MODERATE: Multi-step local operations, code analysis, structured data
- COMPLEX: Design decisions, creative tasks, reasoning, analysis requiring deep thought

If you are uncertain or the request is unclear, respond with: UNCERTAIN

Your response must be ONLY the category word (SIMPLE, MODERATE, COMPLEX, or UNCERTAIN).

Classification:"""
            params = {"temperature": 0.1, "num_predict": 10}
            capabilities = {"classification": 0.7, "response": 0.6, "reasoning": 0.5}

        # Log the decision prompt
        if self.logger:
            self.logger.log_jeeves_decision_prompt(
                prompt=prompt,
                model=model,
                context={**params, "timeout": timeout, "capabilities": capabilities}
            )

        try:
            response = requests.post(
                f"{self.config.config['ollama']['host']}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": params
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                classification = result.get('response', '').strip().upper()
                
                # Clean up classification
                parsed_classification = 'UNCERTAIN'
                for valid in ['SIMPLE', 'MODERATE', 'COMPLEX', 'UNCERTAIN']:
                    if valid in classification:
                        parsed_classification = valid
                        break
                
                confidence = self._extract_confidence(classification)
                
                # Log the decision response
                if self.logger:
                    self.logger.log_jeeves_decision_response(
                        response=result.get('response', ''),
                        classification=parsed_classification,
                        confidence=confidence
                    )
                
                return {
                    'classification': parsed_classification,
                    'raw_response': result.get('response', ''),
                    'confidence': confidence
                }
            
            error_result = {'classification': 'UNCERTAIN', 'error': f'HTTP {response.status_code}', 'confidence': 0}
            if self.logger:
                self.logger.log_error('LLM_ERROR', f'HTTP {response.status_code}')
            return error_result
            
        except requests.Timeout:
            error_result = {'classification': 'UNCERTAIN', 'error': 'timeout', 'confidence': 0}
            if self.logger:
                self.logger.log_error('LLM_ERROR', 'Local LLM classification timeout')
            return error_result
        except Exception as e:
            error_result = {'classification': 'UNCERTAIN', 'error': str(e), 'confidence': 0}
            if self.logger:
                self.logger.log_error('LLM_ERROR', str(e))
            return error_result
    
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
        start_time = time.time()
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.getcwd()
            )
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr}"
            
            if result.returncode != 0:
                output += f"\n[exit code: {result.returncode}]"
            
            result_str = output if output else "(no output)"
            
            # Log the execution
            if self.logger:
                self.logger.log_local_execution(
                    command=command,
                    result=result_str,
                    execution_time_ms=execution_time_ms
                )
            
            return result_str
            
        except subprocess.TimeoutExpired:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = "Error: Command timed out after 60 seconds"
            if self.logger:
                self.logger.log_error('EXECUTION_ERROR', error_msg)
            return error_msg
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Error executing command: {e}"
            if self.logger:
                self.logger.log_error('EXECUTION_ERROR', error_msg, traceback=str(e))
            return error_msg
    
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
        """Generate a response using the local LLM with model-specific optimization"""
        model = self.config.config['jeeves']['default_model']
        timeout = self.config.config['jeeves']['timeout_seconds']
        
        # Get model-specific prompt and parameters
        if HAS_MODEL_CONFIGS:
            prompt = format_response_prompt(model, request)
            params = get_response_params(model)
        else:
            # Fallback to generic prompt
            prompt = f"""You are Jeeves, a helpful assistant. Respond to the user's request concisely.

User: {request}

Jeeves:"""
            params = {"temperature": 0.7}

        try:
            response = requests.post(
                f"{self.config.config['ollama']['host']}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": params
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                error_msg = f"Error: Local LLM returned HTTP {response.status_code}"
                if self.logger:
                    self.logger.log_error('LLM_ERROR', error_msg)
                return error_msg
                
        except requests.Timeout:
            error_msg = "Error: Local LLM timed out"
            if self.logger:
                self.logger.log_error('LLM_ERROR', error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Error with local LLM: {e}"
            if self.logger:
                self.logger.log_error('LLM_ERROR', error_msg, traceback=str(e))
            return error_msg
    
    def _print_routing_message(self, destination: str, method: str, reason: str = ""):
        """Print fine-tuned messaging about routing decisions"""
        if destination == 'local':
            if method == 'pattern_match':
                print("✅ Jeeves: Handled instantly with pattern matching")
            elif method == 'llm_classification':
                print("✅ Jeeves: Local LLM handled this request")
            else:
                print("✅ Jeeves: Processed locally")
        else:  # cloud
            if method == 'fallback_uncertainty':
                print("🤔 Jeeves: Local LLM was uncertain → Escalating to primary AI")
                print(f"   Reason: {reason}")
            elif method == 'fallback_incomplete':
                print("📊 Jeeves: Local response incomplete → Escalating for better results")
            elif method == 'llm_classification':
                print("🧠 Jeeves: Complex request detected → Routing to primary AI")
                print("   This requires deeper reasoning than the local model can provide.")
            else:
                print("☁️  Jeeves: Routing to primary AI for best results")
    
    def route(self, request: str) -> Dict[str, Any]:
        """
        Main routing method - decides where to send the request
        
        Returns dict with:
        - destination: 'local' or 'cloud'
        - method: how it was routed (pattern, classification, fallback)
        - result: the response (if local)
        - should_escalate: whether to send to Kimi
        """
        
        # Start logging session if enabled
        if self.logger:
            self.logger.start_session(request)
            self.logger.log_system_context({
                "jeeves_version": "0.1.0",
                "default_model": self.config.config['jeeves']['default_model'],
                "pattern_matching": self.config.config['routing']['use_pattern_matching'],
                "local_llm": self.config.config['routing']['use_local_llm'],
                "auto_fallback": self.config.config['routing']['auto_fallback']
            })
        
        try:
            # Step 1: Pattern matching (fastest)
            if self._matches_shell_pattern(request):
                print("🎯 Jeeves: Recognized shell command")
                result = self._execute_local_shell(request)
                self._print_routing_message('local', 'pattern_match')
                
                result_dict = {
                    'destination': 'local',
                    'method': 'pattern_match',
                    'result': result,
                    'should_escalate': False
                }
                
                if self.logger:
                    self.logger.end_session(result, 'LOCAL')
                
                return result_dict
            
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
                
                self._print_routing_message('local', 'pattern_match')
                
                result_dict = {
                    'destination': 'local',
                    'method': 'pattern_match',
                    'result': result,
                    'should_escalate': False
                }
                
                if self.logger:
                    self.logger.end_session(result, 'LOCAL')
                
                return result_dict
            
            # Step 3: Local LLM classification
            if self.config.config['routing']['use_local_llm']:
                print("🤔 Jeeves: Analyzing request complexity...")
                classification = self._classify_with_local_llm(request)
                
                category = classification.get('classification', 'UNCERTAIN')
                confidence = classification.get('confidence', 0)
                
                # Get model-specific confidence thresholds
                if HAS_MODEL_CONFIGS:
                    model = self.config.config['jeeves']['default_model']
                    thresholds = get_confidence_thresholds(model)
                    simple_threshold = thresholds['simple']
                    moderate_threshold = thresholds['moderate']
                else:
                    simple_threshold = 0.7
                    moderate_threshold = 0.8
                
                print(f"   Analysis: {category} (confidence: {confidence:.0%})")
                
                # Handle based on classification with model-specific thresholds
                if category == 'SIMPLE' and confidence >= simple_threshold:
                    # Try to handle locally
                    result = self._generate_local_response(request)
                    
                    # Check if response indicates uncertainty
                    if self.config.config['routing']['auto_fallback'] and self._is_uncertain_response(result):
                        self._print_routing_message('cloud', 'fallback_uncertainty', 
                                                    "Local LLM expressed uncertainty")
                        
                        result_dict = {
                            'destination': 'cloud',
                            'method': 'fallback_uncertainty',
                            'classification': classification,
                            'should_escalate': True
                        }
                        
                        if self.logger:
                            self.logger.end_session("[ESCALATED - Uncertainty]", 'ESCALATED')
                        
                        return result_dict
                    
                    self._print_routing_message('local', 'llm_classification')
                    
                    result_dict = {
                        'destination': 'local',
                        'method': 'llm_classification',
                        'classification': classification,
                        'result': result,
                        'should_escalate': False
                    }
                    
                    if self.logger:
                        self.logger.end_session(result, 'LOCAL')
                    
                    return result_dict
                
                elif category == 'MODERATE' and confidence >= moderate_threshold:
                    # Try local first, but be ready to escalate
                    result = self._generate_local_response(request)
                    
                    if len(result) < 50 or self._is_uncertain_response(result):
                        self._print_routing_message('cloud', 'fallback_incomplete',
                                                    "Response too brief or uncertain")
                        
                        result_dict = {
                            'destination': 'cloud',
                            'method': 'fallback_incomplete',
                            'classification': classification,
                            'should_escalate': True
                        }
                        
                        if self.logger:
                            self.logger.end_session("[ESCALATED - Incomplete]", 'ESCALATED')
                        
                        return result_dict
                    
                    self._print_routing_message('local', 'llm_classification')
                    
                    result_dict = {
                        'destination': 'local',
                        'method': 'llm_classification',
                        'classification': classification,
                        'result': result,
                        'should_escalate': False
                    }
                    
                    if self.logger:
                        self.logger.end_session(result, 'LOCAL')
                    
                    return result_dict
                
                else:
                    # COMPLEX or UNCERTAIN - go to cloud
                    reason = "Complex reasoning required" if category == 'COMPLEX' else "Uncertain classification"
                    self._print_routing_message('cloud', 'llm_classification', reason)
                    
                    result_dict = {
                        'destination': 'cloud',
                        'method': 'llm_classification',
                        'classification': classification,
                        'should_escalate': True
                    }
                    
                    if self.logger:
                        self.logger.end_session(f"[ESCALATED - {category}]", 'ESCALATED')
                    
                    return result_dict
            
            # Default: escalate to cloud
            self._print_routing_message('cloud', 'default', 'Default routing to primary AI')
            
            result_dict = {
                'destination': 'cloud',
                'method': 'default',
                'should_escalate': True
            }
            
            if self.logger:
                self.logger.end_session("[ESCALATED - Default]", 'ESCALATED')
            
            return result_dict
            
        except Exception as e:
            if self.logger:
                self.logger.log_error('ROUTING_ERROR', str(e))
                self.logger.end_session(f"[ERROR: {e}]", 'ERROR')
            raise
    
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
                        print(f"🤖 Jeeves → Primary AI: {result['method']}")
                        print("   [Request escalated to primary AI]")
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
                print("\n[Request would be sent to primary AI]")
            else:
                print(f"\n{result.get('result', 'No result')}")
                
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
