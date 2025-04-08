from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, TypeVar, Union
from enum import Enum
from pydantic import BaseModel, field_validator, Field
import logging

from .data_models.models import IndexMetadata, Document, IndexingResponse

# from concurrent.futures import as_completed
# from contextlib import ExitStack

logger = logging.getLogger(__name__)

# class User(BaseModel):
    
#     user_id: str
#     parent_id: str
    
#     class Config:
#         arbitrary_types_allowed = True
#         extra = "allow"

# class DocumentMetadata(BaseModel):
#     user_data: User
#     is_global: bool = False
#     class Config:
#         arbitrary_types_allowed = True
#         extra = "allow"


# @dataclass
# class UserDocumentData:
#     """
#     Data to be received by the system
#     """
#     url: str
#     metadata: DocumentMetadata
    

# class IndexingResponse:
#     """Result of an indexing operation"""
#     success: bool
#     document_id: str
#     error_message: Optional[str] = None


class Index(ABC):
    """Abstract base class for indexing operations.
    
    This class defines the interface for index providers.
    Invoked at every user call. Instantiated when index needs to be created, as well.
    
    Attributes
    ----------
    index_name : str
        Name of the index
    """
    
    # the documents here are already processed and ready to be indexed
    @abstractmethod
    async def index_documents(self, documents: List[Document]) -> List[IndexingResponse]:
        """Index the given list of documents.
        
        Parameters
        ----------
        documents : List[Document]
            List of Document objects to be indexed
            
        Returns
        -------
        List[IndexingResponse]
            List of IndexingResponse objects with results of the indexing operation
        """
        pass

    @abstractmethod
    async def delete_document(self, document_id: str) -> List[bool]:
        """Delete all the chunks for the document from the index, given the document id 
        
        Parameters
        ----------
        document_ids : List[str]
            List of document IDs to delete
            
        Returns
        -------
        List[bool]
            List of Booleans objects inidicating results of the delete operation
        """
        pass
    
    # @abstractmethod
    # async def list_documents(self, index_name: str, account_id: Optional[str], user_id: str) -> List[Document]:
        
    
    # @abstractmethod
    # async def update_documents(self, documents: List[Document]) -> List[IndexingResponse]:
    #     """Update the given documents in the index.
        
    #     Parameters
    #     ----------
    #     documents : List[Document]
    #         List of Document objects to update
            
    #     Returns
    #     -------
    #     List[IndexingResponse]
    #         List of IndexingResponse objects with results of the update operation
    #     """
    #     pass
    
    # @abstractmethod
    # async def get_document(self, document_id: str) -> Optional[Document]:
    #     """Retrieve a single document by ID. Recollect the document if chunked. 
        
    #     Parameters
    #     ----------
    #     document_id : str
    #         ID of the document to retrieve. This is the parent document ID and not the chunk ID
            
    #     Returns
    #     -------
    #     Optional[Document]
    #         Document object if found, None otherwise
    #     """
    #     pass
    
    
    @abstractmethod
    async def create_index(self, index: IndexMetadata, **kwargs) -> bool:
        
        
        """Create a new index with the specified metadata.
        
        Parameters
        ----------
        index : IndexMetadata
            IndexMetadata object containing index configuration
            
        Returns
        -------
        IndexingResponse
            IndexingResponse with creation result
        """
        pass
    

    @abstractmethod
    async def delete_index(self, index_name: str, **kwargs) -> bool:
        """Delete an index with the specified name.
        
        Parameters
        ----------
        index_name : str
            Name of the index to delete
            
        Returns
        -------
        bool
            Boolean indicating whether the index was deleted or not
        """
        pass
    
    
    @abstractmethod
    async def check_index_exists(self, index_name: str, **kwargs) -> bool:
        """Check if the index with the specified name exists.
        
        Parameters
        ----------
        index_name : str
            Name of the index to check
            
        Returns
        -------
        bool
            Boolean indicating whether the index exists
        """
        pass 
    
    

    
    