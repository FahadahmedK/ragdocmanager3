from enum import Enum
from .adaptors import AISearchQueryEngine


class Providers(Enum):

    AZURE = 'azure'
    DEFAULT = 'ai_attack'



class QueryEngineFactory:

    _PROVIDERS = {
        'azure': AISearchQueryEngine,
        'ai_attack': None
    }

    @classmethod
    def get_query_engine(cls, provider: str, **kwargs):
        provider_class = cls._PROVIDERS.get(str(provider).lower())
        if not provider_class:
            raise ValueError(f"Provider '{provider}' not supported or not implemented")
        return provider_class(**kwargs)