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
    readonly_fields = []

    class Media:
        js = [
            'admin/js/jquery.init.js',
        ]


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    form = ProcessForm
    list_display = ('standard', 'classification', 'created_at')
    list_filter = ('standard',)
    search_fields = ('standard__name',)
    inlines = [ProcessStepInline]
