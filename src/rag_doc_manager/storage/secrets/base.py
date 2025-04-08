from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Optional

class SecretstoreError(Exception):
    pass

class SecretNotFoundError(SecretstoreError):
    pass

class AuthenticationError(SecretstoreError):
    pass

class SecretStoreConnectionError(SecretstoreError):
    pass


class SecretStore(ABC):
    config: Optional[Dict[str, Any]]
    logger: logging.Logger

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}

    @abstractmethod
    def get_secret(self, key: str) -> str:
        pass

    @abstractmethod
    def set_secret(self, key: str, value: str) -> bool:
        pass
    
    
    

    
    

    