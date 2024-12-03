from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from part.models import Part  # Assuming Part model exists in the `part` app

class MaskingProfile(models.Model):
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='masking_profiles')
    part_revision = models.CharField(max_length=50)
    masking_area = models.TextField()
    MASKING_FAMILY_CHOICES = [
        ('tape', 'Tape'),
        ('wax', 'Wax'),
        ('lacquer', 'Lacquer'),
        # Add other masking families here
    ]
    masking_family = models.CharField(
        max_length=50, choices=MASKING_FAMILY_CHOICES, verbose_name=_("Masking Family")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Masking Profile for {self.part.part_number} - Revision {self.part_revision}"

class MaskingPhoto(models.Model):
    masking_profile = models.ForeignKey(MaskingProfile, on_delete=models.CASCADE, related_name='photos')
    photo_type = models.CharField(
        max_length=10,
        choices=[
            ('front', 'Front'),
            ('top', 'Top'),
            ('right', 'Right'),
            ('closeup', 'Close-Up'),
        ],
    )
    image = models.ImageField(upload_to='masking_photos/')
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.photo_type} photo for {self.masking_profile}"
