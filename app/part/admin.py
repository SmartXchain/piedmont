from django.contrib import admin
from .models import Part, PartDetails, JobDetails

@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ('part_number', 'part_description', 'part_revision')

@admin.register(PartDetails)
class PartDetailsAdmin(admin.ModelAdmin):
    list_display = ('part', 'job_identity', 'processing_standard', 'alloy_with_heat_treat_condition')

@admin.register(JobDetails)
class JobDetailsAdmin(admin.ModelAdmin):
    list_display = ('job_number', 'part_detail', 'part_quantity', 'date')
