import os
import uuid
from typing import Union, List, Optional, Dict, Any, Annotated
from pathlib import Path
from .document_loaders.factory import DocumentLoaderFactory
from .chunkers.factory import ChunkerFactory
from .embedders.base import Embedder
from .embedders.factory import EmbedderFactory
from rag_doc_manager.index.data_models.models import Document
from .processing_utils.utils import FileType
from langchain.schema import Document as LangchainDocument

class DocumentProcessor:
    """
    A modular document processor that handles loading, chunking, and embedding documents.
    
    This class combines the DocumentLoaderFactory, ChunkerFactory, and EmbedderFactory
    to provide a complete document processing pipeline. It processes documents and 
    returns structured Document objects ready for indexing.
    
    Parameters
    ----------
    embedder : Embedder
        The embedder instance to use for generating embeddings.
    chunking_strategy : str, optional
        The strategy to use for chunking documents, by default "base".
    chunk_size : int, optional
        The size of chunks to create, by default 1000.
    chunk_overlap : int, optional
        The overlap between chunks, by default 100.
    chunking_kwargs : dict, optional
        Additional arguments to pass to the chunker.
    """
    
    def __init__(
        self,
        embedder: Embedder,
        chunking_strategy: str = "base",
        chunk_size: int = 50,
        chunk_overlap: int = 10,
        **chunking_kwargs
    ):
        self.embedder = embedder
        self.chunking_strategy = chunking_strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunking_kwargs = chunking_kwargs
    
    def _generate_document_id(self, file_path: Union[str, Path]) -> str:
        """
        Generate a unique document ID based on the file path.
        
        Parameters
        ----------
        file_path : Union[str, Path]
            The path to the document file.
            
        Returns
        -------
        str
            A unique document ID.
        """
        path = Path(file_path)
        return f'{path.stem}'   #document id to be the file name #_{uuid.uuid4().hex[:8]}"
    
    def _generate_chunk_id(self, document_id: str, chunk_index: int) -> str:
        """
        Generate a unique chunk ID based on the document ID and chunk index.
        
        Parameters
        ----------
        document_id : str
            The parent document ID.
        chunk_index : int
            The index of the chunk within the document.
            
        Returns
        -------
        str
            A unique chunk ID.
        """
        return f"{document_id}_chunk_{chunk_index}"
    
    def _load_document(self, file_path: Union[str, Path]) -> List[LangchainDocument]:
        """
        Load a document using the appropriate loader from DocumentLoaderFactory.
        
        Parameters
        ----------
        file_path : Union[str, Path]
            The path to the document file.
            
        Returns
        -------
        List[LangchainDocument]
            The loaded document(s) in Langchain format.
        """
        loader = DocumentLoaderFactory.get_loader(file_path)
        return loader.load()
    
    def _chunk_document(
        self, 
        langchain_docs: List[LangchainDocument], 
        file_type: Optional[FileType] = None
    ) -> List[LangchainDocument]:
        """
        Split loaded documents into chunks using the configured chunking strategy.
        
        Parameters
        ----------
        langchain_docs : List[LangchainDocument]
            The loaded documents to chunk.
        file_type : Optional[FileType], optional
            The type of the file being processed, by default None.
            
        Returns
        -------
        List[LangchainDocument]
            The chunked documents in Langchain format.
        """
        text_splitter = ChunkerFactory.get_splitter(
            chunking_strategy=self.chunking_strategy,
            file_type=file_type,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            **self.chunking_kwargs
        )
        
        return text_splitter.split_documents(langchain_docs)
    
    def _embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        """
        Generate embeddings for document chunks.
        
        Parameters
        ----------
        chunks : List[str]
            The chunks of text to embed.
            
        Returns
        -------
        List[List[float]]
            The embeddings for each chunk.
        """
        return self.embedder.embed_texts(chunks)
    
    def _convert_to_documents(
        self,
        langchain_docs: List[LangchainDocument],
        document_id: str,
        account_id: Optional[str],
        user_id: Optional[str],
        is_global: bool,
        session_id: Optional[str],
        embeddings: List[List[float]]
    ) -> List[Document]:
        """
        Convert Langchain documents to our Document model.
        
        Parameters
        ----------
        langchain_docs : List[LangchainDocument]
            The chunked Langchain documents.
        document_id : str
            The ID of the parent document.
        account_id : Optional[str]
            The account ID for the document.
        user_id : Optional[str]
            The user ID for the document.
        is_global : bool
            Whether the document is globally accessible.
        embeddings : List[List[float]]
            The embeddings for each document chunk.
            
        Returns
        -------
        List[Document]
            A list of Document objects ready for indexing.
        """
        documents = []
        
        for idx, (doc, embedding) in enumerate(zip(langchain_docs, embeddings)):
            chunk_id = self._generate_chunk_id(document_id, idx)
            
            # Create a Document object for each chunk
            document = Document(
                account_id=account_id,
                user_id=user_id,
                document_id=document_id,
                chunk_id=chunk_id,
                chunk_position=idx,
                content=doc.page_content,
                is_global=is_global,
                session_id = session_id,
                metadata=doc.metadata,
                embedding=embedding,

            )
            
            documents.append(document)
        
        return documents
    
    def process_document(
        self,
        file_path: Union[str, Path],
        account_id: Optional[str] = None,
        user_id: Optional[str] = None,
        is_global: bool = False,
        document_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Process a document through the entire pipeline: loading, chunking, and embedding.
        
        Parameters
        ----------
        file_path : Union[str, Path]
            The path to the document file.
        account_id : Optional[str], optional
            The account ID for the document, by default None.
        user_id : Optional[str], optional
            The user ID for the document, by default None.
        is_global : bool, optional
            Whether the document is globally accessible, by default False.
        document_id : Optional[str], optional
            The ID to use for the document, by default None (will be generated).
        session_id : Optional[str], optional
            The ID of the chat session, by default None.
        metadata : Optional[Dict[str, Any]], optional
            Additional metadata to include with the document, by default None.
            
        Returns
        -------
        List[Document]
            A list of processed Document objects ready for indexing.
        """
        # Generate or use provided document ID
        doc_id = document_id or self._generate_document_id(file_path)
        
        # Load document
        langchain_docs = self._load_document(file_path)
        
        # Extract file type for chunking
        file_type = FileType.from_path(file_path)
        
        # Add file metadata if provided
        if metadata:
            for doc in langchain_docs:
                doc.metadata.update(metadata)
                
        # Add file path and other basic metadata
        path_obj = Path(file_path)
        for doc in langchain_docs:
            doc.metadata.update({
                # "source": str(path_obj),
                # "filename": path_obj.name,
                "file_type": str(file_type.value),
                "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else None,
            })
        
        # Chunk document
        chunked_docs = self._chunk_document(langchain_docs, file_type)
        
        # Extract text content for embedding
        chunk_texts = [doc.page_content for doc in chunked_docs]
        
        # Generate embeddings
        embeddings = self._embed_chunks(chunk_texts)
        
        # Convert to Document objects
        documents = self._convert_to_documents(
            chunked_docs, 
            doc_id, 
            account_id, 
            user_id, 
            is_global, 
            session_id,
            embeddings
        )
        
        return documents
    
    def process_documents(
        self,
        file_paths: List[Union[str, Path]],
        account_id: Optional[str] = None,
        user_id: Optional[str] = None,
        is_global: bool = False,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Process multiple documents in batch.
        
        Parameters
        ----------
        file_paths : List[Union[str, Path]]
            A list of paths to document files.
        account_id : Optional[str], optional
            The account ID for the documents, by default None.
        user_id : Optional[str], optional
            The user ID for the documents, by default None.
        is_global : bool, optional
            Whether the documents are globally accessible, by default False.
        session_id : Optional[str], optional
            The ID of the chat session, by default None.
        metadata : Optional[Dict[str, Any]], optional
            Additional metadata to include with all documents, by default None.
            
        Returns
        -------
        List[Document]
            A list of all processed Document objects ready for indexing.
        """
        all_documents = []
        
        for file_path in file_paths:
            documents = self.process_document(
                file_path=file_path,
                account_id=account_id,
                user_id=user_id,
                is_global=is_global,
                session_id=session_id,
                metadata=metadata
            )
            all_documents.extend(documents)

        return all_documents

    def process_text(
        self,
        text: str,
        account_id: Optional[str] = None,
        user_id: Optional[str] = None,
        is_global: bool = False,
        document_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Process a text string through chunking and embedding.

        Parameters
        ----------
        text : str
            The text content to process.
        account_id : Optional[str], optional
            The account ID for the document, by default None.
        user_id : Optional[str], optional
            The user ID for the document, by default None.
        is_global : bool, optional
            Whether the document is globally accessible, by default False.
        document_id : Optional[str], optional
            The ID to use for the document, by default None (will be generated).
        metadata : Optional[Dict[str, Any]], optional
            Additional metadata to include with the document, by default None.

        Returns
        -------
        List[Document]
            A list of processed Document objects ready for indexing.
        """
        # Generate or use provided document ID
        doc_id = document_id

        # Create a LangchainDocument from the text
        langchain_doc = LangchainDocument(
            page_content=text,
            metadata=metadata or {}
        )

        # Chunk the document
        text_splitter = ChunkerFactory.get_splitter(
            chunking_strategy=self.chunking_strategy,
            file_type=None,  # No file type for raw text
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            **self.chunking_kwargs
        )

        chunked_docs = text_splitter.split_documents([langchain_doc])

        # Extract text content for embedding
        chunk_texts = [doc.page_content for doc in chunked_docs]

        # Generate embeddings
        embeddings = self._embed_chunks(chunk_texts)

        # Convert to Document objects
        documents = self._convert_to_documents(
            chunked_docs,
            doc_id,
            account_id,
            user_id,
            is_global,
            session_id,
            embeddings
        )

        return documents