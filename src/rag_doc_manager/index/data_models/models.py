from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import datetime
from rag_doc_manager.customer_manager.data_models.models import IndexConfig

@dataclass
class IndexMetadata:
    
    # TODO: reduce coupling
    name: str
    config: IndexConfig
    # created_at: Optional[str] = None
    # last_updated_at = Optional[str] = None

@dataclass
class IndexingResponse:
    
    # users need to track their documents via document_id, perhaps
    # how else do we version?
    success: bool
    document_id: str
    error_message: Optional[str]

@dataclass
class Document:
    """
    Document enriched by the system to be indexed with extended metadata and hierarchical relationships.
    
    Hierarchy:
      - account_id (grandparent): The account under which the user belongs.
      - user_id (parent): The user who owns the document.
      - document_id (child): The  identifier of the original document.
      - chunk_id (grandchild): Unique Identifier for a chunk of the document if it has been split.
    """
    
    # Hierarchical fields
    
    # Hierarchical fields
    account_id: str = None  # Grandparent
    user_id: Optional[str] = None     # Parent
    document_id: str = ""             # Child
    chunk_id: Optional[str] = None    # Grandchild
    chunk_position: Optional[int] = None
    session_id: Optional[str] = None
    
    # Core content and search-related fields
    content: str = ""
    is_global: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    embedding: Optional[List[float]] = None
    
    
    # Timestamps for auditing
    created_at: datetime = field(default_factory=lambda: datetime.datetime.now(tz=datetime.UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.datetime.now(tz=datetime.UTC))

    version: int = 1
    # additional_fields: Dict[str, Any] = field(default_factory=dict)
    
    # def __post_init__(self):
    #     # Add additional fields as attributes
    #     for key, value in self.additional_fields.items():
    #         setattr(self, key, value)
