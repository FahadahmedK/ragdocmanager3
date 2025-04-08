from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class DocumentHistoryRecord:
    """
    Data class for storing
    document modification history.
    """
    
    document_id: str
    user_id: str
    account_id: str
    customer_id: str # to think about generating this
    status: str 
    timestamp: float = field(default_factory=time.time)
    


class DocumentHistoryStore(ABC):

    """
    Abstract base class for storing document modification history.
    This defines the interface for tracking document changes.
    """
    
    @abstractmethod
    async def record_document_action(
        self,
        document_history_record: DocumentHistoryRecord
    ):
        pass
    
    
    @abstractmethod
    async def get_document_history(
        self,
        document_id: str # will be unique per customer, per account
    ) -> DocumentHistoryRecord: # to record each action per call or only the last action ? # for now, only the last action
        pass


