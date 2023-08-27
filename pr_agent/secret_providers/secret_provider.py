from abc import ABC, abstractmethod


class SecretProvider(ABC):

    @abstractmethod
    def get_secret(self, secret_name: str) -> str:
        pass

    @abstractmethod
    def store_secret(self, secret_name: str, secret_value: str):
        pass
