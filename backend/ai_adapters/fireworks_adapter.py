import os
import json
import aiohttp
from .base import AIAdapter

_FIREWORKS_BASE_URL = "https://api.fireworks.ai/inference/v1"
_DEFAULT_MODEL = "accounts/fireworks/models/llama-v3p1-70b-instruct"


class FireworksAdapter(AIAdapter):
    def __init__(self, config: dict):
        self.api_key = os.environ.get("FIREWORKS_API_KEY")
        self.model = config.get("model", _DEFAULT_MODEL)
        self.max_tokens = config.get("max_tokens", 1024)

    async def chat(self, message: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": message}],
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{_FIREWORKS_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                data = await response.json()
                return data["choices"][0]["message"]["content"]
