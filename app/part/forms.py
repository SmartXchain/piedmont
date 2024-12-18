from django import forms
from .models import Part, PartDetails, JobDetails


class PartForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = ['part_number', 'part_revision', 'part_description']

    def clean(self):
        cleaned_data = super().clean()
        part_number = cleaned_data.get('part_number')
        part_revision = cleaned_data.get('part_revision')

        # Exclude the current instance from the uniqueness check
        query = Part.objects.filter(part_number=part_number, part_revision=part_revision)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise forms.ValidationError(
                f"A part with number {part_number} and revision {part_revision} already exists."
            )
        return cleaned_data


class PartDetailsForm(forms.ModelForm):
    class Meta:
        model = PartDetails
        fields = ['job_identity', 'processing_standard', 'classification', 'alloy_with_heat_treat_condition', 'rework']
        widgets = {
            'job_identity': forms.Select(attrs={'class': 'form-control'}),
            'processing_standard': forms.Select(attrs={'class': 'form-control'}),
            'classification': forms.Select(attrs={'class': 'form-control'}),
            'alloy_with_heat_treat_condition': forms.TextInput(attrs={'class': 'form-control'}),
            'rework': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



class JobDetailsForm(forms.ModelForm):
    class Meta:
        model = JobDetails
        fields = [
            'part_detail', 'job_number', 'customer', 'purchase_order_with_revision',
            'part_quantity', 'serial_or_lot_numbers', 'surface_repaired', 'surface_area',
            'date', 'job_identity', 'processing_standard', 'classification'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['part_detail'].widget.attrs.update({'class': 'form-select'})
        self.fields['job_identity'].widget.attrs.update({'class': 'form-select'})
        self.fields['processing_standard'].widget.attrs.update({'class': 'form-select'})
        self.fields['classification'].widget.attrs.update({'class': 'form-select'})
        self.fields['surface_area'].widget.attrs.update({'class': 'form-control'})

