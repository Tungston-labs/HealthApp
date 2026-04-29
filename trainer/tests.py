from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from .serializers import TrainerSerializer


class TrainerSerializerImageUploadTests(SimpleTestCase):
    def test_profile_pic_accepts_heic_extension(self):
        serializer = TrainerSerializer(
            data={
                "profile_pic": SimpleUploadedFile(
                    "trainer-profile.heic",
                    b"heic-bytes",
                    content_type="image/heic",
                )
            },
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_profile_pic_rejects_unsupported_extension(self):
        serializer = TrainerSerializer(
            data={
                "profile_pic": SimpleUploadedFile(
                    "trainer-profile.pdf",
                    b"pdf-bytes",
                    content_type="application/pdf",
                )
            },
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("profile_pic", serializer.errors)
