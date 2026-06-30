import json
import os
from openai import AsyncOpenAI
from .base import AIAdapter


class OpenAIAdapter(AIAdapter):
    def __init__(self, config: dict):
        self.client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = config.get("model", "gpt-4o")
        self.max_tokens = config.get("max_tokens", 1024)

    async def chat(self, message: str) -> tuple[str, dict]:
        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=max(self.max_tokens, 4096),
            messages=[{"role": "user", "content": message}],
        )
        usage = {
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
        }
        return response.choices[0].message.content, usage

    async def chat_with_tools(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict],
    ) -> tuple[str | None, list[dict], dict]:
        """
        Single OpenAI turn with function calling.
        Prepends system as a system message; tools are converted from Anthropic to OpenAI format.
        """
        openai_messages = [{"role": "system", "content": system}, *messages]
        openai_tools = [_anthropic_to_openai_tool(t) for t in tools]

        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=max(self.max_tokens, 4096),
            messages=openai_messages,
            tools=openai_tools,
            tool_choice="auto",
        )

        message = response.choices[0].message
        final_text = message.content or None
        tool_calls = []
        for tc in (message.tool_calls or []):
            tool_calls.append({
                "id": tc.id,
                "name": tc.function.name,
                "input": json.loads(tc.function.arguments),
            })

        usage = {
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
        }

        return final_text if not tool_calls else None, tool_calls, usage


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
