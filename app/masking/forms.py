from django import forms
from .models import MaskingProfile, MaskingPhoto


class MaskingProfileForm(forms.ModelForm):
    class Meta:
        model = MaskingProfile
        fields = ['part']


class MaskingPhotoForm(forms.ModelForm):
    class Meta:
        model = MaskingPhoto
        fields = ['masking_profile', 'photo_type', 'image', 'description']
