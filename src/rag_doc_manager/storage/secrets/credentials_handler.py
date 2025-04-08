from azure.identity import DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential

class AzureCredentialManager:
    _instance = None

    def __new__(cls, use_managed_identity=False, use_environment=False):
        """
        Singleton pattern: ensures only one instance of the credential manager.
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_credentials(use_managed_identity, use_environment)
        return cls._instance

    def _initialize_credentials(self, use_managed_identity, use_environment):
        """
        Initializes the appropriate credentials based on the flags
        provided during instantiation.
        """
        if use_managed_identity:
            # Use Managed Identity credentials (for Azure VM, App Service, etc.)
            self.credentials = ManagedIdentityCredential()
        elif use_environment:
            # Use EnvironmentCredential (typically from AZURE_CLIENT_ID, AZURE_TENANT_ID, and AZURE_CLIENT_SECRET)
            self.credentials = EnvironmentCredential()
        else:
            # Default credential flow that checks multiple sources
            self.credentials = DefaultAzureCredential()

    def get_credentials(self):
        """
        Returns the credentials object to be used for authentication.
        """
        if self.credentials is None:
            raise ValueError("Credentials not initialized.")
        return self.credentials
