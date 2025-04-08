import logging

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError



logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CosmosDBClient:

    _mongo_client = None

    def __init__(self, connection_string: str, database_name: str, collection_name: str, primary_key: str = "_id"):
        """Initialize connection to Cosmos DB using the MongoDB API via PyMongo. 
        """
        if CosmosDBClient._mongo_client is None:
            # Only create MongoClient once
            CosmosDBClient._mongo_client = MongoClient(connection_string)
        
        self.client = CosmosDBClient._mongo_client
        self.database = self.client[database_name]
        self.collection = self.database[collection_name]
        self.primary_key = primary_key

    def insert_record(self, record_data: dict, record_id: str)-> bool:
        """Insert or replace a record"""
        try:
            # Upsert: Insert if not exists, update if exists
            self.collection.replace_one({self.primary_key: record_id}, record_data, upsert=True)
        except DuplicateKeyError as e:
            print(f"Duplicate record found: {e}")

    def get_record(self, record_id: str) -> dict:
        """Retrieve a record by ID. If not found, return None"""
        return self.collection.find_one({self.primary_key: record_id})

    def query_records(self, query: str) -> list:
        """Query records with MongoDB query syntax. This is an implementation of the find method in PyMongo."""
        return list(self.collection.find(query))

    def get_records(self) -> list:
        """Get all record ids in the collection. This is an implementation of the distinct method in PyMongo."""
        return list(self.collection.distinct(self.primary_key))

    def update_or_create_record(self, record_id: str, updated_data: dict) -> bool:
        """Update an existing record or create a new one if it doesn't exist"""
        try:
            result = self.collection.update_one(
                {self.primary_key: record_id},
                {"$set": updated_data},
                upsert=True  # This ensures a new record is created if not found
            )
            
            if result.matched_count > 0:
                logger.info(f"Record {record_id} updated successfully.")
                return True
            else:
                logger.info(f"Record {record_id} created successfully.")
                return True
        except Exception as e:
            logger.error(f"An error occurred when updating record: {str(e)}")
            return False

    def delete_record(self, record_id: str)-> bool:
        """Delete a record by ID"""
        result = self.collection.delete_one({self.primary_key: record_id})
        return result.deleted_count > 0
    
    def delete_collection(self):
        """Delete the entire collection"""
        try:
            self.database.drop_collection(self.collection.name)
            print(f"Collection {self.collection.name} deleted successfully.")
        except Exception as e:
            print(f"Error deleting collection: {e}")

    def close(self):
        """Close the connection to the database"""
        self.client.close()