# process/admin.py
from django.contrib import admin
from .models import Process, ProcessStep
from .forms import ProcessForm, ProcessStepInlineForm
from methods.models import Method
from django.utils.html import format_html


class ProcessStepInline(admin.StackedInline):  # Change to Stacked for more fields
    model = ProcessStep
    form = ProcessStepInlineForm
    extra = 1
    ordering = ('step_number',)
    show_change_link = True
    autocomplete_fields = ['method']
    readonly_fields = ['method_preview']

    def method_preview(self, obj):
        if obj.method:
            return format_html(
                "<strong>{}</strong><br>{}<br><em>{}</em>",
                obj.method.title,
                obj.method.description[:100] + ("..." if len(obj.method.description) > 100 else ""),
                obj.method.method_type,
            )
        return "—"
    method_preview.short_description = "Method Overview"


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    form = ProcessForm
    list_display = ('standard', 'classification', 'created_at')
    list_filter = ('standard', 'classification')
    search_fields = ('standard__name',)
    inlines = [ProcessStepInline]

    def step_count(self, obj):
        return obj.steps.count()

    def has_unassigned_methods(self, obj):
        unassigned = obj.steps.filter(method__isnull=True).exists()
        return "⚠️ Yes" if unassigned else "✅ All Assigned"
    has_unassigned_methods.short_description = "Unassigned Methods"

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing
            return ['classification']
        return []
