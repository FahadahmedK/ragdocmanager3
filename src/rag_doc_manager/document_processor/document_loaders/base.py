from abc import ABC, abstractmethod
from typing import Union
from pathlib import Path
from langchain_core.document_loaders.base import BaseLoader



class BaseDocumentLoader(ABC):
    
    
    @abstractmethod
    async def load_document(
        self,
        file_path
    ):
    
        pass