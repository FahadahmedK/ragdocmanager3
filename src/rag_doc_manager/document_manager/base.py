from abc import ABC, abstractmethod
from typing import Annotated, Union
from pathlib import Path
import threading
from enum import Enum

from rag_doc_manager.customer_manager.remote_customer_schema_manager import CustomerIndexSchemaManager

class Scope(Enum):

    GLOBAL = 'global'
    ACCOUNT = 'account'
    USER = 'user'
    SESSION = 'session'


class DocumentManager(ABC):


    client_name: str

    _instances = {}
    _lock = threading.RLock()
    customer_manager = CustomerIndexSchemaManager()

    def __init__(self, customer: str):
        # Only initialize once
        if not hasattr(self, '_initialized') or not self._initialized:
            self._initialized = True
            # self.initialize()

    # TODO: allow as many instances of DocumentManager in the future for better performance (con: memory overhead)
    def __new__(cls, customer: Annotated[str, "unique ID of the customer"], *args, **kwargs):
        with cls._lock:
            if customer not in cls._instances:
                instance = super(DocumentManager, cls).__new__(cls)
                instance._initialized = False
                instance.customer = customer
                cls._instances[customer] = instance
            return cls._instances[customer]


    @abstractmethod
    def upload(
        self,
        index_name: str,
        file: Annotated[Union[str, Path], "local file path"],
        account_id: Annotated[str, "Account ID under the customer"],
        user_id: Annotated[str, "User ID of the user sending request"],
        session_id: Annotated[str, "ID of the specific session (chat or another app)"],
        scope: Annotated[Scope, "Define indexing hierarchy"]
    ):
        pass

    @abstractmethod
    def delete(
        self,
        account_id: Annotated[str, "Account ID under the customer"],
        user_id: Annotated[str, "User ID of the user sending request"]
    ):
        pass

    # @abstractmethod
    def search(
        self
    ):
        raise NotImplementedError



        
    @classmethod
    def clear_instances(cls):
        """Clear all instances (useful for testing)"""
        with cls._lock:
            cls._instances.clear()
        
        
    

   

    
    # 1. Get Object Storage
    # 2. Download file from object storage in a specific prefix 
    # 3. Process the document
    # 4. Get the indexer
    # 6. Index the document
        
    # 1. Get Searcher
    # 2. Search the document

    