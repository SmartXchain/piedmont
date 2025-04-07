# admin/forms.py
from django import forms
from part.models import PartStandard

class PartStandardForm(forms.ModelForm):
    class Meta:
        model = PartStandard
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['classification'].label_from_instance = lambda obj: (
            f"{obj.name} ({obj.standard.name})" if obj.standard else obj.name
        )
