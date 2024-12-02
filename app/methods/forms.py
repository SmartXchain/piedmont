from django import forms
from .models import Method

class MethodForm(forms.ModelForm):
    class Meta:
        model = Method
        fields = ['title', 'description', 'method_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'method_type': forms.Select(attrs={'class': 'form-control'}),
        }
