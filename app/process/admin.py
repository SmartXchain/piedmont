from django.contrib import admin
from .models import Process, ProcessStep
from django import forms
from methods.models import Method


class MethodChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.title} - {obj.description[:100]}{'...' if len(obj.description) > 100 else ''}"


class ProcessStepInline(admin.TabularInline):
    model = ProcessStep
    extra = 1
    fields = ('method', 'step_number')
    ordering = ['step_number']

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == "method":
            return MethodChoiceField(
                queryset=Method.objects.all(),
                widget=forms.Select,
                empty_label="Select a method",
                help_text="Select a method to use for this step.",
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = ('standard', 'classification', 'created_at', 'updated_at')
    list_filter = ('standard', 'classification')
    search_fields = ('standard__name', 'classification__name', 'description')
    inlines = [ProcessStepInline]  # Allow adding steps directly inside Process

    def get_readonly_fields(self, request, obj=None):
        """ Make certain fields read-only after creation to avoid classification conflicts. """
        if obj:
            return ['standard', 'classification']
        return []
