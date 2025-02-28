from django.db import models
from part.models import PartDetails, Part
from django.db.models import F
from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe


class MaskingProfile(models.Model):
    part_detail = models.ForeignKey(
        'part.PartDetails',  # Reference to the PartDetails model
        on_delete=models.CASCADE,
        related_name='masking_profiles'
    )
    surface_repaired = models.TextField(blank=True, null=True, verbose_name="Surface Repaired")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Masking Profile for {self.part_detail.part.part_number} (Revision {self.part_detail.part.part_revision})"


def masking_profile_list(request):
    profiles = (
        MaskingProfile.objects
        .select_related('part_detail__part')  # Ensure related Part and PartDetail data is fetched
        .values(
            part_number=F('part_detail__part__part_number'),
            part_revision=F('part_detail__part__part_revision'),
            part_description=F('part_detail__part__part_description'),
        )
        .distinct()
    )
    return render(request, 'masking/masking_profile_list.html', {'profiles': profiles})
