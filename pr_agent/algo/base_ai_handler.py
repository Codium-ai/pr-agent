from abc import ABC, abstractmethod

class BaseAiHandler(ABC):
    """
    This class defines the interface for an AI handler.
    """

    @abstractmethod
    def __init__(self):
        pass

    @property
    @abstractmethod
    def deployment_id(self):
        pass

    @abstractmethod
    async def chat_completion(self, model: str, system: str, user: str, temperature: float = 0.2):
        pass

