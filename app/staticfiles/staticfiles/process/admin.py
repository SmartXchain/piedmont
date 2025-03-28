from django.contrib import admin
from .models import Process, ProcessStep


class ProcessStepInline(admin.TabularInline):  # Inline editing for ProcessSteps within Process
    model = ProcessStep
    extra = 1  # Show one empty row for quick addition
    fields = ('method', 'step_number')
    ordering = ['step_number']


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
