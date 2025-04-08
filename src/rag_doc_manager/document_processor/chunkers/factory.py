from enum import Enum
from typing import Optional, List, Dict, Any, Union, Literal
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter,
    MarkdownTextSplitter,
    PythonCodeTextSplitter,
    Language,
)

from langchain_text_splitters.html import HTMLSemanticPreservingSplitter

from ..processing_utils.utils import FileType


class ChunkingStrategy(str, Enum):
    
    BASE = "base"
    SEMANTIC = "semantic"
    TOKEN = "token"
    


class ChunkerFactory:



    @staticmethod
    def get_splitter(
        chunking_strategy: str = ChunkingStrategy.BASE,
        file_type: Optional[str] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        **kwargs,
        # add config for semantic chunking
    ):

            
        chunking_strategy = chunking_strategy.lower()
        
        if chunking_strategy == ChunkingStrategy.BASE:
            assert file_type, "file_type must be provided when using the base chunking strategy"
            
            if isinstance(file_type, str):
                file_type = FileType(file_type.strip('.').lower())
            
            if file_type == FileType.MD: # markdown
                return MarkdownTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
                
            elif file_type in [FileType.PDF, FileType.DOCX, FileType.TXT]:
                
                return RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    separators=["\n\n", "\n", " ", ""]
                )
            
            elif file_type == FileType.PPTX:
                return RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    separators=["\n", " ", ""]
                )
            
            elif file_type == FileType.HTML:
                return HTMLSemanticPreservingSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
                
            else: 
                raise ValueError(f"file type {file_type} does not exist")
    
    
        elif chunking_strategy == ChunkingStrategy.TOKEN:
            return TokenTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                encoding_name=kwargs.get('encoding_name', 'cl100k_base')
            )
    