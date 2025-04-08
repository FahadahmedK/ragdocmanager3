from pydantic import BaseModel
from dataclasses import dataclass,field

from datetime import datetime

class DocumentRecord(BaseModel):
    document_id: str
    customer_id: str
    index_name: str
    account_id: str
    user_id: str
    session_id: str
    scope: str
    document_url: str
    document_name: str
    document_size: int
    document_indexed: bool
    indexed_at: datetime
    chunk_ids: list
