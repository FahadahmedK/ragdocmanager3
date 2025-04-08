from typing import Union
from pathlib import Path

from langchain_community.document_loaders import (
    TextLoader, 
    PyMuPDFLoader, 
    Docx2txtLoader,
    CSVLoader,
    UnstructuredExcelLoader,
    UnstructuredPowerPointLoader,
    BSHTMLLoader,
    JSONLoader,
    UnstructuredMarkdownLoader
)

from ..processing_utils.utils import FileType

class DocumentLoaderFactory:
    
    _document_parsers = {
        FileType.PDF: PyMuPDFLoader,
        FileType.DOCX: Docx2txtLoader,
        FileType.TXT: TextLoader,
        FileType.CSV: CSVLoader,
        FileType.XLSX: UnstructuredExcelLoader,
        FileType.PPTX: UnstructuredPowerPointLoader,
        FileType.HTML: BSHTMLLoader,
        FileType.JSON: JSONLoader,
        FileType.MD: UnstructuredMarkdownLoader
    }
    
    @classmethod
    def get_loader(cls, file_path: Union[str, Path]):
        
        file_type = FileType.from_path(file_path)
        
        loader_cls = cls._document_parsers[file_type]
        
        return loader_cls(file_path)
    


def loader(file_type: FileType):
    def register_loader(document_loader_cls):
        DocumentLoaderFactory.register_loader(file_type, document_loader_cls)
        return document_loader_cls
    return register_loader 
        
  
    
