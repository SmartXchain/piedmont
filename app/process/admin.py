from django.contrib import admin
from .models import Process, ProcessStep
from django import forms


class ProcessStepInline(admin.TabularInline):
    model = ProcessStep
    extra = 1
    fields = ('method', 'step_number')
    ordering = ['step_number']

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == "method":
            kwargs["queryset"] = Method.objects.all()
            return forms.ModelChoiceField(
                queryset=kwargs["queryset"],
                label="Method",
                widget=forms.Select,
                to_field_name="id",
                empty_label="Select a method",
                help_text="Select a method to use for this step.",
                # Format: "Title - First 100 chars of description"
                label_from_instance=lambda obj: f"{obj.title} - {obj.description[:100]}{'...' if len(obj.description) > 100 else ''}"
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


@admin.register(ProcessStep)
class ProcessStepAdmin(admin.ModelAdmin):
    list_display = ('process', 'method', 'step_number')
    list_filter = ('process__standard', 'method')
    search_fields = ('process__standard__name', 'method__title')
    ordering = ['process', 'step_number']
