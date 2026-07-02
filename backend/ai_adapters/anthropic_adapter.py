import json
import os
from anthropic import AsyncAnthropic
from .base import AIAdapter


class AnthropicAdapter(AIAdapter):
    def __init__(self, config: dict):
        self.client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.model = config.get("model", "claude-opus-4-8")
        self.max_tokens = config.get("max_tokens", 1024)

    async def chat(self, message: str) -> tuple[str, dict]:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max(self.max_tokens, 4096),
            messages=[{"role": "user", "content": message}],
        )
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
        return response.content[0].text, usage

    async def chat_with_tools(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict],
    ) -> tuple[str | None, list[dict], dict]:
        """
        Single Anthropic turn with tool use.
        Converts OpenAI-format messages and returns normalized (text, tool_calls, usage).
        Tool schemas are already in Anthropic format (input_schema field).
        """
        anthropic_messages = _to_anthropic_messages(messages)
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max(self.max_tokens, 4096),  # tool loops need more room
            system=system,
            messages=anthropic_messages,
            tools=tools,
        )

        tool_calls = [
            {"id": block.id, "name": block.name, "input": block.input}
            for block in response.content
            if block.type == "tool_use"
        ]
        text_parts = [block.text for block in response.content if block.type == "text"]
        final_text = "\n".join(text_parts).strip() or None

        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }

        return final_text, tool_calls, usage


# ── Message format conversion: OpenAI → Anthropic ───────────────────────────

def _to_anthropic_messages(messages: list[dict]) -> list[dict]:
    """
    Convert the internal OpenAI-format message list to Anthropic format.

    Key differences:
    - Anthropic has no "tool" role: tool results go inside a "user" message as
      {"type": "tool_result", "tool_use_id": ...} content blocks.
    - Consecutive tool result messages are batched into a single user message.
    - Assistant tool calls are {"type": "tool_use", "id", "name", "input"} blocks.
    """
    result = []
    i = 0
    while i < len(messages):
        msg = messages[i]
        role = msg["role"]

        if role == "user":
            result.append({"role": "user", "content": msg["content"]})
            i += 1

        elif role == "assistant":
            tool_calls = msg.get("tool_calls") or []
            if tool_calls:
                content_blocks = []
                if msg.get("content"):
                    content_blocks.append({"type": "text", "text": msg["content"]})
                for tc in tool_calls:
                    content_blocks.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["function"]["name"],
                        "input": json.loads(tc["function"]["arguments"]),
                    })
                result.append({"role": "assistant", "content": content_blocks})
            else:
                result.append({"role": "assistant", "content": msg.get("content", "")})
            i += 1

        elif role == "tool":
            # Batch all consecutive tool results into one user message
            tool_result_blocks = []
            while i < len(messages) and messages[i]["role"] == "tool":
                tr = messages[i]
                tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tr["tool_call_id"],
                    "content": tr["content"],
                })
                i += 1
            result.append({"role": "user", "content": tool_result_blocks})

        else:
            i += 1  # skip unknown roles

    return result
