import os
import logging

logger = logging.getLogger(__name__)

def ensure_dir(path: str) -> None:
    """
    Ensure the directory exists. If not, create it.
    
    Args:
        path (str): Path to the directory.
    """
    try:
        os.makedirs(path, exist_ok=True)
        logger.debug(f"Directory ensured at: {path}")
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        raise

def get_file_extension(filename: str) -> str:
    """
    Extract the file extension from a filename.

    Args:
        filename (str): File name or path.
    
    Returns:
        str: Lowercase file extension.
    """
    return os.path.splitext(filename)[1].lower()
