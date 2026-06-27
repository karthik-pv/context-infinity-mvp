import json
import os
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
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": message}],
        }
        data = await self._post(payload)
        return data["choices"][0]["message"]["content"]

    async def chat_with_tools(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict],
    ) -> tuple[str | None, list[dict]]:
        """
        Single Fireworks turn with tool calling (OpenAI-compatible format).
        Prepends system as a system message; tools converted from Anthropic to OpenAI format.
        """
        openai_messages = [{"role": "system", "content": system}, *messages]
        openai_tools = [_anthropic_to_openai_tool(t) for t in tools]

        payload = {
            "model": self.model,
            "max_tokens": max(self.max_tokens, 4096),
            "messages": openai_messages,
            "tools": openai_tools,
            "tool_choice": "auto",
        }
        data = await self._post(payload)

        message = data["choices"][0]["message"]
        final_text = message.get("content") or None
        tool_calls_raw = message.get("tool_calls") or []

        tool_calls = []
        for tc in tool_calls_raw:
            tool_calls.append({
                "id": tc["id"],
                "name": tc["function"]["name"],
                "input": json.loads(tc["function"]["arguments"]),
            })

        return final_text if not tool_calls else None, tool_calls

    async def _post(self, payload: dict) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{_FIREWORKS_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                return await response.json()


def _anthropic_to_openai_tool(tool: dict) -> dict:
    """Convert Anthropic tool schema to OpenAI function format."""
    return {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool.get("description", ""),
            "parameters": tool["input_schema"],
        },
    }
