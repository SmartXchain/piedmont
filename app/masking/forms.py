from django import forms
from .models import MaskingProcess, MaskingStep


class MaskingProcessForm(forms.ModelForm):
    """Form for creating and editing Masking Processes."""

    class Meta:
        model = MaskingProcess
        fields = ["part_number", "masking_description"]
        widgets = {
            "part_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Part Number"}),
            "masking_description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Enter Masking Description"}),
        }


class MaskingStepForm(forms.ModelForm):
    """Form for creating and editing Masking Steps."""

    class Meta:
        model = MaskingStep
        fields = ["title", "description", "image"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter Step Title"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Enter Step Description"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
