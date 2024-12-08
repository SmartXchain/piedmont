from django import forms
from .models import MaskingProfile, MaskingPhoto
from part.models import Part

class MaskingProfileForm(forms.ModelForm):
    class Meta:
        model = MaskingProfile
        fields = ['part']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['part'].label_from_instance = lambda obj: f"{obj.part_number} - Rev {obj.part_revision} ({obj.part_description})"

    def clean(self):
        cleaned_data = super().clean()
        part = cleaned_data.get('part')

        # Check for duplicates
        if part and MaskingProfile.objects.filter(part=part).exists():
            self.add_error('part', f"A masking profile for part {part.part_number} with revision {part.part_revision} already exists.")
        
        return cleaned_data


class MaskingPhotoForm(forms.ModelForm):
    class Meta:
        model = MaskingPhoto
        fields = ['masking_profile', 'photo_type', 'image', 'description']
