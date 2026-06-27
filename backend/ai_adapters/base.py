from abc import ABC, abstractmethod


class AIAdapter(ABC):
    @abstractmethod
    async def chat(self, message: str) -> str:
        ...
