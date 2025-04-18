# admin/forms.py
from django import forms
from part.models import PartStandard, WorkOrder, Part
from standard.models import Standard, Classification


class WorkOrderForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = [
            'work_order_number', 'rework', 'job_identity', 'standard',
            'classification', 'surface_repaired', 'customer',
            'purchase_order_with_revision', 'part_quantity',
            'serial_or_lot_numbers', 'surface_area', 'current_density'
        ]
        widgets = {
            'serial_or_lot_numbers': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        part = kwargs.pop('part', None)
        super().__init__(*args, **kwargs)

        if part:
            # ✅ Use actual model instances
            self.fields['standard'].queryset = Standard.objects.filter(
                id__in=PartStandard.objects.filter(part=part).values_list('standard', flat=True)
            )

            self.fields['classification'].queryset = Classification.objects.filter(
                id__in=PartStandard.objects.filter(part=part).values_list('classification', flat=True)
            )

            part_standards = part.standards.all()
            if part_standards.count() == 1:
                self.fields['standard'].initial = part_standards[0].standard
                self.fields['classification'].initial = part_standards[0].classification


class PartForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = ['part_number', 'part_description', 'part_revision']
        widgets = {
            'part_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Part Number'}),
            'part_description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Description'}),
            'part_revision': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Revision'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        part_number = cleaned_data.get('part_number')
        part_revision = cleaned_data.get('part_revision')

        if part_number and part_revision:
            # Don't raise error here — we want the view to handle redirect
            if Part.objects.filter(part_number=part_number, part_revision=part_revision).exists():
                # Just return cleaned_data without error to avoid form error display
                self._duplicate_exists = True  # Flag for the view
        return cleaned_data


class PartStandardForm(forms.ModelForm):
    class Meta:
        model = PartStandard
        fields = ['standard', 'classification']
        widgets = {
            'standard': forms.Select(attrs={'class': 'form-select'}),
            'classification': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        # Pull the standard from the form data if available
        super().__init__(*args, **kwargs)

        self.fields['classification'].queryset = Classification.objects.none()

        if 'standard' in self.data:
            try:
                standard_id = int(self.data.get('standard'))
                self.fields['classification'].queryset = Classification.objects.filter(standard_id=standard_id)
            except (ValueError, TypeError):
                pass  # Invalid input; fallback to empty queryset

        elif self.instance.pk and self.instance.standard:
            self.fields['classification'].queryset = Classification.objects.filter(standard=self.instance.standard)

        # Optional: pretty labels
        self.fields['classification'].label_from_instance = lambda obj: (
            f"Method: {obj.method or '—'}, Class: {obj.class_name or '—'}, Type: {obj.type or '—'}"
        )
