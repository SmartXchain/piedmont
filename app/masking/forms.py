from django import forms
from .models import MaskingProfile, MaskingPhoto


class MaskingProfileForm(forms.ModelForm):
    class Meta:
        model = MaskingProfile
        fields = ['part', 'part_revision', 'masking_area', 'masking_family', 'job_identity', 'surface_repaired']
        widgets = {
            'masking_area': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'surface_repaired': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }



class MaskingPhotoForm(forms.ModelForm):
    class Meta:
        model = MaskingPhoto
        fields = ['masking_profile', 'photo_type', 'image', 'description']
