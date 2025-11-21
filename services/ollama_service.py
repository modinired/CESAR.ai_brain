"""
CESAR.ai Ollama Service

Provides interface to local Ollama LLM models.

Supported Models:
- qwen2.5-coder:7b (Code generation, debugging, refactoring)
- llama3:8b (General tasks, chat, analysis)

Features:
- Async generation with streaming support
- Health checks and model availability monitoring
- Automatic error handling and retry logic
- Performance monitoring and caching

Author: CESAR.ai Development Team
Date: November 19, 2025
"""

import asyncio
import json
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import UUID, uuid4

import aiohttp
from pydantic import BaseModel


class LLMResponse(BaseModel):
    """Response from LLM generation"""
    content: str
    tokens_input: int
    tokens_output: int
    model: str
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = {}


class OllamaHealthCheck(BaseModel):
    """Ollama service health status"""
    status: str  # 'online', 'offline', 'degraded'
    version: Optional[str] = None
    models_available: List[str] = []
    response_time_ms: Optional[int] = None
    error: Optional[str] = None


class OllamaService:
    """
    Service for interacting with local Ollama LLM models.

    Provides:
    - Model generation (synchronous and streaming)
    - Health monitoring
    - Model management (list, pull, delete)
    - Error handling with automatic retry
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout_seconds: int = 120,
        max_retries: int = 2,
    ):
        """
        Initialize Ollama service.

        Args:
            base_url: Ollama server URL (default: http://localhost:11434)
            timeout_seconds: Request timeout (default: 120s for large generations)
            max_retries: Max retry attempts on failure (default: 2)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self.max_retries = max_retries

        # Cache for model info
        self._model_cache: Dict[str, Dict[str, Any]] = {}

    async def generate(
        self,
        model: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        system_prompt: Optional[str] = None,
        stop_sequences: Optional[List[str]] = None,
    ) -> LLMResponse:
        """
        Generate completion from Ollama model.

        Args:
            model: Model name (e.g., 'qwen2.5-coder:7b', 'llama3:8b')
            prompt: Input prompt
            max_tokens: Maximum tokens to generate (default: model's max)
            temperature: Sampling temperature (0.0-1.0, default: 0.7)
            top_p: Nucleus sampling threshold (default: 0.9)
            system_prompt: Optional system/instruction prompt
            stop_sequences: Optional list of stop sequences

        Returns:
            LLMResponse with generated content and metadata

        Example:
            >>> ollama = OllamaService()
            >>> response = await ollama.generate(
            ...     model="qwen2.5-coder:7b",
            ...     prompt="Write a Python function to calculate fibonacci numbers",
            ...     max_tokens=500,
            ... )
            >>> print(response.content)
        """
        start_time = datetime.now()

        # Build request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
            },
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        if system_prompt:
            payload["system"] = system_prompt

        if stop_sequences:
            payload["options"]["stop"] = stop_sequences

        # Execute with retry logic
        for attempt in range(self.max_retries + 1):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(
                        f"{self.base_url}/api/generate", json=payload
                    ) as response:
                        if response.status == 200:
                            data = await response.json()

                            duration_ms = int(
                                (datetime.now() - start_time).total_seconds() * 1000
                            )

                            # Extract response
                            return LLMResponse(
                                content=data.get("response", ""),
                                tokens_input=data.get("prompt_eval_count", 0),
                                tokens_output=data.get("eval_count", 0),
                                model=model,
                                finish_reason=data.get("done_reason"),
                                metadata={
                                    "duration_ms": duration_ms,
                                    "total_duration_ns": data.get("total_duration"),
                                    "load_duration_ns": data.get("load_duration"),
                                    "prompt_eval_duration_ns": data.get(
                                        "prompt_eval_duration"
                                    ),
                                    "eval_duration_ns": data.get("eval_duration"),
                                },
                            )
                        else:
                            error_text = await response.text()
                            if attempt < self.max_retries:
                                # Retry after delay
                                await asyncio.sleep(2 ** attempt)
                                continue
                            else:
                                raise Exception(
                                    f"Ollama API error {response.status}: {error_text}"
                                )

            except aiohttp.ClientError as e:
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise Exception(f"Ollama connection error: {str(e)}")

        raise Exception("Max retries exceeded")

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Generate completion with streaming.

        Yields chunks of text as they are generated.

        Args:
            model: Model name
            prompt: Input prompt
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            top_p: Nucleus sampling
            system_prompt: Optional system prompt

        Yields:
            Text chunks as they are generated

        Example:
            >>> async for chunk in ollama.generate_stream(
            ...     model="llama3:8b",
            ...     prompt="Explain quantum computing",
            ... ):
            ...     print(chunk, end="", flush=True)
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
            },
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        if system_prompt:
            payload["system"] = system_prompt

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(
                f"{self.base_url}/api/generate", json=payload
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line:
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    yield data["response"]

                                if data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    error = await response.text()
                    raise Exception(f"Ollama streaming error {response.status}: {error}")

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Chat completion (multi-turn conversation).

        Args:
            model: Model name
            messages: List of message dicts with 'role' and 'content'
                     [{"role": "user", "content": "Hello"}, ...]
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            LLMResponse with assistant's reply

        Example:
            >>> response = await ollama.chat(
            ...     model="llama3:8b",
            ...     messages=[
            ...         {"role": "user", "content": "What is Python?"},
            ...         {"role": "assistant", "content": "Python is a programming language..."},
            ...         {"role": "user", "content": "What are its main features?"},
            ...     ],
            ... )
        """
        start_time = datetime.now()

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(
                f"{self.base_url}/api/chat", json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    duration_ms = int(
                        (datetime.now() - start_time).total_seconds() * 1000
                    )

                    message = data.get("message", {})

                    return LLMResponse(
                        content=message.get("content", ""),
                        tokens_input=data.get("prompt_eval_count", 0),
                        tokens_output=data.get("eval_count", 0),
                        model=model,
                        finish_reason=data.get("done_reason"),
                        metadata={
                            "duration_ms": duration_ms,
                            "role": message.get("role", "assistant"),
                        },
                    )
                else:
                    error = await response.text()
                    raise Exception(f"Ollama chat error {response.status}: {error}")

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List all available Ollama models.

        Returns:
            List of model dictionaries with name, size, modified date, etc.

        Example:
            >>> models = await ollama.list_models()
            >>> for model in models:
            ...     print(f"{model['name']}: {model['size_gb']:.1f} GB")
        """
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = []

                    for model in data.get("models", []):
                        models.append({
                            "name": model.get("name"),
                            "size_bytes": model.get("size", 0),
                            "size_gb": model.get("size", 0) / (1024 ** 3),
                            "modified_at": model.get("modified_at"),
                            "digest": model.get("digest"),
                            "details": model.get("details", {}),
                        })

                    # Cache model info
                    for model in models:
                        self._model_cache[model["name"]] = model

                    return models
                else:
                    return []

    async def pull_model(self, model_name: str) -> bool:
        """
        Pull (download) a model from Ollama library.

        Args:
            model_name: Model to pull (e.g., 'qwen2.5-coder:7b')

        Returns:
            True if successful, False otherwise

        Example:
            >>> success = await ollama.pull_model("llama3:8b")
            >>> if success:
            ...     print("Model downloaded successfully")
        """
        payload = {"name": model_name, "stream": False}

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=600)
            ) as session:  # 10 min timeout for download
                async with session.post(
                    f"{self.base_url}/api/pull", json=payload
                ) as response:
                    if response.status == 200:
                        # Refresh model cache
                        await self.list_models()
                        return True
                    else:
                        return False
        except Exception:
            return False

    async def delete_model(self, model_name: str) -> bool:
        """
        Delete a model from Ollama.

        Args:
            model_name: Model to delete

        Returns:
            True if successful

        Example:
            >>> await ollama.delete_model("old-model:latest")
        """
        payload = {"name": model_name}

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.delete(
                    f"{self.base_url}/api/delete", json=payload
                ) as response:
                    if response.status == 200:
                        # Remove from cache
                        self._model_cache.pop(model_name, None)
                        return True
                    else:
                        return False
        except Exception:
            return False

    async def check_health(self) -> OllamaHealthCheck:
        """
        Check Ollama service health.

        Returns:
            OllamaHealthCheck with status and available models

        Example:
            >>> health = await ollama.check_health()
            >>> if health.status == 'online':
            ...     print(f"Ollama online with {len(health.models_available)} models")
            >>> else:
            ...     print(f"Ollama offline: {health.error}")
        """
        start_time = datetime.now()

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5)
            ) as session:
                # Check version endpoint
                async with session.get(f"{self.base_url}/api/version") as response:
                    if response.status == 200:
                        version_data = await response.json()
                        response_time_ms = int(
                            (datetime.now() - start_time).total_seconds() * 1000
                        )

                        # Get available models
                        models = await self.list_models()
                        model_names = [m["name"] for m in models]

                        return OllamaHealthCheck(
                            status="online",
                            version=version_data.get("version"),
                            models_available=model_names,
                            response_time_ms=response_time_ms,
                        )
                    else:
                        return OllamaHealthCheck(
                            status="degraded",
                            error=f"Unexpected status code: {response.status}",
                        )

        except aiohttp.ClientConnectorError:
            return OllamaHealthCheck(
                status="offline",
                error="Cannot connect to Ollama server. Is it running?",
            )
        except asyncio.TimeoutError:
            return OllamaHealthCheck(
                status="degraded", error="Ollama server timeout (>5s)"
            )
        except Exception as e:
            return OllamaHealthCheck(status="offline", error=str(e))

    async def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific model.

        Args:
            model_name: Model to query

        Returns:
            Model info dict or None if not found

        Example:
            >>> info = await ollama.get_model_info("qwen2.5-coder:7b")
            >>> print(f"Context window: {info['context_length']} tokens")
        """
        payload = {"name": model_name}

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/show", json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "name": model_name,
                            "parameters": data.get("parameters"),
                            "template": data.get("template"),
                            "details": data.get("details", {}),
                            "model_info": data.get("model_info", {}),
                        }
                    else:
                        return None
        except Exception:
            return None

    async def embeddings(
        self, model: str, text: str
    ) -> Optional[List[float]]:
        """
        Generate embeddings for text.

        Args:
            model: Model name (must support embeddings)
            text: Text to embed

        Returns:
            List of embedding floats, or None on error

        Example:
            >>> embedding = await ollama.embeddings(
            ...     model="llama3:8b",
            ...     text="This is a sample sentence",
            ... )
            >>> print(f"Embedding dimension: {len(embedding)}")
        """
        payload = {"model": model, "prompt": text}

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/embeddings", json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("embedding")
                    else:
                        return None
        except Exception:
            return None


# Singleton instance
_ollama_instance: Optional[OllamaService] = None


def get_ollama_service(
    base_url: str = "http://localhost:11434",
) -> OllamaService:
    """
    Get singleton Ollama service instance.

    Args:
        base_url: Ollama server URL

    Returns:
        OllamaService instance

    Example:
        >>> ollama = get_ollama_service()
        >>> health = await ollama.check_health()
    """
    global _ollama_instance

    if _ollama_instance is None:
        _ollama_instance = OllamaService(base_url=base_url)

    return _ollama_instance
