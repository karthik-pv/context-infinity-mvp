import os
from anthropic import AsyncAnthropic
from .base import AIAdapter


class AnthropicAdapter(AIAdapter):
    def __init__(self, config: dict):
        self.client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.model = config.get("model", "claude-opus-4-8")
        self.max_tokens = config.get("max_tokens", 1024)

    async def chat(self, message: str) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": message}],
        )
        return response.content[0].text
