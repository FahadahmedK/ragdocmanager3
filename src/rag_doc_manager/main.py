from fastapi import FastAPI
from rag_doc_manager.api.routes.registration import router as registration_router
from rag_doc_manager.api.routes.documents import router as documents_router
from rag_doc_manager.api.routes.search import router as search_router

app = FastAPI(root_path="/api/v1")


@app.get('/')
def root_message():
    return {
        'message': 'The server is running'
    }

@app.get('/health')
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Include the users router with a prefix of '/api/v1'
app.include_router(registration_router)
app.include_router(documents_router)
app.include_router(search_router)