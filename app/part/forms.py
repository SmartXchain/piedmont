from django import forms
from .models import Part, PartDetails, JobDetails

class PartForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = ['part_number', 'part_description', 'part_revision']
        widgets = {
            'part_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter part number'}),
            'part_description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter part description'}),
            'part_revision': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter part revision'}),
        }

class PartDetailsForm(forms.ModelForm):
    class Meta:
        model = PartDetails
        fields = ['job_identity', 'processing_standard', 'alloy_with_heat_treat_condition']
        widgets = {
            'job_identity': forms.Select(attrs={'class': 'form-control'}),
            'processing_standard': forms.Select(attrs={'class': 'form-control'}),
            'alloy_with_heat_treat_condition': forms.TextInput(attrs={'class': 'form-control'}),
        }

class JobDetailsForm(forms.ModelForm):
    class Meta:
        model = JobDetails
        fields = ['part', 'purchase_order_with_revision', 'part_quantity', 'serial_or_lot_numbers', 'job_number', 'surface_repaired', 'date']
        widgets = {
            'part': forms.Select(attrs={'class': 'form-control'}),
            'purchase_order_with_revision': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter PO with revision'}),
            'part_quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter part quantity'}),
            'serial_or_lot_numbers': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter serial or lot numbers'}),
            'job_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter job number'}),
            'surface_repaired': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Surface Repaired'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
