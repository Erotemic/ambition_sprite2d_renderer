"""Read generated images within the renderer's texture budget."""
from PIL import Image

MAX_TEXTURE_SIDE = 16384


def configure_generated_image_reads() -> None:
    """Generated pages can fill one maximum-size texture."""
    Image.MAX_IMAGE_PIXELS = MAX_TEXTURE_SIDE * MAX_TEXTURE_SIDE
