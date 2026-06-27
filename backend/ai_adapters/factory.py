import json
import os
from .base import AIAdapter

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")


def get_adapter() -> AIAdapter:
    with open(_CONFIG_PATH) as f:
        config = json.load(f)

    provider = config.get("ai_provider", "anthropic")

    if provider == "anthropic":
        from .anthropic_adapter import AnthropicAdapter
        return AnthropicAdapter(config.get("anthropic", {}))
    elif provider == "openai":
        from .openai_adapter import OpenAIAdapter
        return OpenAIAdapter(config.get("openai", {}))
    elif provider == "fireworks":
        from .fireworks_adapter import FireworksAdapter
        return FireworksAdapter(config.get("fireworks", {}))
    else:
        raise ValueError(f"Unknown ai_provider: {provider!r}")
