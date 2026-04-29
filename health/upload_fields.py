import os

from rest_framework import serializers
from rest_framework.exceptions import ValidationError


ALLOWED_IMAGE_EXTENSIONS = ("jpg", "jpeg", "png", "gif", "webp", "heic", "heif")


def validate_image_extension(file_obj):
    filename = getattr(file_obj, "name", "") or ""
    extension = os.path.splitext(filename)[1].lower().lstrip(".")

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        allowed = ", ".join(ALLOWED_IMAGE_EXTENSIONS)
        raise ValidationError(f"Unsupported image file extension. Allowed extensions: {allowed}.")


class ImageUploadField(serializers.FileField):
    """
    Stores image uploads by extension without forcing Pillow to decode formats
    such as HEIC.
    """

    def to_internal_value(self, data):
        file_obj = super().to_internal_value(data)
        validate_image_extension(file_obj)
        return file_obj

    def to_representation(self, value):
        if not value:
            return None

        try:
            url = value.url
        except ValueError:
            return None

        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(url)
        return url
