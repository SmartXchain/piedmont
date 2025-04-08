from django.contrib import admin
from .models import Process, ProcessStep
from standard.models import Classification

class ProcessStepInline(admin.TabularInline):
    model = ProcessStep
    extra = 1
    ordering = ('step_number',)

@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    form = ProcessForm
    list_display = ('standard', 'classification', 'created_at')
    list_filter = ('standard', 'classification')
    search_fields = ('standard__name',)
    inlines = [ProcessStepInline]

@admin.register(ProcessStep)
class ProcessStepAdmin(admin.ModelAdmin):
    list_display = ('process', 'step_number', 'method')
    list_filter = ('process',)
    search_fields = ('process__standard__name', 'method__title')
