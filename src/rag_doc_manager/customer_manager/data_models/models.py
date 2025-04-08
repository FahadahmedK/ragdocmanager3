from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, field_validator, Field



class IndexingStrategy(str, Enum):
    DEFAULT = "shared"
    KEYED = "keyed"  # multiple indices based on keys

class IndexingStrategyConfig(BaseModel):
    strategy: IndexingStrategy = Field(default=IndexingStrategy.DEFAULT)
    index_key: Optional[str] = None
    
    @field_validator("index_key")
    def validate_index_key(cls, v, info):  # renamed `values` to `info`
        if info.data.get("strategy") == IndexingStrategy.DEFAULT and v is not None:
            raise ValueError("Index key should not be provided for default indexing strategy")
        if info.data.get("strategy") == IndexingStrategy.KEYED and v is None:
            raise ValueError("Index key should be provided for keyed indexing strategy")
        return v

    class Config:
        use_enum_values = True

class IndexField(BaseModel):
    name: str
    field_type: str
    filterable: Optional[bool] = False  
    searchable: Optional[bool] = False  
    sortable: Optional[bool] = False
    primary_key: Optional[bool] = False
    
    @field_validator("field_type")
    def validate_type(cls, v, info):
        valid_types = ["string", "date", "integer", "float", "boolean"]
        if v not in valid_types:
            raise ValueError(f"Invalid type: {v}. Must be one of {valid_types}")
        return v

class IndexSchema(BaseModel):
    fields: List[IndexField]
    vector_dimensions: Optional[int] = None

class IndexConfig(BaseModel):
    """
    Schema of the index to be created per use-case (perhaps even per tenant)
    """
    index_schema: IndexSchema
    indexing_strategy_config: IndexingStrategyConfig
    description: Optional[str] = None
    additional_settings: Dict[str, Any] = Field(default_factory=dict)

class Customer(BaseModel):
    customer_id: str # unique (primary key)
    index_config: IndexConfig  # same index config for each client

class IndexSchemaManagerState(BaseModel):
    customer_list: List[Customer] = Field(default_factory=list)

# Subclass for managing Customer Records
class CustomersRecord(Customer):
    pass