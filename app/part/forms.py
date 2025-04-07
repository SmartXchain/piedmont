# admin/forms.py
from django import forms
from part.models import PartStandard


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
