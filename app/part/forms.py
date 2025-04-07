# admin/forms.py
from django import forms
from part.models import PartStandard, WorkOrder


class PartStandardForm(forms.ModelForm):
    class Meta:
        model = PartStandard
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Custom label for classifications showing method/class/type and standard name
        self.fields['classification'].label_from_instance = lambda obj: (
            f"Method: {obj.method or '—'}, Class: {obj.class_name or '—'}, Type: {obj.type or '—'}" + (f" ({obj.standard.name})" if obj.standard else "")
        )

class WorkOrderForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = [
            'work_order_number', 'rework', 'job_identity', 'standard',
            'classification', 'surface_repaired', 'customer',
            'purchase_order_with_revision', 'part_quantity',
            'serial_or_lot_numbers', 'surface_area',
            'current_density'
        ]
        widgets = {
            'serial_or_lot_numbers': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        part = kwargs.pop('part', None)
        super().__init__(*args, **kwargs)
        if part:
            self.fields['standard'].queryset = part.standards.values_list('standard', flat=True)
            self.fields['classification'].queryset = part.standards.values_list('classification', flat=True)