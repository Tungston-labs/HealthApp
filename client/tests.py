from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from rest_framework import serializers

from health.upload_fields import ImageUploadField


class ImageUploadFieldTests(SimpleTestCase):
    class UploadSerializer(serializers.Serializer):
        image = ImageUploadField()

    def test_accepts_heic_and_webp_extensions(self):
        for filename in ("profile.heic", "banner.webp"):
            serializer = self.UploadSerializer(
                data={
                    "image": SimpleUploadedFile(
                        filename,
                        b"image-bytes",
                        content_type="application/octet-stream",
                    )
                }
            )

            self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rejects_unsupported_extensions(self):
        serializer = self.UploadSerializer(
            data={
                "image": SimpleUploadedFile(
                    "profile.pdf",
                    b"pdf-bytes",
                    content_type="application/pdf",
                )
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("image", serializer.errors)
