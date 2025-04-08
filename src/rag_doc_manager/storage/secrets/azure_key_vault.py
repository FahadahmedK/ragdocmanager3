from typing import Any, Dict, Optional

from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient

from rag_doc_manager.storage.secrets.credentials_handler import AzureCredentialManager
from rag_doc_manager.storage.secrets.base import SecretStore, SecretStoreConnectionError, SecretNotFoundError, AuthenticationError


class AzureKeyVaultStore(SecretStore):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._authenticate()

    def _authenticate(self):
        try:
            if not self.config.get('vault_url'):
                raise ValueError('vault_url is required to initialize AzureKeyVaultStore')

            self.vault_url = self.config.get('vault_url')

            if self.config.get('credential'):
                # use provided credential object directly
                credential = self.config['credential']
            elif all(key in self.config for key in ['client_id', 'tenant_id', 'client_secret']):
                credential = ClientSecretCredential(
                    tenant_id=self.config['tenant_id'],
                    client_id=self.config['client_id'],
                    client_secret=self.config['client_secret']
                )
            else:
                credential_manager = AzureCredentialManager()
                credential = credential_manager.get_credentials()

            self.client = SecretClient(
                vault_url=self.vault_url,
                credential=credential
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Azure Key Vault client: {str(e)}")
            raise SecretStoreConnectionError(f"Failed to initialize Azure Key Vault client: {str(e)}")

    def get_secret(self, key: str) -> str:
        try:
            secret = self.client.get_secret(key)
            return secret.value
        except ResourceNotFoundError:
            raise SecretNotFoundError(f"Secret '{key}' not found")
        except HttpResponseError as e:
            if hasattr(e, 'status_code'):
                if e.status_code == 401 or e.status_code == 403:
                    raise AuthenticationError(f"Authentication failed: {str(e)}")
            raise SecretStoreConnectionError(f"Azure Key Vault error: {str(e)}")

    def set_secret(self, key: str, value: str) -> bool:
        try:
            self.client.set_secret(key, value)
            return True
        except HttpResponseError as e:
            if hasattr(e, 'status_code'):
                if e.status_code == 401 or e.status_code == 403:
                    raise AuthenticationError(f"Authentication failed: {str(e)}")
            raise SecretStoreConnectionError(f"Azure Key Vault error: {str(e)}")

    