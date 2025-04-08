from typing import List, Optional
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient

from azure.search.documents.indexes.models import VectorSearch
from azure.search.documents.indexes.models import VectorSearchProfile
from azure.search.documents.indexes.models import HnswAlgorithmConfiguration
from azure.search.documents.indexes.models import SearchIndex
from azure.search.documents.indexes.models import SearchFieldDataType, SearchField
from azure.core.exceptions import ResourceNotFoundError

from rag_doc_manager.storage.secrets.credentials_handler import AzureCredentialManager
from rag_doc_manager.index.data_models.models import Document, IndexingResponse, IndexMetadata
from rag_doc_manager.customer_manager.data_models.models import IndexSchema
from rag_doc_manager.index.base import Index


import logging

# Create a logger object
logger = logging.getLogger(__name__)  # Use __name__ to get the name of the current module

class AISearchIndexClient(Index):
    """Implementation of the Index abstract class for Azure AI Search"""

    def __init__(self, ais_service_name: str, index_name: str, ):
        self.service_name = ais_service_name
        self.index_name = index_name
        self.metadata = None
        credential_manager = AzureCredentialManager()
        self.credentials = credential_manager.get_credentials()
        self.index_client = SearchIndexClient(
            endpoint=f"https://{self.service_name}.search.windows.net",
            index_name=self.index_name,
            credential=self.credentials
        )
        self.search_client = SearchClient(
            endpoint=f"https://{self.service_name}.search.windows.net",
            index_name=self.index_name,
            credential=self.credentials
        )


    def index_documents(self, documents: List[Document]) -> List[IndexingResponse]:
        """Index the given list of documents in Azure AI Search."""
        results = []
        self._get_primary_key()

        # Mapping Document model to Azure Search Indexing format
        docs = [self.convert_doc_to_search_record(doc) for doc in documents]
        documents_to_index = [doc for doc in docs if doc is not None]

        indexing_results = self.search_client.upload_documents(documents=documents_to_index)
        
        # Prepare indexing response
        for result in indexing_results:
            results.append(IndexingResponse(
                success=result.succeeded,
                document_id=result.key,
                error_message=result.error_message
            ))

        #TODO: Add logging for failure of individual chunks

        return results

    def delete_document(self, document_id: List[str]) -> List[IndexingResponse]:
        """Delete the given documents from the Azure AI Search index."""
        results = []

        chunk_ids = self.list_document_chunks(document_id)
        try:
            #TODO: Check schema
            delete_actions = [{"@search.action": "delete", "chunk_id": document_id} for document_id in chunk_ids]
            indexing_results = self.search_client.upload_documents(documents=delete_actions)

            for result in indexing_results:
                results.append(IndexingResponse(
                    success=result.succeeded,
                    document_id=result.key,
                    error_message=result.error_message
                ))
            
            #TODO: Add logging for individual chunk deletion failures
        except Exception as e:
            raise Exception(f"Failed to delete chunks for document {document_id}: {e}")
        return results

    def list_document_chunks(self, document_id: str) -> List[str]:
        """List all chunks for a document_id in the Azure AI Search index.
        
        Parameters
        ----------
        document_id : str
            ID of the document to list chunks for
        
        Returns
        -------
        List[str]
            List of chunk IDs for the specified document
        """
        primary_key = self._get_primary_key()
        #TODO: Check if this is the right field in the schema
        filter = f"document_id eq '{document_id}'"
        try:
            results = self.search_client.search(filter=filter)
            chunk_ids = [result.get(primary_key) for result in results]
        except Exception as e:
            raise Exception(f"Failed to list document chunks for document {document_id}: {e}")
            chunk_ids = []
        return chunk_ids


    def create_index(self, index: IndexMetadata) -> bool:
        """Create a new index in Azure AI Search."""
        if index.name == self.index_name:
            self.metadata = index
        else:
            logger.error(f"Index name mismatch: {index.name} != {self.index_name}, the index could not be created.")
            return False
        azure_fields = self.define_azure_fields(index.config.index_schema)
        # Formatting the schema for it to be ready for index creation
        try:
            #TODO: Make this configurable by the user
            vector_search = VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="my-algorithms-config",
                    kind="hnsw",
                    parameters={
                        "metric": "cosine",
                    },
                )
            ],
            profiles=[
                VectorSearchProfile(
                    name="my-vector-search-profile",
                    algorithm_configuration_name="my-algorithms-config",
                )
            ],
            )

            index = SearchIndex(
                name=index.name,
                fields=azure_fields,
                vector_search=vector_search,
            )
            result = self.index_client.create_or_update_index(index)
            logger.info(f"{result.name} created")
            return True
        except Exception as e:
            logger.error(f"Failed to create index {index.name}: {e}")
            return False
        


    async def delete_index(self, index_name: str) -> bool:
        """Delete the specified index from Azure AI Search."""
        try:
            self.index_client.delete_index(index_name)
            return True
        except Exception as e:
            logger.error(f"Failed to delete index {index_name}: {e}")
            return False

    def check_index_exists(self, index_name: str) -> bool:
        """Check if the specified index exists in Azure AI Search."""
        try:
            index = self.index_client.get_index(index_name)
            return True
        except ResourceNotFoundError as e:
            logger.info(f"Index {index_name} not found: {e}")
            return False

        
    def convert_doc_to_search_record(self, document: Document) -> dict:
        """Convert a Document object to a dictionary for indexing in Azure Search."""

        if self.metadata:
            fields =  [field.name for field in self.metadata.config.index_schema.fields]
        else:
            try:
                fields = [field.name for field in self.index_client.get_index(name = self.index_name).fields]
            except Exception as e:
                raise Exception(f"Failed to get fields from index {self.index_name}: {e}")
                fields = []
        
        record = {}
        for field in fields:
            record[field] = getattr(document, field, None)
        self._get_primary_key()
        if self.primary_key not in record:
            logger.error(f"Primary key {self.primary_key} not found in document {document.document_id}")
            record = None
        return record
        

    def define_azure_fields(self,index_schema: IndexSchema) -> dict:
        # Map Pydantic field types to Azure Search types
        field_type_mapping = {
            "string": SearchFieldDataType.String,  
            "date": SearchFieldDataType.DateTimeOffset,  
            "integer": SearchFieldDataType.Int32,  
            "float": SearchFieldDataType.Double,  
            "boolean": SearchFieldDataType.Boolean 
            }

        # Build fields for Azure Search
        azure_fields = []
        for field in index_schema.fields:
            print(field)
            azure_field = SearchField(name=field.name, type=field_type_mapping[field.field_type])
            
            # Set other attributes if specified
            if field.filterable:
                azure_field.filterable = True
            if field.searchable:
                azure_field.searchable = True
            if field.sortable:
                azure_field.sortable = True
            if field.primary_key:
                azure_field.key = True
            
            azure_fields.append(azure_field)
        
        # Include vector dimensions if applicable (for vector search)
        if index_schema.vector_dimensions:
            # Assuming vector search is supported by your field types (e.g., "Collection(Edm.Single)")
            # TODO: Check based on asumed general schema
            vector_field = SearchField(name="embedding", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), vector_search_dimensions=1536,
                vector_search_profile_name="my-vector-search-profile",)
            vector_field.vector_search_dimensions = index_schema.vector_dimensions
            azure_fields.append(vector_field)
        
        return azure_fields

    def _get_primary_key(self) -> Optional[str]:
        """Get the primary key field for the index."""
        try:
            fields = self.index_client.get_index(name=self.index_name).fields
            primary_key = next((field.name for field in fields if field.key), None)
            self.primary_key = primary_key
            return primary_key
        except Exception as e:
            raise Exception(f"Failed to get primary key for index {self.index_name}: {e}")
            return None


class AISearchException(Exception):
    def __init__(self, detail: str):
        self.detail = detail