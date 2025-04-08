from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Header, Request
from fastapi.responses import JSONResponse
from fastapi import status
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Type, Annotated
import uuid
from pathlib import Path


from rag_doc_manager.document_manager.azure_document_manager import AzureDocumentManager
from rag_doc_manager.document_manager.base import DocumentManager
from rag_doc_manager.utils.io import save_bytes_as_file
from rag_doc_manager.customer_manager.remote_customer_schema_manager import CustomerIndexSchemaManager
from rag_doc_manager.customer_manager.data_models.models import IndexConfig
from rag_doc_manager.index_manager.index_manager import IndexManager
from rag_doc_manager.index.adaptors.azure_ai_indexing_engine import AISearchIndexClient
from rag_doc_manager.storage.secrets.azure_key_vault import AzureKeyVaultStore




router = APIRouter(prefix='/documents', tags=['documents'])


class DeleteDocumentRequest(BaseModel):
    customer_id: str
    account_id: str
    user_id: str
    document_id: str




# class IndexDocumentRequest(BaseModel):
#     #request: Request
#     document_url: Optional[HttpUrl] = None

class IndexDocumentHeaders(BaseModel):
    customer_id: str = Field(..., description="Customer ID")
    account_id: str = Field(..., description="Account ID under the customer")
    user_id: str = Field(..., description="ID of the user indexing documents")
    file_name: str = Field(..., description="Name of the file (must be unique)")
    session_id: Optional[str] = Field(None, description="Chat session ID") # not treated as optional  in the upload function
    scope: Optional[str] = Field(default='global', description="Scope (session, user, account, or global)")




@router.post("/index_document")
async def index_document(
        headers: Annotated[IndexDocumentHeaders, Header()],
        request: Request
):
    try:
        # construct parent dir
        user_dir = Path(headers.customer_id) / headers.user_id
        user_dir.mkdir(exist_ok=True, parents=True)  # Added parents=True for consistency

        if headers.session_id:
            user_dir = user_dir / headers.session_id

        user_dir.mkdir(exist_ok=True, parents=True)  # Added parents=True for consistency

        # save the file
        # Fixed: You need to await the body() method and use the request object from request_with_headers
        body_content = await request.body()
        file_info = save_bytes_as_file(file_content=body_content, parent_dir=user_dir, file_name=headers.file_name)

        document_manager = AzureDocumentManager(customer=headers.customer_id, account_id=headers.account_id)

        document_manager.upload(
            index_name=headers.customer_id,
            account_id=headers.account_id,
            user_id=headers.user_id,
            session_id=headers.session_id,
            file=file_info['file_path'],
            scope=headers.scope
        )

        return file_info
    except Exception as e:
        raise
        # return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)





@router.delete("/delete_document")
def delete_document(request: DeleteDocumentRequest):
    """Delete a document from the index and remove it from the storage."""
    try:
        document_manager = AzureDocumentManager(customer=request.customer_id, account_id=request.account_id)
        document_manager.delete(
            document_id=request.document_id,
            user_id=request.user_id

        )
        return JSONResponse(content={"message": "Document deleted successfully"}, status_code=status.HTTP_200_OK)	
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def download_file_from_bytes():
    pass