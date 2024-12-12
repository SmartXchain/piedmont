from django import forms
from .models import Method


class MethodForm(forms.ModelForm):
    class Meta:
        model = Method
        fields = [
            'method_type', 'title', 'description', 'tank_name', 'temp_min', 'temp_max',
            'immersion_time_min', 'immersion_time_max', 'chemical', 'is_rectified'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add custom attributes for better styling or identification
        for field_name, field in self.fields.items():
            if field_name in ['tank_name', 'temp_min', 'temp_max', 'immersion_time_min', 'immersion_time_max', 'chemical']:
                field.widget.attrs['class'] = 'form-control'
