# coding=utf-8
"""
AI client module

Unified AI model interface based on LiteLLM
Supports 100+ AI providers (OpenAI, DeepSeek, Gemini, Claude, domestic models, etc.)
"""

import os
from typing import Any, Dict, List

from litellm import completion


class AIClient:
    """Unified AI client (based on LiteLLM)"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize AI client

        Args:
            config: AI configuration dictionary
                - MODEL: model identification (format: provider/model_name)
                - API_KEY: API key
                - API_BASE: API base URL (optional)
                - TEMPERATURE: sampling temperature
                - MAX_TOKENS: Maximum number of generated tokens
                - TIMEOUT: request timeout (seconds)
                - NUM_RETRIES: Number of retries (optional)
                - FALLBACK_MODELS: list of alternative models (optional)
        """
        self.model = config.get("MODEL", "deepseek/deepseek-chat")
        self.api_key = config.get("API_KEY") or os.environ.get("AI_API_KEY", "")
        self.api_base = config.get("API_BASE", "")
        self.temperature = config.get("TEMPERATURE", 1.0)
        self.max_tokens = config.get("MAX_TOKENS", 5000)
        self.timeout = config.get("TIMEOUT", 120)
        self.num_retries = config.get("NUM_RETRIES", 2)
        self.fallback_models = config.get("FALLBACK_MODELS", [])

    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Call an AI model to have a conversation

        Args:
            messages: message list, format: [{"role": "system/user/assistant", "content": "..."}]
            **kwargs: additional parameters, which will override the default configuration

        Returns:
            str: AI response content

        Raises:
            Exception: Exception thrown when API call fails
        """
        # Build request parameters
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "timeout": kwargs.get("timeout", self.timeout),
            "num_retries": kwargs.get("num_retries", self.num_retries),
        }

        #Add API Key
        if self.api_key:
            params["api_key"] = self.api_key

        # Add API Base (if configured)
        if self.api_base:
            params["api_base"] = self.api_base

        # Add max_tokens (if configured and not 0)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        if max_tokens and max_tokens > 0:
            params["max_tokens"] = max_tokens

        #Add fallback model (if configured)
        if self.fallback_models:
            params["fallbacks"] = self.fallback_models

        #Incorporate other additional parameters
        for key, value in kwargs.items():
            if key not in params:
                params[key] = value

        # Bật stream để tương thích với 9router (luôn trả về định dạng chunk streaming)
        params["stream"] = True

        # Call LiteLLM
        response = completion(**params)

        # Extract response content (xử lý stream)
        content = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content += chunk.choices[0].delta.content
                
        return content or ""

    def validate_config(self) -> tuple[bool, str]:
        """
        Verify that the configuration is valid

        Returns:
            tuple: (valid, error message)
        """
        if not self.model:
            return False, "AI model not configured (model)"

        if not self.api_key:
            return False, "AI API Key is not configured, please set it in config.yaml or environment variable AI_API_KEY"

        # Verify model format (should contain provider/model)
        if "/" not in self.model:
            return False, f"Model format error: {self.model}, should be in 'provider/model' format (such as 'deepseek/deepseek-chat')"

        return True, ""
