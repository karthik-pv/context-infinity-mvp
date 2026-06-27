import os
from openai import AsyncOpenAI
from .base import AIAdapter


class OpenAIAdapter(AIAdapter):
    def __init__(self, config: dict):
        self.client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = config.get("model", "gpt-4o")
        self.max_tokens = config.get("max_tokens", 1024)

    async def chat(self, message: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": message}],
        )
        return response.choices[0].message.content
