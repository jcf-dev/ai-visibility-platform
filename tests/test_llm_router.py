import pytest
from unittest.mock import AsyncMock
from app.infrastructure.llm.client import MultiProviderRouter


@pytest.mark.asyncio
async def test_router_routing():
    router = MultiProviderRouter()

    # Mock the internal providers
    router.providers["openai"] = AsyncMock()
    router.providers["gemini"] = AsyncMock()
    router.providers["mock"] = AsyncMock()

    # Test OpenAI routing
    await router.generate("test", "gpt-4")
    router.providers["openai"].generate.assert_called_with("test", "gpt-4")

    # Test Gemini routing
    await router.generate("test", "gemini-pro")
    router.providers["gemini"].generate.assert_called_with("test", "gemini-pro")

    # Test Mock routing
    await router.generate("test", "mock-test")
    router.providers["mock"].generate.assert_called_with("test", "mock-test")


@pytest.mark.asyncio
async def test_router_fallback():
    router = MultiProviderRouter()
    router.providers["mock"] = AsyncMock()

    # Test unknown prefix falls back to mock (or default)
    # Assuming default is mock in test env
    await router.generate("test", "unknown-model")
    router.providers["mock"].generate.assert_called()
