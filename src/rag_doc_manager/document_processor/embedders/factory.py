from typing import Dict, Type, List
from .base import Embedder, AzureOpenAIEmbedder, HuggingFaceEmbedder, OpenAIEmbedder

class EmbedderFactory:
    """
    Factory class for creating different types of embedders.

    This factory simplifies the instantiation of different embedding providers.
    """

    # Registry to store embedder classes
    _embedders: Dict[str, Type[Embedder]] = {
        "azure": AzureOpenAIEmbedder,
        "openai": OpenAIEmbedder,
        "huggingface": HuggingFaceEmbedder
    }

    @classmethod
    def register_embedder(cls, name: str, embedder_class: Type[Embedder]) -> None:
        """
        Register a new embedder type with the factory.

        Parameters
        ----------
        name : str
            The name to register the embedder under.
        embedder_class : Type[Embedder]
            The embedder class to register.
        """
        cls._embedders[name] = embedder_class

    @classmethod
    def create_embedder(cls, embedder_type: str, **kwargs) -> Embedder:
        """
        Create an embedder instance of the specified type.

        Parameters
        ----------
        embedder_type : str
            The type of embedder to create, must be one of the registered types.
        **kwargs
            Additional arguments to pass to the embedder constructor.

        Returns
        -------
        Embedder
            An instance of the requested embedder.

        Raises
        ------
        ValueError
            If the requested embedder type is not registered.
        """
        embedder_class = cls._embedders.get(embedder_type.lower())
        if embedder_class is None:
            available_types = ", ".join(cls._embedders.keys())
            raise ValueError(f"Unsupported embedder type: {embedder_type}. Available types: {available_types}")

        return embedder_class(**kwargs)

    @classmethod
    def list_embedders(cls) -> List[str]:
        """
        Get a list of all registered embedder types.

        Returns
        -------
        List[str]
            A list of registered embedder type names.
        """
        return list(cls._embedders.keys())