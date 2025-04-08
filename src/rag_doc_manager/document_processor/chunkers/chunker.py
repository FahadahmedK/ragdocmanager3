from .factory import get_splitter


class Chunker:
    
    @classmethod
    def chunk(
        document
        file_type: str
        chunking_strategy: str="base"
    ):
        splitter = get_splitter(
            file_type=file_type
        )
        
        chunks = splitter.split_text(document)
        
        return chunks