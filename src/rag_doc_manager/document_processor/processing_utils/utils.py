from enum import Enum
from pathlib import Path
from typing import Union

class FileType(str, Enum):
    
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    CSV = "csv"
    XLSX = "xlsx"
    PPTX = "pptx"
    HTML = "html"
    JSON = "json"
    MD = "md"
    
    @classmethod
    def from_path(cls, path: Union[str, Path]) -> 'FileType':
        
        if isinstance(path, str):
            path = Path(path)
        extension = path.suffix.strip('.').lower()
        
        try:
            return cls(extension)
        except ValueError:
            raise ValueError(f"Unsupported file type: {extension}")
        