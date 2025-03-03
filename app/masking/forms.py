from django import forms
from .models import MaskingProcess, MaskingStep


class MaskingProcessForm(forms.ModelForm):
    """Form for creating and editing MaskingProcess instances."""
    class Meta:
        model = MaskingProcess
        fields = ["part_number", "part_number_masking_description"]


class MaskingStepForm(forms.ModelForm):
    """Form for creating and editing MaskingStep instances."""
    class Meta:
        model = MaskingStep
        fields = ["masking_process", "masking_step_number", "masking_repair_title", "masking_description", "image"]
