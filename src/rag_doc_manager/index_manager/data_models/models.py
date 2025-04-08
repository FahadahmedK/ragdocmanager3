from pydantic import BaseModel
from dataclasses import dataclass, field
from datetime import datetime

    
class IndexRecord(BaseModel):
    customer_id: str
    index_name: str
    account_ids: list[str]
    document_ids: list[str]
    created_at: datetime
    updated_at: datetime
    admin_id: str