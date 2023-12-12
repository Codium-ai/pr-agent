from abc import ABC, abstractmethod

class BaseAiHandler(ABC):
    """
    This class defines the interface for an AI handler to be used by the PR Agents.  
    """

    @abstractmethod
    def __init__(self):
        pass

    @property
    @abstractmethod
    def deployment_id(self):
        pass

    @abstractmethod
    """
    This method should be implemented to return a chat completion from the AI model.
    params:
        model: the name of the model to use for the chat completion
        system: the system message string to use for the chat completion
        user: the user message string to use for the chat completion
        temperature: the temperature to use for the chat completion    
    """
    async def chat_completion(self, model: str, system: str, user: str, temperature: float = 0.2):
        pass

