from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from unittest.mock import MagicMock, patch

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


class TrainerSerializerCreateTests(SimpleTestCase):
    @patch("trainer.serializers.TrainerCertificate.objects.create")
    @patch("trainer.serializers.Trainer.objects.create")
    def test_create_attaches_certificates_after_trainer_is_created(
        self,
        trainer_create,
        certificate_create,
    ):
        trainer = MagicMock()
        trainer.email = "trainer@example.com"
        trainer.phno = "9876543210"
        trainer.name = "Trainer"
        trainer_create.return_value = trainer
        certificate = MagicMock()
        certificate_create.return_value = certificate

        serializer = TrainerSerializer()
        serializer.create(
            {
                "name": "Trainer",
                "phno": "9876543210",
                "email": "trainer@example.com",
                "dob": "2000-01-01",
                "section_timing": "30",
                "gender": "female",
                "location": "Kerala",
                "expecting_salary": "25000.00",
                "no_of_section": 3,
                "adar_number": "991882111100",
                "adar_image": "https://example.com/adar.jpg",
                "certificates": ["https://example.com/cert.jpg"],
            }
        )

        trainer_create.assert_called_once()
        self.assertNotIn("certificates", trainer_create.call_args.kwargs)
        certificate_create.assert_called_once_with(
            image_url="https://example.com/cert.jpg"
        )
        trainer.certificates.add.assert_called_once_with(certificate)
