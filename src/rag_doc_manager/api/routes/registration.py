from pydantic import BaseModel
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from rag_doc_manager.customer_manager.remote_customer_schema_manager import CustomerIndexSchemaManager
from rag_doc_manager.customer_manager.data_models.models import IndexConfig
from rag_doc_manager.index_manager.index_manager import IndexManager

router = APIRouter(prefix='/register', tags=['registration'])


class CreateAccountRequest(BaseModel):
    customer_id: str
    account_id: str
    admin_id: str
    #body: Optional[IndexConfig] = None



@router.post("/create_customer")
def create_account(request: CreateAccountRequest):
    """Create an account for a given customer. Save a record with configuration state to database (cosmosdb) and create customer index."""
    try:
        customer_manager = CustomerIndexSchemaManager()
        index_schema = customer_manager.create_default_index()
        customer_manager.register_customer(request.customer_id, index_schema)
        index_manager = IndexManager(customer_id = request.customer_id, account_id = request.account_id)
        index_manager.create_new_index(user_id = request.admin_id, client_index_schema_manager = customer_manager)

        #TODO: Change message when account already exists, improve error handling
        return JSONResponse(content={"message": f"Account created successfully for customer: {request.customer_id}"}, status_code=status.HTTP_200_OK)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
