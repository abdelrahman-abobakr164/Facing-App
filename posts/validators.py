from django.core.exceptions import ValidationError
from PIL import Image
import os

MB = 1024 * 1024

IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
VIDEO_EXTENSIONS = {"mp4", "webm", "mov"}

MAX_IMAGE_SIZE = 10 * MB
MAX_VIDEO_SIZE = 50 * MB


def _check_file(file, *, allowed, max_size, label):
    extension = os.path.splitext(file.name)[1].lower().lstrip(".")
    if extension not in allowed:
        raise ValidationError(
            f"'{file.name}' is not a supported {label}. "
            f"Allowed types: {', '.join(sorted(allowed))}."
        )
    if file.size > max_size:
        raise ValidationError(
            f"'{file.name}' is too large. "
            f"Maximum {label} size is {max_size // MB} MB."
        )


def validation_image(file):
    _check_file(file, allowed=IMAGE_EXTENSIONS, max_size=MAX_IMAGE_SIZE, label="image")

    try:
        Image.open(file).verify()
    except Exception:
        raise ValidationError(f"'{file.name}' is not a valid image.") from None
    finally:
        file.seek(0)


def validation_video(file):
    _check_file(file, allowed=VIDEO_EXTENSIONS, max_size=MAX_VIDEO_SIZE, label="video")
