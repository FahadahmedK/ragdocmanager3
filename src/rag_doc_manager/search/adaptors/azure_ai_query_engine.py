import logging
from typing import Optional, Dict, Any
import time
from azure.search.documents.models import VectorizedQuery, QueryType
from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential

from ..base import QueryEngine, SearchParams, SearchResult, SearchResponse, Scope
from rag_doc_manager.document_processor.embedders.factory import EmbedderFactory
from rag_doc_manager.storage.secrets.azure_key_vault import AzureKeyVaultStore
from rag_doc_manager.storage.secrets.credentials_handler import AzureCredentialManager

class AISearchQueryEngine(QueryEngine):

    credentials = AzureCredentialManager().get_credentials()

    key_vault = AzureKeyVaultStore(
            config={
                'vault_url': 'https://kv-indcopilot-llmops-dev.vault.azure.net/'
            }
        )

    embedder = EmbedderFactory.create_embedder(
        'azure',
        # api_key=self.key_vault.get_secret("openai-api-key"),
        endpoint=key_vault.get_secret("azure-openai-endpoint"),
        deployment_name='text-embedding-ada-002'
    )


    def __init__(
        self,
    ):

        self.service_name = self.key_vault.get_secret('aisearch-endpoint')
        self.logger = logging.getLogger(__name__)


    def _get_search_client(self, index_name: str) -> SearchClient:

        return SearchClient(
            endpoint=f"https://{self.service_name}.search.windows.net",
            index_name=index_name,
            credential=AISearchQueryEngine.credentials
        )

    def _build_filter_expression(
        self,
        account_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        scope: Optional[str] = 'global',
        custom_filters: Dict[str, Any] = None
    ) -> Optional[str]:

        filter_conditions = []
        # Add hierarchical filters

        if scope == 'account':
            assert account_id
            filter_conditions.append(f"account_id eq '{account_id}'")

        elif scope == 'user':
            assert user_id
            filter_conditions.append(f"user_id eq '{user_id}'")

        elif scope == 'session':
            assert session_id
            filter_conditions.append(f"session_id eq '{session_id}'")

        else:
            # If is_global is True, include global documents in the results, as well
            if filter_conditions:
                # If we already have user-specific filters, add OR condition for global docs
                global_condition = "is_global eq true"
                existing_conditions = " and ".join(filter_conditions)
                filter_conditions = [f"({existing_conditions}) or {global_condition}"]
            else:
                # If no filters yet, just include global docs
                filter_conditions.append("is_global eq true")

        # Add custom filters
        if custom_filters:
            for field, value in custom_filters.items():
                if isinstance(value, str):
                    filter_conditions.append(f"{field} eq '{value}'")
                elif isinstance(value, bool):
                    filter_conditions.append(f"{field} eq {str(value).lower()}")
                elif isinstance(value, (int, float)):
                    filter_conditions.append(f"{field} eq {value}")
                elif isinstance(value, list):
                    # Handle list values for IN-style queries
                    if value and isinstance(value[0], str):
                        values_str = ", ".join([f"'{v}'" for v in value])
                        filter_conditions.append(f"{field} in ({values_str})")
                    elif value:
                        values_str = ", ".join([str(v) for v in value])
                        filter_conditions.append(f"{field} in ({values_str})")

        # Combine all conditions with AND
        if filter_conditions:
            return " and ".join(filter_conditions)

        return None

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
        **kwargs
    ):
        """
        Search the specified index using Azure AI Search.

        Parameters
        ----------
        index_name : str
            The name of the search index.
        query : str
            The search query.
        account_id : Optional[str], optional
            The account ID to filter by, by default None.
        user_id : Optional[str], optional
            The user ID to filter by, by default None.
        is_global : bool, optional
            Whether to include global documents, by default False.
        search_params : Optional[SearchParams], optional
            Parameters for configuring search behavior, by default None.
        **kwargs
            Additional keyword arguments

       Returns
        -------
        SearchResponse
            The search results.
        """
        # Start timing the query

        # TODO: leverage the super class to add this functionality

        search_client = self._get_search_client(index_name)
        start_time = time.time()

        if search_params is None:
            search_params = SearchParams()

        # TODO: deal with global documents
        filter_expression = self._build_filter_expression(
            account_id=account_id,
            user_id=user_id,
            session_id=session_id,
            scope=scope,
            # is_global=is_global,
            custom_filters=search_params.filters
        )



        search_options = {
            'filter': filter_expression,
            'top': search_params.top_k,
            'include_total_count': True,
            'query_type': 'simple',
            "select": "document_id,chunk_id,content,is_global,account_id,user_id"
        }

        # Handle sorting if specified
        if search_params.sort_by:
            search_options["order_by"] = search_params.sort_by

        if search_params.search_strategy == 'vector':

            # TODO: only dealing with vector search right now
            embedded_query = AISearchQueryEngine.embedder.embed_text(query)

            vector_query = VectorizedQuery(
                vector=embedded_query,
                k_nearest_neighbors=search_params.top_k,
                fields="embedding",
                exhaustive=True # exhaustive search for accuracy
            )

            # setting up vector search options
            search_options["vector_queries"] = [vector_query]
            search_options.pop('query_type', None)

            search_results = search_client.search(
                search_text=None,
                **search_options
            )

        elif search_params.search_strategy == 'text':

            # raise NotImplementedError("text search not implemented")
            search_results = []
            pass
        elif search_params.search_strategy == 'hybrid':
            search_results = []
            # raise NotImplementedError("hybrid search not implemented")
            pass
        else:

            self.logger.warning(
                f"Search strategy {search_params.search_strategy} not implemented, falling back to vector search")

            # Default to vector search

        results = []
        for result in search_results:

            metadata = {}
            if hasattr(result, "metadata") and result.metadata:
                metadata = result.metadata

            search_result = SearchResult(
                document_id=result['document_id'],
                content=result['content'],
                score=result["@search.score"],
                chunk_id=result.get('chunk_id', None),
                metadata=metadata
            )

            results.append(search_result)

        query_time_ms = (time.time() - start_time) * 1000
        return SearchResponse(
            results=results,
            total_results=search_results.get_count(),
            query_time_ms=query_time_ms
        )


