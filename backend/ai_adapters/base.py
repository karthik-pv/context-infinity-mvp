from abc import ABC, abstractmethod


class AIAdapter(ABC):
    @abstractmethod
    async def chat(self, message: str) -> tuple[str, dict]:
        """Single-turn chat without tools. Returns (text, usage)."""
        ...

    @abstractmethod
    async def chat_with_tools(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict],
    ) -> tuple[str | None, list[dict], dict]:
        """
        Single LLM turn with tool use support.

        Args:
            system: System prompt text.
            messages: Conversation so far in OpenAI wire format:
                      - user/assistant text: {"role": ..., "content": "..."}
                      - assistant with tool calls: {"role": "assistant", "content": "",
                            "tool_calls": [{"id", "type", "function": {"name", "arguments"}}]}
                      - tool result: {"role": "tool", "tool_call_id": ..., "name": ..., "content": "..."}
            tools: Tool schemas in Anthropic format:
                   [{"name": ..., "description": ..., "input_schema": {JSON Schema}}]

        Returns:
            (final_text, tool_calls, usage) where:
            - final_text: assistant text response (may be None or empty when tool calls are present)
            - tool_calls: list of {"id": str, "name": str, "input": dict}
                          Empty list when the response is the final message.
            - usage: {"input_tokens": int, "output_tokens": int}
        """
        ...
