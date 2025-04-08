from typing import Optional, Dict, Any, List
import os
import json
import logging

from ..customer_manager.data_models.models import IndexConfig, Customer, IndexSchemaManagerState
from rag_doc_manager.customer_manager.data_models.models import IndexSchema, IndexField, IndexConfig, IndexingStrategyConfig
from rag_doc_manager.storage.database_manager.cosmosdb_manager import CosmosDBClient
from rag_doc_manager.storage.secrets.azure_key_vault import AzureKeyVaultStore

logger = logging.getLogger(__name__)


class CustomerIndexSchemaManager:
    
    """
    This class maintains a region-wise shared state containing customers and their index schemas
    """
    
    _COSMOSDB_STATE_COLLECTION = "customer_index_mapping"
    _DEFAULT_INDEX_FILE_PATH = os.path.join("data_models","default_index_schema.json")
    _COSMOSDB_DATABASE = "rag_doc_manager"
    keyvault_url = "https://kv-indcopilot-llmops-dev.vault.azure.net/"

    
    _instance = None

    def __new__(cls, *args, **kwargs):
        # initialize if not initialized
        if cls._instance is None:
            cls._instance = super(CustomerIndexSchemaManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):

        #TODO: Use CustomerCollection instead of CosmosDBClient
        self.kv_client = AzureKeyVaultStore(config={"vault_url": CustomerIndexSchemaManager.keyvault_url})
        self.cosmosdb_client = CosmosDBClient(connection_string=self.kv_client.get_secret("cosmosdb-connection-string"), database_name=CustomerIndexSchemaManager._COSMOSDB_DATABASE, collection_name=CustomerIndexSchemaManager._COSMOSDB_STATE_COLLECTION, primary_key = "customer_id")
        self._state = None

    def customer_exists(self, customer_id: str) -> bool:
        try:
            record = self.cosmosdb_client.get_record(customer_id)
            if record and record.get("customer_id") == customer_id:
                return True
            else:
                logger.warning(f"Customer with id '{customer_id}' not found.")
                return False
        except Exception as e:
            raise Exception(f"Customer with id '{customer_id}' not found :{e}")
            return False

    def register_customer(self, customer_id: str, index_config: IndexConfig) -> bool:
        """Register a new customer with the given id and index config"""
        if self.customer_exists(customer_id=customer_id):
            logger.error(f"Customer with name '{customer_id}' already exists")
            return False

        try:
            self.cosmosdb_client.insert_record(record_data= Customer(customer_id=customer_id, index_config=index_config).model_dump(), record_id= customer_id)
            logger.info(f"Registered customer: {customer_id}")   
            return True
        except Exception as e:
            #TODO: Implement better error handling
            logger.error(f"Could not register customer with name: {customer_id}: {e}")
            return False
        

    def get_index_config(self, customer_id: str) -> Optional[IndexConfig]:
        """Get the index config for the customer with the given name"""
        if self.customer_exists(customer_id):
            customer_record = self.cosmosdb_client.get_record(record_id=customer_id)
            if customer_record.get("index_config"):
                return IndexConfig.parse_obj(customer_record.get("index_config"))
            else:
                logger.error(f"Index config for '{customer_id}' not found")
                return None
        else:
            return None
        
        

    def update_index_config(self, customer_id: str, index_config: IndexConfig) -> bool:
        """Update the index config for the customer with the given name"""
        if self.customer_exists(customer_id):
            try:
                self.cosmosdb_client.create_or_update_record(record_id=customer_id, updated_data=Customer(customer_id=customer_id, index_config=index_config).model_dump())
                logger.info(f"Updated index config for customer: {customer_id}")
                return True
            except Exception as e:
                raise Exception(f"Index config for '{customer_id}' failed with error: {e}")
        else:
            logger.error(f"Could not update infex config for customer with name '{customer_id}'")
            return False



    def delete_customer(self, customer_id: str) -> bool:
        """Delete the customer with the given name"""
        if self.customer_exists(customer_id):
            try:
                self.cosmosdb_client.delete_record(record_id=customer_id)
                logger.info(f"Deleted customer: {customer_id}")
                return True
            except Exception as e:
                raise Exception(f"Deletion of customer with name '{customer_id}' failed with error: {e}")
                return False
            #TODO: Implement deletion of index?
            return True
        else:
            logger.error(f"Customer with name '{customer_id}' not found")
            return False


    def list_customers(self) -> List[str]:
        """Return a list of all customer names"""
        try:
            return self.cosmosdb_client.get_records()
        except Exception as e:
            raise Exception(f"Error listing customers: {e}")
            return None
    
    @staticmethod
    def create_default_index() -> IndexConfig:
        """Create a default index definition for the customer with the given name"""
        schema_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),CustomerIndexSchemaManager._DEFAULT_INDEX_FILE_PATH)
        with open(schema_file_path, "r") as f:
            index_config_data = json.load(f)
        fields = [IndexField(**field_data) for field_data in index_config_data["index_fields"]]
        index_config = IndexConfig(
            index_schema=IndexSchema(fields=fields, vector_dimensions=1536),
            indexing_strategy_config=IndexingStrategyConfig(),
            description="Default index configuration."
        )
        #self.update_index_config(customer_name, index_config)
        return index_config



