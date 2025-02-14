from django.contrib import admin
from .models import ProcessStep, Process


@admin.register(ProcessStep)
class ProcessStepAdmin(admin.ModelAdmin):
    list_display = ('process', 'method', 'step_number')


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = ('standard', 'classification', 'description')
