#!/usr/bin/env python3
"""
Model-Specific Configurations for Jeeves

Provides optimized prompts, parameters, and formatting for different LLM families.
Each model has different instruction formats, optimal parameters, and capabilities.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ModelFamily(Enum):
    """LLM model families with distinct characteristics"""
    QWEN = "qwen"           # Alibaba Qwen series (ChatML format)
    LLAMA = "llama"         # Meta Llama series
    PHI = "phi"             # Microsoft Phi series
    GEMMA = "gemma"         # Google Gemma series
    DEEPSEEK = "deepseek"   # DeepSeek series
    MISTRAL = "mistral"     # Mistral series
    MIXTRAL = "mixtral"     # Mixtral series
    CODELLAMA = "codellama" # CodeLlama series
    STARCODER = "starcoder" # StarCoder series
    UNKNOWN = "unknown"


@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    # Model identification
    name: str
    family: ModelFamily
    
    # Optimal generation parameters
    classification_temperature: float = 0.1
    response_temperature: float = 0.7
    classification_max_tokens: int = 10
    response_max_tokens: int = 512
    top_p: float = 0.9
    top_k: int = 40
    
    # Capabilities
    supports_system_prompt: bool = True
    context_window: int = 4096
    
    # Prompt templates
    classification_prompt_template: str = "default"
    response_prompt_template: str = "default"
    
    # Formatting
    chat_format: str = "default"  # "chatml", "llama-2", "alpaca", "vicuna", etc.
    stop_sequences: list = None
    
    # Routing preferences
    confidence_threshold_simple: float = 0.7
    confidence_threshold_moderate: float = 0.8
    
    def __post_init__(self):
        if self.stop_sequences is None:
            self.stop_sequences = []


# Model-specific prompt templates
CLASSIFICATION_PROMPTS = {
    "default": """You are a request classifier. Classify the following user request.

Request: "{request}"

Respond with EXACTLY one of these categories:
- SIMPLE: Basic shell commands, file operations, simple queries
- MODERATE: Multi-step local operations, code analysis, structured data
- COMPLEX: Design decisions, creative tasks, reasoning, analysis requiring deep thought

If you are uncertain or the request is unclear, respond with: UNCERTAIN

Your response must be ONLY the category word (SIMPLE, MODERATE, COMPLEX, or UNCERTAIN).

Classification:""",

    "qwen": """<|im_start|>system
You are a precise request classifier. Your task is to classify user requests into exactly one category.<|im_end|>
<|im_start|>user
Classify this request: "{request}"

Categories:
- SIMPLE: Basic shell commands, file operations, simple queries
- MODERATE: Multi-step local operations, code analysis
- COMPLEX: Design decisions, creative tasks, deep reasoning

Respond with ONLY one word: SIMPLE, MODERATE, COMPLEX, or UNCERTAIN<|im_end|>
<|im_start|>assistant
""",

    "llama": """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a request classifier. Classify user requests into categories.<|eot_id|><|start_header_id|>user<|end_header_id|>
Classify: "{request}"

Categories: SIMPLE, MODERATE, COMPLEX, UNCERTAIN

Respond with ONLY the category word.<|eot_id|><|start_header_id|>assistant<|end_header_id|>
""",

    "phi": """<|user|>
Classify this request into SIMPLE, MODERATE, COMPLEX, or UNCERTAIN:
"{request}"<|end|>
<|assistant|>
""",

    "gemma": """<start_of_turn>user
Classify this request: "{request}"

Choose one: SIMPLE, MODERATE, COMPLEX, UNCERTAIN<end_of_turn>
<start_of_turn>model
""",

    "deepseek": """You are a helpful assistant that classifies requests.

User: Classify: "{request}"
Respond with: SIMPLE, MODERATE, COMPLEX, or UNCERTAIN

Assistant:""",

    "minimal": """Request: {request}
Category (SIMPLE/MODERATE/COMPLEX/UNCERTAIN):""",
}


RESPONSE_PROMPTS = {
    "default": """You are Jeeves, a helpful assistant. Respond to the user's request concisely.

User: {request}

Jeeves:""",

    "qwen": """<|im_start|>system
You are Jeeves, a helpful local assistant. Provide concise, accurate responses.<|im_end|>
<|im_start|>user
{request}<|im_end|>
<|im_start|>assistant
""",

    "llama": """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are Jeeves, a helpful assistant.<|eot_id|><|start_header_id|>user<|end_header_id|>
{request}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
""",

    "phi": """<|user|>
{request}<|end|>
<|assistant|>
""",

    "gemma": """<start_of_turn>user
{request}<end_of_turn>
<start_of_turn>model
""",

    "deepseek": """User: {request}

Assistant:""",
}


# Model-specific configurations
MODEL_CONFIGS: Dict[str, ModelConfig] = {
    # Qwen models (Alibaba) - ChatML format
    "qwen2.5:0.5b": ModelConfig(
        name="qwen2.5:0.5b",
        family=ModelFamily.QWEN,
        classification_temperature=0.05,  # Very low for deterministic classification
        response_temperature=0.5,  # Lower for this small model
        classification_max_tokens=5,  # Very short response needed
        response_max_tokens=256,  # Smaller model, shorter responses
        context_window=32768,
        classification_prompt_template="qwen",
        response_prompt_template="qwen",
        confidence_threshold_simple=0.8,  # Higher threshold for small model
        confidence_threshold_moderate=0.85,
        stop_sequences=["<|im_end|>", "<|endoftext|>"],
    ),
    "qwen2.5:1.5b": ModelConfig(
        name="qwen2.5:1.5b",
        family=ModelFamily.QWEN,
        classification_temperature=0.1,
        response_temperature=0.7,
        classification_max_tokens=10,
        response_max_tokens=512,
        context_window=32768,
        classification_prompt_template="qwen",
        response_prompt_template="qwen",
        confidence_threshold_simple=0.7,
        confidence_threshold_moderate=0.8,
        stop_sequences=["<|im_end|>", "<|endoftext|>"],
    ),
    "qwen2.5:3b": ModelConfig(
        name="qwen2.5:3b",
        family=ModelFamily.QWEN,
        classification_temperature=0.1,
        response_temperature=0.7,
        classification_max_tokens=10,
        response_max_tokens=1024,
        context_window=32768,
        classification_prompt_template="qwen",
        response_prompt_template="qwen",
        confidence_threshold_simple=0.7,
        confidence_threshold_moderate=0.8,
        stop_sequences=["<|im_end|>", "<|endoftext|>"],
    ),
    "qwen2.5:7b": ModelConfig(
        name="qwen2.5:7b",
        family=ModelFamily.QWEN,
        classification_temperature=0.1,
        response_temperature=0.7,
        classification_max_tokens=10,
        response_max_tokens=2048,
        context_window=32768,
        classification_prompt_template="qwen",
        response_prompt_template="qwen",
        confidence_threshold_simple=0.7,
        confidence_threshold_moderate=0.8,
        stop_sequences=["<|im_end|>", "<|endoftext|>"],
    ),
    
    # Llama models (Meta)
    "llama3.2:1b": ModelConfig(
        name="llama3.2:1b",
        family=ModelFamily.LLAMA,
        classification_temperature=0.1,
        response_temperature=0.6,
        classification_max_tokens=10,
        response_max_tokens=512,
        context_window=8192,
        classification_prompt_template="llama",
        response_prompt_template="llama",
        confidence_threshold_simple=0.75,
        confidence_threshold_moderate=0.85,
        stop_sequences=["<|eot_id|>", "<|end_of_text|>"],
    ),
    "llama3.2:3b": ModelConfig(
        name="llama3.2:3b",
        family=ModelFamily.LLAMA,
        classification_temperature=0.1,
        response_temperature=0.7,
        classification_max_tokens=10,
        response_max_tokens=1024,
        context_window=8192,
        classification_prompt_template="llama",
        response_prompt_template="llama",
        confidence_threshold_simple=0.7,
        confidence_threshold_moderate=0.8,
        stop_sequences=["<|eot_id|>", "<|end_of_text|>"],
    ),
    "llama3.2:8b": ModelConfig(
        name="llama3.2:8b",
        family=ModelFamily.LLAMA,
        classification_temperature=0.1,
        response_temperature=0.7,
        classification_max_tokens=10,
        response_max_tokens=2048,
        context_window=8192,
        classification_prompt_template="llama",
        response_prompt_template="llama",
        confidence_threshold_simple=0.7,
        confidence_threshold_moderate=0.8,
        stop_sequences=["<|eot_id|>", "<|end_of_text|>"],
    ),
    
    # Phi models (Microsoft)
    "phi3:mini": ModelConfig(
        name="phi3:mini",
        family=ModelFamily.PHI,
        classification_temperature=0.1,
        response_temperature=0.6,
        classification_max_tokens=10,
        response_max_tokens=512,
        context_window=4096,
        classification_prompt_template="phi",
        response_prompt_template="phi",
        confidence_threshold_simple=0.75,
        confidence_threshold_moderate=0.85,
        stop_sequences=["<|end|>", "<|user|>"],
    ),
    "phi3:small": ModelConfig(
        name="phi3:small",
        family=ModelFamily.PHI,
        classification_temperature=0.1,
        response_temperature=0.7,
        classification_max_tokens=10,
        response_max_tokens=1024,
        context_window=8192,
        classification_prompt_template="phi",
        response_prompt_template="phi",
        confidence_threshold_simple=0.7,
        confidence_threshold_moderate=0.8,
        stop_sequences=["<|end|>", "<|user|>"],
    ),
    
    # Gemma models (Google)
    "gemma2:2b": ModelConfig(
        name="gemma2:2b",
        family=ModelFamily.GEMMA,
        classification_temperature=0.1,
        response_temperature=0.7,
        classification_max_tokens=10,
        response_max_tokens=512,
        context_window=4096,
        classification_prompt_template="gemma",
        response_prompt_template="gemma",
        confidence_threshold_simple=0.75,
        confidence_threshold_moderate=0.85,
        stop_sequences=["<end_of_turn>"],
    ),
    "gemma2:4b": ModelConfig(
        name="gemma2:4b",
        family=ModelFamily.GEMMA,
        classification_temperature=0.1,
        response_temperature=0.7,
        classification_max_tokens=10,
        response_max_tokens=1024,
        context_window=8192,
        classification_prompt_template="gemma",
        response_prompt_template="gemma",
        confidence_threshold_simple=0.7,
        confidence_threshold_moderate=0.8,
        stop_sequences=["<end_of_turn>"],
    ),
    
    # DeepSeek models
    "deepseek-r1:1.5b": ModelConfig(
        name="deepseek-r1:1.5b",
        family=ModelFamily.DEEPSEEK,
        classification_temperature=0.1,
        response_temperature=0.6,
        classification_max_tokens=10,
        response_max_tokens=512,
        context_window=32768,
        classification_prompt_template="deepseek",
        response_prompt_template="deepseek",
        confidence_threshold_simple=0.75,
        confidence_threshold_moderate=0.85,
        stop_sequences=["</s>"],
    ),
    "deepseek-r1:7b": ModelConfig(
        name="deepseek-r1:7b",
        family=ModelFamily.DEEPSEEK,
        classification_temperature=0.1,
        response_temperature=0.7,
        classification_max_tokens=10,
        response_max_tokens=2048,
        context_window=32768,
        classification_prompt_template="deepseek",
        response_prompt_template="deepseek",
        confidence_threshold_simple=0.7,
        confidence_threshold_moderate=0.8,
        stop_sequences=["</s>"],
    ),
}


def get_model_config(model_name: str) -> ModelConfig:
    """
    Get configuration for a specific model.
    
    Args:
        model_name: Name of the model (e.g., "qwen2.5:1.5b")
        
    Returns:
        ModelConfig for the model, or default config if not found
    """
    # Exact match
    if model_name in MODEL_CONFIGS:
        return MODEL_CONFIGS[model_name]
    
    # Try to match by family prefix
    for name, config in MODEL_CONFIGS.items():
        if model_name.startswith(name.split(':')[0]):
            return config
    
    # Return default config
    return ModelConfig(
        name=model_name,
        family=ModelFamily.UNKNOWN,
        classification_prompt_template="default",
        response_prompt_template="default",
    )


def format_classification_prompt(model_name: str, request: str) -> str:
    """
    Get classification prompt formatted for the specific model.
    
    Args:
        model_name: Name of the model
        request: User request to classify
        
    Returns:
        Formatted prompt string
    """
    config = get_model_config(model_name)
    template = CLASSIFICATION_PROMPTS.get(
        config.classification_prompt_template,
        CLASSIFICATION_PROMPTS["default"]
    )
    return template.format(request=request)


def format_response_prompt(model_name: str, request: str) -> str:
    """
    Get response prompt formatted for the specific model.
    
    Args:
        model_name: Name of the model
        request: User request
        
    Returns:
        Formatted prompt string
    """
    config = get_model_config(model_name)
    template = RESPONSE_PROMPTS.get(
        config.response_prompt_template,
        RESPONSE_PROMPTS["default"]
    )
    return template.format(request=request)


def get_classification_params(model_name: str) -> Dict[str, Any]:
    """
    Get optimal parameters for classification request.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Dictionary of parameters for Ollama API
    """
    config = get_model_config(model_name)
    return {
        "temperature": config.classification_temperature,
        "num_predict": config.classification_max_tokens,
        "top_p": config.top_p,
        "top_k": config.top_k,
        "stop": config.stop_sequences,
    }


def get_response_params(model_name: str) -> Dict[str, Any]:
    """
    Get optimal parameters for response generation.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Dictionary of parameters for Ollama API
    """
    config = get_model_config(model_name)
    return {
        "temperature": config.response_temperature,
        "num_predict": config.response_max_tokens,
        "top_p": config.top_p,
        "top_k": config.top_k,
        "stop": config.stop_sequences,
    }


def get_confidence_thresholds(model_name: str) -> Dict[str, float]:
    """
    Get model-specific confidence thresholds for routing decisions.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Dictionary with 'simple' and 'moderate' thresholds
    """
    config = get_model_config(model_name)
    return {
        "simple": config.confidence_threshold_simple,
        "moderate": config.confidence_threshold_moderate,
    }


def detect_model_family(model_name: str) -> ModelFamily:
    """
    Detect the family of a model based on its name.
    
    Args:
        model_name: Name of the model
        
    Returns:
        ModelFamily enum
    """
    model_lower = model_name.lower()
    
    if "qwen" in model_lower:
        return ModelFamily.QWEN
    elif "llama" in model_lower:
        return ModelFamily.LLAMA
    elif "phi" in model_lower:
        return ModelFamily.PHI
    elif "gemma" in model_lower:
        return ModelFamily.GEMMA
    elif "deepseek" in model_lower:
        return ModelFamily.DEEPSEEK
    elif "mistral" in model_lower:
        if "mixtral" in model_lower:
            return ModelFamily.MIXTRAL
        return ModelFamily.MISTRAL
    elif "codellama" in model_lower or "code-llama" in model_lower:
        return ModelFamily.CODELLAMA
    elif "starcoder" in model_lower:
        return ModelFamily.STARCODER
    else:
        return ModelFamily.UNKNOWN


# Capability ratings for routing decisions
MODEL_CAPABILITIES = {
    # Ultra-small models - limited capabilities
    "qwen2.5:0.5b": {"classification": 0.6, "response": 0.5, "reasoning": 0.3},
    
    # Small models - basic capabilities
    "qwen2.5:1.5b": {"classification": 0.8, "response": 0.7, "reasoning": 0.5},
    "llama3.2:1b": {"classification": 0.7, "response": 0.6, "reasoning": 0.4},
    "phi3:mini": {"classification": 0.75, "response": 0.7, "reasoning": 0.5},
    "deepseek-r1:1.5b": {"classification": 0.75, "response": 0.7, "reasoning": 0.6},
    "gemma2:2b": {"classification": 0.75, "response": 0.7, "reasoning": 0.5},
    
    # Medium models - good capabilities
    "qwen2.5:3b": {"classification": 0.85, "response": 0.8, "reasoning": 0.7},
    "llama3.2:3b": {"classification": 0.85, "response": 0.8, "reasoning": 0.7},
    "phi3:small": {"classification": 0.85, "response": 0.8, "reasoning": 0.7},
    "gemma2:4b": {"classification": 0.85, "response": 0.8, "reasoning": 0.7},
    
    # Large models - excellent capabilities
    "qwen2.5:7b": {"classification": 0.9, "response": 0.9, "reasoning": 0.85},
    "llama3.2:8b": {"classification": 0.9, "response": 0.9, "reasoning": 0.85},
    "deepseek-r1:7b": {"classification": 0.9, "response": 0.9, "reasoning": 0.9},
}


def get_model_capabilities(model_name: str) -> Dict[str, float]:
    """
    Get capability ratings for a model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Dictionary with capability ratings (0.0-1.0)
    """
    # Exact match
    if model_name in MODEL_CAPABILITIES:
        return MODEL_CAPABILITIES[model_name]
    
    # Try to match by base name
    base_name = model_name.split(':')[0]
    for name, caps in MODEL_CAPABILITIES.items():
        if name.startswith(base_name) or base_name in name:
            return caps
    
    # Default conservative capabilities
    return {"classification": 0.7, "response": 0.6, "reasoning": 0.5}


if __name__ == "__main__":
    # Demo
    print("=== Model Configuration Demo ===\n")
    
    test_models = [
        "qwen2.5:1.5b",
        "llama3.2:3b",
        "phi3:mini",
        "gemma2:2b",
        "deepseek-r1:1.5b",
        "unknown-model:7b",
    ]
    
    for model in test_models:
        print(f"Model: {model}")
        config = get_model_config(model)
        print(f"  Family: {config.family.value}")
        print(f"  Classification temp: {config.classification_temperature}")
        print(f"  Response temp: {config.response_temperature}")
        
        prompt = format_classification_prompt(model, "list files in directory")
        print(f"  Prompt preview: {prompt[:80]}...")
        
        caps = get_model_capabilities(model)
        print(f"  Capabilities: {caps}")
        print()
