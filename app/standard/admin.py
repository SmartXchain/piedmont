from django.contrib import admin
from .models import Standard, InspectionRequirement

class InspectionRequirementInline(admin.TabularInline):
    model = InspectionRequirement
    extra = 1

@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    list_display = ('name', 'revision', 'author')
    inlines = [InspectionRequirementInline]