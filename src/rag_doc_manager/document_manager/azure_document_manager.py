import os
from dotenv import load_dotenv
from pathlib import Path
import logging
from typing import Optional

from rag_doc_manager.document_manager.base import DocumentManager, Scope
from rag_doc_manager.storage.secrets.azure_key_vault import AzureKeyVaultStore
from rag_doc_manager.storage.object.azure_blob_storage import AzureBlobStorage
from rag_doc_manager.document_processor.embedders.factory import EmbedderFactory
from rag_doc_manager.document_processor.processor import DocumentProcessor
from rag_doc_manager.index.adaptors.azure_ai_indexing_engine import AISearchIndexClient
from rag_doc_manager.storage.database_manager.cosmosdb_manager import CosmosDBClient
from rag_doc_manager.document_manager.data_models.models import DocumentRecord
from rag_doc_manager.index_manager.index_manager import IndexManager

logger = logging.getLogger(__name__)


class AzureDocumentManager(DocumentManager):

    key_vault_url = 'https://kv-indcopilot-llmops-dev.vault.azure.net/'
    _DOCUMENT_COLLECTION_NAME = 'documents'
    _COSMOSDB_DATABASE = 'rag_doc_manager'

    def __init__(self, customer: str, account_id: str):

        super().__init__(customer)
        self.customer_id = customer
        self.account_id = account_id

        # call all the factories and get the relevant object
        self.key_vault = AzureKeyVaultStore(
            config={
                'vault_url': AzureDocumentManager.key_vault_url
            }
        )

        embedder = EmbedderFactory.create_embedder(
            'azure',
            #api_key=self.key_vault.get_secret("openai-api-key"),
            endpoint=self.key_vault.get_secret("azure-openai-endpoint"),
            deployment_name='text-embedding-ada-002'
        )

        self.object_storage = AzureBlobStorage(
            connection_string=self.key_vault.get_secret("blob-service-connection-string"),
            container_name='rag-doc-manager-blob'
        )


        self.processor = DocumentProcessor(
            embedder=embedder
        )

        self.document_collection = CosmosDBClient(
            connection_string=self.key_vault.get_secret("cosmosdb-connection-string"),
            database_name=AzureDocumentManager._COSMOSDB_DATABASE,
            collection_name=AzureDocumentManager._DOCUMENT_COLLECTION_NAME,
            primary_key = "document_id"
        )
        self.index_manager =IndexManager(
            customer_id = self.customer, account_id = self.account_id)


    def upload(
        self,
        index_name: str,
        file: str,
        account_id: Optional[str] = None, # optional to make scopes optional
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        scope: Optional[str] = 'global'
    ):

        self.indexing_engine = AISearchIndexClient(
            ais_service_name=self.key_vault.get_secret("aisearch-endpoint"),
            index_name=index_name
        )

        #TODO: Add file metadata
        # BUG: session_id should be optional
        destination_prefix = f'{self.customer}'
        print(scope)
        if scope == 'account':
            assert account_id, "account ID must be provided for session-specific indexing"
            destination_prefix = f'{destination_prefix}/{account_id}'
        elif scope == 'user':
            assert user_id, "user ID must be provided for user-specific indexing"
            destination_prefix = f'{destination_prefix}/{account_id}/{user_id}'
        elif scope == 'session':
            destination_prefix = f'{destination_prefix}/{account_id}/{user_id}/{session_id}'
        else:
            assert scope == 'global'

        self.object_storage.upload_file(file, destination_prefix=destination_prefix, additional_metadata={})
        
        chunked_documents = self.processor.process_document(
            file_path=file,
            account_id=account_id,
            user_id=user_id,
            is_global=True if scope == 'global' else False,
            session_id=session_id
        )
        
        document_id = chunked_documents[0].document_id

        # index documents
        self.indexing_engine.index_documents(documents=chunked_documents)
        document_record = DocumentRecord(
            document_id=document_id,
            customer_id=self.customer,
            index_name=index_name,
            account_id=account_id,
            user_id=user_id,
            session_id=session_id,
            scope=str(scope),
            document_url=os.path.join(destination_prefix, file),
            document_name=os.path.basename(file),
            document_size=os.path.getsize(file),
            document_indexed=True,
            indexed_at=chunked_documents[0].created_at,
            chunk_ids=[doc.chunk_id for doc in chunked_documents]
        )
        self._update_document_record(document_record)

        # Update index record
        self.index_manager.update_docs_in_index_record(document_id = document_id, action= "add")


    def _update_document_record(
        self,
        document_record: DocumentRecord
    ) -> bool:
        """ Inserts the document record in the documents collection.

        Args:
            document_record (DocumentRecord): The document record to be inserted.

        Returns
        -------
            bool: True if the record was successfully inserted, False otherwise.
        """
        try:
            self.document_collection.update_or_create_record(
                updated_data=document_record.model_dump(),
                record_id=document_record.document_id
            )
            return True
        except Exception as e:
            logger.error(f"Error inserting document record for document id {document_record.document_id}: {e}")
            return False

    def _delete_document_record(self, document_id):
        """ Deletes the document record from the documents collection."""
        pass

       



    def delete(
        self,
        document_id: str,
        user_id: str
    ):
        """Deletes a document from the index in blob_storage."""

        # Check user is the owner of the document or the account admin
        

        document_record = self.document_collection.get_record(
            record_id=document_id
            )
        
        if self.is_user_authorized(user_id=user_id, document_record=document_record):
            
            
            #TODO: Delete the document from the blob storage
            document_url = document_record.get('document_url')
            if document_url:
                #TODO: Add error handling
                self.object_storage.delete_file(file_url=document_url)

            #TODO: Change index name to not assume customer_id
            self.indexing_engine = AISearchIndexClient(
            ais_service_name=self.key_vault.get_secret("aisearch-endpoint"),
            index_name=self.customer_id
        )

            # Delete the document from the index
            self.indexing_engine.delete_document(document_id=document_id)

            # Delete the document record from the database
            self.document_collection.delete_record(record_id=document_id)

            # Update index record
            self.index_manager.update_docs_in_index_record(document_id = document_id, action= "delete")

        else:
            raise Exception(f"Document with id: {document_id} not found or user is not authorized to delete the document.")


    def is_user_authorized(self, user_id: str, document_record: dict) -> bool:
        """Checks if the user is authorized to access the document.
        
        Args:
            user_id (str): The user id of the user making the request.
            document_record (dict): The document record to be checked.
        """

        #TODO: Allow admin to update documents in index
        # customer_record = self.index_manager.index_collection.get_record(record_id=self.customer_id)
        # admin_id = customer_record.get('admin_user')

        if document_record:
            document_user = document_record.get('user_id')
            return document_user == user_id
        else:
            return False



        
        
        
        
        
        
        
        
        
        
        



















        