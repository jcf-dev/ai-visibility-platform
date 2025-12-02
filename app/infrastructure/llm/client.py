import asyncio
import random
from typing import Protocol, Dict, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_exception,
)
import httpx
from app.infrastructure.config import settings


def is_retryable_error(exception):
    """
    Determines if an exception should trigger a retry.
    We avoid retrying on 400/401/403/404 or OpenAI quota errors.
    """
    if isinstance(exception, httpx.HTTPStatusError):
        status = exception.response.status_code
        if status in [400, 401, 403, 404]:
            return False
        if status == 429:
            # Check for OpenAI quota error which is not transient
            if "insufficient_quota" in exception.response.text:
                return False
    return True


class LLMResponse:
    def __init__(self, text: str, latency_ms: float, metadata: Dict[str, Any] = None):
        self.text = text
        self.latency_ms = latency_ms
        self.metadata = metadata or {}


class LLMProvider(Protocol):
    async def generate(self, prompt: str, model: str) -> LLMResponse: ...

    async def list_models(self) -> list[str]: ...


class MockLLMProvider:
    """
    A mock provider that returns random responses containing some of the brands
    (if we knew them, but here it just returns generic text).
    To make it useful for testing visibility, we might want to inject behavior,
    but for now let's just return random text that MIGHT contain brands.
    """

    async def list_models(self) -> list[str]:
        return ["mock-model", "mock-gpt-4", "mock-gemini"]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    async def generate(self, prompt: str, model: str) -> LLMResponse:
        # Simulate network latency
        latency = random.uniform(100, 1500)  # ms
        await asyncio.sleep(latency / 1000)

        # Simulate occasional failure
        if random.random() < 0.05:
            raise Exception("Random network glitch in Mock LLM")

        # Generate a response that might mention common tech brands
        # In a real mock, we might want to ensure specific brands from the run
        # are mentioned for testing purposes.
        possible_brands = ["Acme", "Contoso", "Globex", "Soylent Corp", "Initech"]
        mentioned = random.sample(possible_brands, k=random.randint(0, 3))

        response_text = (
            f"Here is a list of top companies for {prompt}: "
            + ", ".join(mentioned)
            + "."
        )

        return LLMResponse(
            text=response_text,
            latency_ms=latency,
            metadata={"provider": "mock", "simulated_version": "1.0"},
        )


class OpenAILLMProvider:
    """
    A real implementation for OpenAI.
    Requires OPENAI_API_KEY in settings.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.models_url = "https://api.openai.com/v1/models"

    async def list_models(self) -> list[str]:
        if not self.api_key:
            return []

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.models_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()
                # Sort models by id for easier reading
                models = sorted(data.get("data", []), key=lambda x: x["id"])
                return [m["id"] for m in models]
            except Exception:
                return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
        & retry_if_exception(is_retryable_error),
        reraise=True,
    )
    async def generate(self, prompt: str, model: str) -> LLMResponse:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set")

        start_time = asyncio.get_event_loop().time()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                },
                timeout=settings.REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()

            end_time = asyncio.get_event_loop().time()
            latency_ms = (end_time - start_time) * 1000

            text = data["choices"][0]["message"]["content"]

            return LLMResponse(
                text=text, latency_ms=latency_ms, metadata={"usage": data.get("usage")}
            )


class GeminiLLMProvider:
    """
    Implementation for Google Gemini API.
    Requires GEMINI_API_KEY in settings.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        # Note: The base URL for generation is slightly different than listing models
        # But we construct the full URL in generate()
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def list_models(self) -> list[str]:
        if not self.api_key:
            return []

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}?key={self.api_key}", timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                models = []
                for model in data.get("models", []):
                    methods = model.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        name = model.get("name")
                        if name.startswith("models/"):
                            name = name.replace("models/", "")
                        models.append(name)
                return models
            except Exception:
                return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
        & retry_if_exception(is_retryable_error),
        reraise=True,
    )
    async def generate(self, prompt: str, model: str) -> LLMResponse:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set")

        # Default to gemini-2.0-flash if just "gemini" is passed or if model is generic
        if model == "gemini" or not model:
            model = "gemini-2.0-flash"

        # Ensure we don't double-prefix if user passed "models/gemini..."
        # The API expects "models/gemini-2.0-flash:generateContent"
        # But our base_url is ".../models"
        # So we want the URL to be ".../models/gemini-2.0-flash:generateContent"

        # If the user passed "models/gemini-2.0-flash", we strip "models/"
        # because we append it to base_url which ends in "/models"
        if model.startswith("models/"):
            model = model.replace("models/", "")

        url = f"{self.base_url}/{model}:generateContent?key={self.api_key}"

        start_time = asyncio.get_event_loop().time()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=settings.REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()

            end_time = asyncio.get_event_loop().time()
            latency_ms = (end_time - start_time) * 1000

            try:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                text = ""
                if "promptFeedback" in data:
                    text = f"[Blocked: {data['promptFeedback']}]"

            return LLMResponse(
                text=text,
                latency_ms=latency_ms,
                metadata={"usage": data.get("usageMetadata")},
            )


class AnthropicLLMProvider:
    """
    Implementation for Anthropic API.
    Requires ANTHROPIC_API_KEY.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.base_url = "https://api.anthropic.com/v1/messages"

    async def list_models(self) -> list[str]:
        if not self.api_key:
            return []
        # Anthropic doesn't have a public list models endpoint that is easily accessible
        # without an SDK or scraping, but we can return common ones if key is present.
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
        & retry_if_exception(is_retryable_error),
        reraise=True,
    )
    async def generate(self, prompt: str, model: str) -> LLMResponse:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")

        start_time = asyncio.get_event_loop().time()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1024,
                },
                timeout=settings.REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()

            end_time = asyncio.get_event_loop().time()
            latency_ms = (end_time - start_time) * 1000

            text = data["content"][0]["text"]

            return LLMResponse(
                text=text, latency_ms=latency_ms, metadata={"usage": data.get("usage")}
            )


class MultiProviderRouter:
    """
    Routes requests to the appropriate provider based on model name or configuration.
    """

    def __init__(self, api_keys: Dict[str, str] = None):
        self.api_keys = api_keys or {}

        # Initialize providers with keys if available
        self.providers = {
            "openai": OpenAILLMProvider(api_key=self.api_keys.get("openai")),
            "gemini": GeminiLLMProvider(api_key=self.api_keys.get("gemini")),
            "anthropic": AnthropicLLMProvider(api_key=self.api_keys.get("anthropic")),
            "mock": MockLLMProvider(),
        }
        self.default_provider = settings.LLM_PROVIDER

    async def generate(self, prompt: str, model: str) -> LLMResponse:
        # 1. Route based on model name prefixes
        if model.startswith("gpt-") or model.startswith("o1-"):
            return await self.providers["openai"].generate(prompt, model)
        elif model.startswith("gemini"):
            return await self.providers["gemini"].generate(prompt, model)
        elif model.startswith("claude"):
            return await self.providers["anthropic"].generate(prompt, model)
        elif model.startswith("mock"):
            return await self.providers["mock"].generate(prompt, model)

        # 2. Fallback to configured default provider if it matches a known provider
        if self.default_provider in self.providers and self.default_provider != "auto":
            return await self.providers[self.default_provider].generate(prompt, model)

        # 3. If auto and no match, raise error
        raise ValueError(f"Could not determine LLM provider for model '{model}'")

    async def list_models(self) -> Dict[str, list[str]]:
        results = {}
        # Run in parallel
        tasks = []
        names = []

        for name, provider in self.providers.items():
            # Only list models if provider has a key (or is mock)
            if name == "mock" or (hasattr(provider, "api_key") and provider.api_key):
                if hasattr(provider, "list_models"):
                    names.append(name)
                    tasks.append(provider.list_models())

        # If no keys provided at all, return mock models as fallback?
        # "If all are not supplied, use mock."
        has_keys = any(
            p.api_key
            for n, p in self.providers.items()
            if n != "mock" and hasattr(p, "api_key")
        )
        if not has_keys and not tasks:
            # If no keys are set, we might want to show mock models if not already shown
            if "mock" not in names:
                names.append("mock")
                tasks.append(self.providers["mock"].list_models())

        if tasks:
            lists = await asyncio.gather(*tasks, return_exceptions=True)
            for name, result in zip(names, lists):
                if isinstance(result, list):
                    results[name] = result
                else:
                    results[name] = []

        return results


def get_llm_provider(api_keys: Dict[str, str] = None) -> LLMProvider:
    # Always return the router, which handles the logic
    return MultiProviderRouter(api_keys=api_keys)
