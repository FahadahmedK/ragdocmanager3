from enum import Enum
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from fastapi import status
import rag_doc_manager.search as s


router = APIRouter(prefix='/search', tags=['search'])


# TODO: will move this to configuration
def get_azure_query_engine():
    return s.QueryEngineFactory.get_query_engine(provider='azure')


@router.get("/", response_model=s.SearchResponse)
async def search_documents(
    query: str = Query(..., description="Search query text"),
    customer_id: str = Query(..., description="Customer ID"),
    account_id: str = Query(..., description="Account name"),
    user_id: Optional[str] = Query(None, description="User ID"),
    session_id: Optional[str] = Query(None, description="Session ID"),
    scope: Optional[str] = Query(default='global', description="scope of the search"),
    search_type: Optional[str] = Query('vector', description="Search type (text, vector, hybrid)"),
    top_k: int = Query(3, description="Number of results to return"),
    query_engine: s.QueryEngine = Depends(get_azure_query_engine)
):

    # TODO: make this configurable
    search_strategy = s.SearchStrategy.VECTOR

    search_params = s.SearchParams(
        top_k=top_k,
        search_strategy=search_strategy,
    )

    return query_engine.search(
        index_name=customer_id,
        account_id=account_id,
        user_id=user_id,
        session_id=session_id,
        scope = scope,
        search_params=search_params,
        query=query
    )


