import asyncio
import random
from typing import Protocol, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
from app.infrastructure.config import settings

class LLMResponse:
    def __init__(self, text: str, latency_ms: float, metadata: Dict[str, Any] = None):
        self.text = text
        self.latency_ms = latency_ms
        self.metadata = metadata or {}

class LLMProvider(Protocol):
    async def generate(self, prompt: str, model: str) -> LLMResponse:
        ...

class MockLLMProvider:
    """
    A mock provider that returns random responses containing some of the brands 
    (if we knew them, but here it just returns generic text).
    To make it useful for testing visibility, we might want to inject behavior, 
    but for now let's just return random text that MIGHT contain brands.
    """
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate(self, prompt: str, model: str) -> LLMResponse:
        # Simulate network latency
        latency = random.uniform(100, 1500) # ms
        await asyncio.sleep(latency / 1000)
        
        # Simulate occasional failure
        if random.random() < 0.05:
            raise Exception("Random network glitch in Mock LLM")

        # Generate a response that might mention common tech brands
        # In a real mock, we might want to ensure specific brands from the run are mentioned
        # for testing purposes.
        possible_brands = ["Acme", "Contoso", "Globex", "Soylent Corp", "Initech"]
        mentioned = random.sample(possible_brands, k=random.randint(0, 3))
        
        response_text = f"Here is a list of top companies for {prompt}: " + ", ".join(mentioned) + "."
        
        return LLMResponse(
            text=response_text,
            latency_ms=latency,
            metadata={"provider": "mock", "simulated_version": "1.0"}
        )

class OpenAILLMProvider:
    """
    A real implementation for OpenAI.
    Requires OPENAI_API_KEY in settings.
    """
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1/chat/completions"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate(self, prompt: str, model: str) -> LLMResponse:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set")

        start_time = asyncio.get_event_loop().time()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                },
                timeout=settings.REQUEST_TIMEOUT_SECONDS
            )
            response.raise_for_status()
            data = response.json()
            
            end_time = asyncio.get_event_loop().time()
            latency_ms = (end_time - start_time) * 1000
            
            text = data["choices"][0]["message"]["content"]
            
            return LLMResponse(
                text=text,
                latency_ms=latency_ms,
                metadata={"usage": data.get("usage")}
            )

class GeminiLLMProvider:
    """
    Implementation for Google Gemini API.
    Requires GEMINI_API_KEY in settings.
    """
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate(self, prompt: str, model: str) -> LLMResponse:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set")

        # Default to gemini-pro if just "gemini" is passed or if model is generic
        if model == "gemini" or not model:
            model = "gemini-1.5-flash"
            
        url = f"{self.base_url}/{model}:generateContent?key={self.api_key}"
        
        start_time = asyncio.get_event_loop().time()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}]
                },
                timeout=settings.REQUEST_TIMEOUT_SECONDS
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
                metadata={"usage": data.get("usageMetadata")}
            )

class MultiProviderRouter:
    """
    Routes requests to the appropriate provider based on model name or configuration.
    """
    def __init__(self):
        self.providers = {
            "openai": OpenAILLMProvider(),
            "gemini": GeminiLLMProvider(),
            "mock": MockLLMProvider()
        }
        self.default_provider = settings.LLM_PROVIDER

    async def generate(self, prompt: str, model: str) -> LLMResponse:
        # 1. Route based on model name prefixes
        if model.startswith("gpt-") or model.startswith("o1-"):
            return await self.providers["openai"].generate(prompt, model)
        elif model.startswith("gemini"):
            return await self.providers["gemini"].generate(prompt, model)
        elif model.startswith("mock"):
            return await self.providers["mock"].generate(prompt, model)
        
        # 2. Fallback to configured default provider if it matches a known provider
        if self.default_provider in self.providers and self.default_provider != "auto":
            return await self.providers[self.default_provider].generate(prompt, model)
        
        # 3. If auto and no match, default to mock for safety
        return await self.providers["mock"].generate(prompt, model)

def get_llm_provider(provider_name: str = settings.LLM_PROVIDER) -> LLMProvider:
    # Always return the router, which handles the logic
    return MultiProviderRouter()
