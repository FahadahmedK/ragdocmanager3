import magic
import logging
from typing import Any
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


def save_bytes_as_file(file_content: bytes, parent_dir: Path, file_name: str) -> dict[str, Any]:
    def detect_file_from_bytes(content: bytes) -> tuple[str, str]:
        mime_type = 'application/octet-stream'
        extension = '.bin'
        try:
            mime_type = magic.Magic(mime=True).from_buffer(content)
            mime_to_ext = {
                'application/pdf': '.pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
                'application/msword': '.doc',
                'text/plain': '.txt',
                'text/csv': '.csv',
                'text/markdown': '.md',
                'application/json': '.json',
            }
            extension = mime_to_ext.get(mime_type, '.bin')
        except Exception as e:
            logger.error(f"Error detecting MIME type {e}. Using Fallback.")

        # Basic signature detection as fallback
        if content.startswith(b'%PDF'):
            return 'application/pdf', '.pdf'
        elif content.startswith(b'PK\x03\x04'):
            # Office Open XML files are ZIP-based
            if b'word/' in content[:4000]:
                return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.docx'
            elif b'xl/' in content[:4000]:
                return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx'
            return 'application/zip', '.zip'
        elif content.startswith(b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'):
            return 'application/msword', '.doc'
        return mime_type, extension

    mime_type, extension = detect_file_from_bytes(content=file_content)

    # TODO: get file name from metadata in the request
    filename = file_name #f"{uuid.uuid4()}{extension}"
    file_path = parent_dir / filename

    # Ensure parent directory exists
    parent_dir.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'wb') as file:
        file.write(file_content)

    return {
        'file_path': str(file_path),  # Convert Path to string for serialization
        'filename': filename,
        'size': len(file_content),
        'mime_type': mime_type,
        'extension': extension
    }