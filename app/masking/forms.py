from django import forms
from masking.models import MaskingProfile
from part.models import PartDetails


class MaskingProfileForm(forms.ModelForm):
    part_detail = forms.ModelChoiceField(
        queryset=PartDetails.objects.select_related('classification', 'processing_standard'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Select Part Details (Part Number, Revision, Classification)"
    )

    class Meta:
        model = MaskingProfile
        fields = ['part_detail', 'surface_repaired']
        widgets = {
            'surface_repaired': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
