from typing import List, Union, Tuple
import datetime
from typing_extensions import Self
from dataclasses import dataclass
import uuid
import logging
# from pydantic import BaseModel, model_validator

from rag_doc_manager.customer_manager.data_models.models import IndexingStrategy
from rag_doc_manager.customer_manager.remote_customer_schema_manager import CustomerIndexSchemaManager
from rag_doc_manager.index.adaptors.azure_ai_indexing_engine import AISearchIndexClient
from rag_doc_manager.storage.secrets.azure_key_vault import AzureKeyVaultStore
from rag_doc_manager.index.data_models.models import IndexMetadata
from rag_doc_manager.storage.database_manager.cosmosdb_manager import CosmosDBClient
from rag_doc_manager.index_manager.data_models.models import IndexRecord

from rag_doc_manager.index.base import Index

logger = logging.getLogger(__name__)

@dataclass
class ClientIndexMapping:
    
    index_name: str # Unique for each index, serves as unique identifier
    customer_id: str  
    accounts: Union[List[str], str] # multiple accounts can share one index, or one account per index
    # users: List[str] # multiple users per index, but not required right now


class MonoStateIndexManager:
    
    def __init__(self):
        
        self.__dict__["_INTERNAL_INDEX_REGISTRY"] = MonoStateIndexManager._INTERNAL_INDEX_REGISTRY
    
class IndexCreationError(Exception):
    """Raised when an error occurs during index creation."""
    pass


class IndexManager(MonoStateIndexManager):
    
    """
    This module makes the decision to create a new index (should I create a new index?)
    It does the following:
    
    1. It checks that the request is coming from a specific client
    2. It retrieves the index schema for that client via CustomerIndexSchemaManager
    3. It checks the index creation strategy for the client
        a. If the strategy is DEFAULT, it creates a new index with the client's name if it does not exist
        b. If the strategy is KEYED, it creates a new index with the client's name and the index key if it does not exist
    4. It saves the index to the internal index registry, which maps clients to their respective indices under the specified key (if applicable)
    
    """

    key_vault_url = 'https://kv-indcopilot-llmops-dev.vault.azure.net/'
    _INDEX_COLLECTION_NAME = 'indexes'
    _COSMOSDB_DATABASE = 'rag_doc_manager'
    
    def __init__(self, customer_id: str, account_id: str):
        
        self.customer_id = customer_id
        self.account_id = account_id


        self.key_vault = AzureKeyVaultStore(
            config={
                'vault_url': IndexManager.key_vault_url
            }
        )

        self.search_service = self.key_vault.get_secret('aisearch-endpoint')

        self.index_collection = CosmosDBClient(connection_string=self.key_vault.get_secret("cosmosdb-connection-string"), database_name=IndexManager._COSMOSDB_DATABASE, collection_name=IndexManager._INDEX_COLLECTION_NAME, primary_key = "index_name")

    def _get_index_config(self) -> Self:
        
        self.client_index_config = self.client_index_schema_manager.get_index_config(self.customer_id)

        if not self.client_index_config:
            raise IndexCreationError(f"Failed to retrieve index configuration for client {self.customer_id}")
        
        return self
    
    def _create_unique_index_name(self) -> Self:

        try:
            
            if self.client_index_config.indexing_strategy_config == IndexingStrategy.DEFAULT:
                self.index_name = f"{self.customer_id}"
            
            else:
                self.index_name = f"{self.customer_id}"

        except Exception as e:
            raise IndexCreationError(f"Failed to create a new index for client {self.customer_id}: {str(e)}")
        
        
    
    def _need_to_create_new_index(self, index_maintainer: Index) -> bool:
        
        if index_maintainer.check_index_exists(self.index_name):
            return False
        
        return True

    def create_new_index(self, user_id: str, client_index_schema_manager: CustomerIndexSchemaManager) -> None:
        
        self.client_index_schema_manager = client_index_schema_manager
        self._get_index_config()
        self._create_unique_index_name()
        
        index_client = AISearchIndexClient(ais_service_name = self.search_service, index_name = self.index_name)
        try:
            if self._need_to_create_new_index(index_client):
                index_metadata = IndexMetadata(name=self.index_name, config=self.client_index_config)
                index_client.create_index(index_metadata)

                try:
                    index_record = IndexRecord(customer_id=self.customer_id, index_name=self.index_name, account_ids={self.account_id}, document_ids=[], created_at=datetime.datetime.now(datetime.UTC).isoformat(), admin_id=user_id, updated_at=datetime.datetime.now(datetime.UTC).isoformat())
                    self.index_collection.insert_record(record_data=index_record.model_dump(), record_id=self.index_name)
                except Exception as e:
                    raise Exception(f"Failed to create record for index: {self.index_name}: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to create index {self.index_name}: {str(e)}")  
        
    def delete_index(self):
        raise NotImplementedError
    
    def list_indices(self):
        raise NotImplementedError

    def update_docs_in_index_record(self, document_id, action):
        """ Updates the index record in the indexes collection.
        If new document was added, document is added to the index record.
        If document was deleted, document is removed from the index record.

        Args:
            document_id (str): The document id.
            action (str): The action to be performed. Either 'add' or 'delete'.
        
        Returns:
        -------
            bool: True if the record was successfully updated, False otherwise.
        """
        #TODO: Update to customer id search
        self.index_name = self.customer_id

        # Get the index record
        index_record = self.index_collection.get_record(record_id=self.index_name)
        
        if index_record:
            if action == 'add':
                index_record["document_ids"].append(document_id)
            elif action == 'delete':
                index_record["document_ids"].remove(document_id)
            else:
                logger.error(f"Invalid action: {action}")
                return False
            self.index_collection.update_or_create_record(
                updated_data=index_record,
                record_id=self.index_name
            )
            return True
        else:
            logger.warning(f"Index record not found for index name {self.index_name}. Could not update record.")
            return False 
