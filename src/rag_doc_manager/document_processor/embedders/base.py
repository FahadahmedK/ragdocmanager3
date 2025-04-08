from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Dict, List, Type, Union
from openai import AzureOpenAI
from azure.identity import get_bearer_token_provider
from rag_doc_manager.storage.secrets.credentials_handler import AzureCredentialManager


class Embedder(ABC):
    """
    Abstract base class for text embedding models.
    
    This class defines the interface for all embedding implementations.
    """
    
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embeddings for a single text.
        
        Parameters
        ----------
        text : str
            The input text to embed.
            
        Returns
        -------
        List[float]
            The embedding vector as a list of floats.
        """
        pass
    
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Parameters
        ----------
        texts : List[str]
            A list of input texts to embed.
            
        Returns
        -------
        List[List[float]]
            A list of embedding vectors, each as a list of floats.
        """
        pass


class AzureOpenAIEmbedder(Embedder):
    """
    Embedder implementation using Azure OpenAI API.
    
    Parameters
    ----------
    api_key : str
        The Azure OpenAI API key.
    endpoint : str
        The Azure OpenAI endpoint URL.
    deployment_name : str
        The deployment name for the embedding model.
    """
    
    def __init__(self,  endpoint: str, deployment_name: str):
        try:
            from openai import AzureOpenAI
            credential_manager = AzureCredentialManager()
            credentials = credential_manager.get_credentials()
            token_provider = get_bearer_token_provider(credentials, "https://cognitiveservices.azure.com/.default")


            self.client = AzureOpenAI(
                azure_ad_token_provider=token_provider,
                azure_endpoint=endpoint,
                api_version = "2023-07-01-preview"
            )
            self.deployment_name = deployment_name
        except ImportError:
            raise ImportError("Please install the openai package: pip install openai")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text using Azure OpenAI.
        
        Parameters
        ----------
        text : str
            The input text to embed.
            
        Returns
        -------
        List[float]
            The embedding vector as a list of floats.
        """
        response = self.client.embeddings.create(
            input=[text],
            model=self.deployment_name
        )
        return response.data[0].embedding
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts using Azure OpenAI.
        
        Parameters
        ----------
        texts : List[str]
            A list of input texts to embed.
            
        Returns
        -------
        List[List[float]]
            A list of embedding vectors, each as a list of floats.
        """
        response = self.client.embeddings.create(
            input=texts,
            model=self.deployment_name
        )
        return [item.embedding for item in response.data]


class OpenAIEmbedder(Embedder):
    """
    Embedder implementation using OpenAI API.
    
    Parameters
    ----------
    api_key : str
        The OpenAI API key.
    model_name : str, optional
        The model name to use for embeddings, by default "text-embedding-3-small".
    """
    
    def __init__(self, api_key: str, model_name: str = "text-embedding-3-small"):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model_name = model_name
        except ImportError:
            raise ImportError("Please install the openai package: pip install openai")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text using OpenAI.
        
        Parameters
        ----------
        text : str
            The input text to embed.
            
        Returns
        -------
        List[float]
            The embedding vector as a list of floats.
        """
        response = self.client.embeddings.create(
            input=[text],
            model=self.model_name
        )
        return response.data[0].embedding
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts using OpenAI.
        
        Parameters
        ----------
        texts : List[str]
            A list of input texts to embed.
            
        Returns
        -------
        List[List[float]]
            A list of embedding vectors, each as a list of floats.
        """
        response = self.client.embeddings.create(
            input=texts,
            model=self.model_name
        )
        return [item.embedding for item in response.data]


class HuggingFaceEmbedder(Embedder):
    """
    Embedder implementation using Hugging Face transformers.
    
    Parameters
    ----------
    model_name : str, optional
        The model name to use for embeddings, by default "sentence-transformers/all-MiniLM-L6-v2".
    device : str, optional
        The device to run the model on, by default "cpu".
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "cpu"):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name, device=device)
        except ImportError:
            raise ImportError("Please install the sentence-transformers package: pip install sentence-transformers")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text using Hugging Face.
        
        Parameters
        ----------
        text : str
            The input text to embed.
            
        Returns
        -------
        List[float]
            The embedding vector as a list of floats.
        """
        embedding = self.model.encode(text)
        return embedding.tolist()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts using Hugging Face.
        
        Parameters
        ----------
        texts : List[str]
            A list of input texts to embed.
            
        Returns
        -------
        List[List[float]]
            A list of embedding vectors, each as a list of floats.
        """
        embeddings = self.model.encode(texts)
        return embeddings.tolist()


