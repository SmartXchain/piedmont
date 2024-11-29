from django.contrib import admin
from .models import PartDetails

# Register your models here.
@admin.register(PartDetails)
class PartDetailsAdmin(admin.ModelAdmin):
    list_display = ('part', 'get_job_identity_display', 'processing_standard')