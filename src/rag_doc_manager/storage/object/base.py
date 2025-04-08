
from abc import ABC, abstractmethod
from typing import Union, Dict
from pathlib import Path

class ObjectStorage(ABC):
    
    """
    Abstract base class for object storage operations.
    This defines the interface for storing and retrieving raw documents.
    """
    
    
    @abstractmethod
    def upload_file(self, file_path: Union[str, Path], destination_prefix: str, additional_metadata: Dict[str, str]) -> str:
        """
        Upload a file to object storage.
        
        Parameters
        ----------
        file_path : Union[str, Path]
            Path to the file to upload
        destination_prefix : str
            Prefix (folder/path) within the storage where the file should be stored
        additional_metadata: Dict[str, str]
        Returns
        -------
        str
            URL or identifier for the uploaded file
        """
        pass

    
    # @abstractmethod
    # def download_file(self, file_url: str, destination_path: str, **kwargs) -> str:
    #
    #     """
    #     Download a file from object storage.
    #
    #     Parameters
    #     ----------
    #     file_url : str
    #         URL or identifier of the file to download
    #     destination_path : Union[str, Path]
    #         Local path where the file should be saved
    #
    #     Returns
    #     -------
    #     str
    #         Path to the downloaded file
    #     """
        
    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        
        """
        Delete a file from object storage.
        
        Parameters
        ----------
        file_url : str
            URL or identifier of the file to delete (could also be just the name if Shared Access Storage is used)
            
        Returns
        -------
        bool
            True if the file was deleted successfully, False otherwise
        """