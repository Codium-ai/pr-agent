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


class AiHandler(BaseAiHandler):
    """
    This class handles interactions with the OpenAI API for chat completions.
    It initializes the API key and other settings from a configuration file,
    and provides a method for performing chat completions using the OpenAI ChatCompletion API.
    """

    # ... rest of your code ...


class CustomAiHandler(BaseAiHandler):
    """
    This class is your custom AI handler that uses a different LLM library.
    """

    def __init__(self):
        # Initialize your custom AI handler
        pass

    @property
    def deployment_id(self):
        # Return the deployment ID for your custom AI handler
        pass

    async def chat_completion(self, model: str, system: str, user: str, temperature: float = 0.2):
        # Implement the chat completion method for your custom AI handler
        pass