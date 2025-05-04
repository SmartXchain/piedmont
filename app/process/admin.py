# process/admin.py
from django.contrib import admin
from .models import Process, ProcessStep
from .forms import ProcessForm, ProcessStepInlineForm
from django.utils.html import format_html


class ProcessStepInline(admin.TabularInline):
    model = ProcessStep
    form = ProcessStepInlineForm
    extra = 1
    ordering = ('step_number',)
    autocomplete_fields = ['method']
    readonly_fields = ['method_preview']

    class Media:
        js = [
            'admin/js/jquery.init.js',
            'process/js/method_overview.js',
        ]

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
    list_filter = ('standard',)
    search_fields = ('standard__name',)