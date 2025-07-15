from PIL import Image, UnidentifiedImageError
import logging

logger = logging.getLogger(__name__)

def load_image(path: str) -> Image.Image:
    """
    Loads an image and converts it to RGB format.

    Args:
        path (str): Path to the image file.

    Returns:
        Image.Image: Loaded and converted image.

    Raises:
        FileNotFoundError: If the file does not exist.
        UnidentifiedImageError: If the image cannot be opened.
    """
    try:
        image = Image.open(path).convert("RGB")
        logger.debug(f"Loaded image from: {path}")
        return image
    except FileNotFoundError:
        logger.error(f"Image file not found: {path}")
        raise
    except UnidentifiedImageError:
        logger.error(f"Unable to identify image file: {path}")
        raise
