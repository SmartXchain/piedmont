from django import forms
from .models import Part, PartDetails, JobDetails


class PartForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = ['part_number', 'part_revision', 'part_description']


class PartDetailsForm(forms.ModelForm):
    class Meta:
        model = PartDetails
        fields = ['job_identity', 'processing_standard', 'classification', 'alloy_with_heat_treat_condition', 'rework']


class JobDetailsForm(forms.ModelForm):
    class Meta:
        model = JobDetails
        fields = [
            'part_detail', 'job_number', 'customer', 'purchase_order_with_revision',
            'part_quantity', 'serial_or_lot_numbers', 'surface_repaired', 'surface_area',
            'date', 'job_identity', 'processing_standard', 'classification', 'current_density',
        ]
