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
    part_detail = forms.ModelChoiceField(
        queryset=PartDetails.objects.none(),  # Dynamically populated in the view
        label="Part Details",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = JobDetails
        fields = [
            'part_detail', 'job_number', 'job_identity', 'surface_repaired', 
            'surface_area', 'date', 'processing_standard', 'classification'
        ]
        widgets = {
            'job_number': forms.TextInput(attrs={'class': 'form-control'}),
            'job_identity': forms.Select(attrs={'class': 'form-select'}),
            'surface_repaired': forms.TextInput(attrs={'class': 'form-control'}),
            'surface_area': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'processing_standard': forms.Select(attrs={'class': 'form-select'}),
            'classification': forms.Select(attrs={'class': 'form-select'}),
        }