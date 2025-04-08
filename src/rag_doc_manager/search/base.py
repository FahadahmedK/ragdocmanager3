from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Callable
from enum import Enum
from pydantic import BaseModel, Field

# TODO: Violating DRY (same object can be found in doocument manager)
class Scope(Enum):
    GLOBAL = 'global'
    ACCOUNT = 'account'
    USER = 'user'
    SESSION = 'session'


class SearchStrategy(Enum):
    
    TEXT = "text"
    VECTOR = "vector"
    HYBRID = "hybrid"

class SearchResult(BaseModel):

    """
    Represents a single search result returned by the query engine
    """
    document_id: str
    content: str
    score: float
    chunk_id: Optional[str] = None 
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    
class SearchResponse(BaseModel):
    """Represents the complete response from a search query"""
    results: List[SearchResult]
    total_results: int
    query_time_ms: Optional[float] = None


class Filters(BaseModel):
    pass
    

class SearchParams(BaseModel):
    
    """Parameters for configuring search behavior"""
    top_k: int = 10
    # enhance filters later 
    filters: Dict[str, Any] = Field(default_factory=dict)
    search_strategy: SearchStrategy = SearchStrategy.HYBRID
    sort_by: Optional[str] = None
    # sort_order: Optional[str] = None  # "asc" or "desc"
    vector_search_weight: Optional[float] = None
    keyword_search_weight: Optional[float] = None

    class Config:
        use_enum_values = True


# TODO: 
# class RerankingStrategy(BaseModel):
#     """Configuration for result reranking"""
#     name: str  # e.g., "semantic", "diversity", "custom"
#     config: Dict[str, Any] = {}
#     custom_reranker: Optional[Callable[[List[SearchResult], str], List[SearchResult]]] = None



    
class QueryEngine(ABC):
    
    @abstractmethod
    def search(
        self,
        index_name: str,
        query: str,
        account_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        scope: Optional[str] = 'global',
        # is_global: bool = False,
        # metadata: Dict[str, Any] = None,
        search_params: Optional[SearchParams] = None,
        # TODO
        # reranking: Optional[RerankingStrategy] = None,
        **kwargs
    ) -> SearchResponse:
        
        pass