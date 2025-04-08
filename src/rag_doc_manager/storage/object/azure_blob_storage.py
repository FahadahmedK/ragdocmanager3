from typing import Optional, Union, Dict
import logging
from pathlib import Path
import datetime
from azure.storage.blob import BlobServiceClient
from azure.storage.blob import ContentSettings
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError


from .base import ObjectStorage

logger = logging.getLogger(__name__)

class AzureBlobStorage(ObjectStorage):
    """
    Azure Blob Storage implementation of the ObjectStorage interface.
    Handles storing and retrieving documents from Azure Blob Storage.
    """

    def __init__(
        self,
        connection_string: str,
        container_name: str,
        account_name: Optional[str] = None,
        account_key: Optional[str] = None,
        create_container_if_not_exists: bool = True
    ):
        """
        Initialize the Azure Blob Storage client.

        Parameters
        ----------
        connection_string : str
            Azure Blob Storage connection string
        container_name : str
            Name of the container to use
        account_name : Optional[str], optional
            Azure Storage account name, by default None
            (Required for SAS token generation if not in connection string)
        account_key : Optional[str], optional
            Azure Storage account key, by default None
            (Required for SAS token generation if not in connection string)
        create_container_if_not_exists : bool, optional
            Whether to create the container if it doesn't exist, by default True
        """

        self.connection_string = connection_string
        self.container_name = container_name
        self.account_name = account_name
        self.account_key = account_key
        self.create_container_if_not_exists = create_container_if_not_exists

        if not self.account_name or not self.account_key:
            parts = self.connection_string.split(';')
            for part in parts:
                if part.startswith('AccountName='):
                    self.account_name = part.split('=', 1)[1]

                elif part.startswith('AccountKey='):
                    self.account_key = part.split('=', 1)[1]


    def _get_blob_service_client(self) -> BlobServiceClient:
        """
        Get the Azure Blob Service client.

        Returns
        -------
        BlobServiceClient
            Azure Blob Service client
        """
        return BlobServiceClient.from_connection_string(self.connection_string)

    def _ensure_container_exists(self) -> None:
        """
        Ensure the container exists, creating it if necessary.
        """

        if self.create_container_if_not_exists:

            with self._get_blob_service_client() as blob_service_client:
                try:

                    container_client = blob_service_client.get_container_client(self.container_name)
                    container_client.create_container()
                    logger.info(f"Container {self.container_name} created")

                except ResourceExistsError:
                    logger.info(f"Container {self.container_name} already exists")


    def upload_file(self, file_path: Union[str, Path], destination_prefix: str, additional_metadata: Dict[str, str]) -> str:
        """
        Upload a file to Azure Blob Storage.

        Parameters
        ----------
        file_path : Union[str, Path]
            Path to the file to upload
        destination_prefix : str
            Prefix (folder/path) within the container where the file should be stored
        additional_metadata: Dict[str, str]
        Returns
        -------
        str
            URL for the uploaded file
        """

        file_path = Path(file_path)

        self._ensure_container_exists()

        blob_name = f"{destination_prefix.rstrip('/')}/{file_path.name}"

        # Determine content type based on file extension
        content_type = self._get_content_type(file_path)


        with self._get_blob_service_client() as blob_service_client:
            blob_client = blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            content_settings = ContentSettings(content_type=content_type)

            metadata = {
                'original_filename': file_path.name,
                'upload_timestamp': datetime.datetime.now(datetime.UTC).isoformat()
            }

            metadata.update(additional_metadata)

            try:
                with open(file_path, 'rb') as data:
                    blob_client.upload_blob(
                        data,
                        overwrite=True,
                        content_settings=content_settings,
                        metadata=metadata
                    )
                    logger.info(f"Uploaded {file_path} to {blob_name}")
                return blob_client.url

            except Exception as e:
                logger.error(f"Error uploading {file_path}: {e}")
                raise

    def delete_file(self, file_url: str) -> bool:
        """
        Delete a file from Azure Blob Storage.

        Parameters
        ----------
        file_url : str
            URL of the file to delete

        Returns
        -------
        bool
            True if deletion was successful, False otherwise
        """
        # Extract blob name from URL
        blob_name = self._extract_blob_name_from_url(file_url)

        # Delete the blob
        with self._get_blob_service_client() as blob_service_client:
            blob_client = blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            try:
                blob_client.delete_blob()
                logger.info(f"Deleted {blob_name}")
                return True

            except ResourceNotFoundError:
                logger.warning(f"Blob {blob_name} not found, nothing to delete")
                return False
            except Exception as e:
                logger.error(f"Error deleting {blob_name}: {e}")
                return False

    def _extract_blob_name_from_url(self, file_url: str) -> str:
        """
        Extract blob name from a URL.

        Parameters
        ----------
        file_url : str
            URL of the file

        Returns
        -------
        str
            Blob name
        """
        # Handle URLs with SAS tokens
        if "?" in file_url:
            file_url = file_url.split("?")[0]

        # Extract blob name
        parts = file_url.split("/")
        container_index = parts.index(self.container_name) if self.container_name in parts else -1

        if 0 <= container_index < len(parts) - 1:
            return "/".join(parts[container_index + 1:])
        else:
            # If the container name is not in the URL, assume the last part is the blob name
            return parts[-1]

    def _get_content_type(self, file_path: Path) -> str:
        """
        Get the content type based on file extension.

        Parameters
        ----------
        file_path : Path
            Path to the file

        Returns
        -------
        str
            Content type
        """
        # Simple mapping of common file extensions to content types
        content_type_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".json": "application/json",
            ".html": "text/html",
            ".htm": "text/html",
            ".xml": "application/xml",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".zip": "application/zip",
            ".md": "text/markdown",
        }

        return content_type_map.get(file_path.suffix.lower(), "application/octet-stream")