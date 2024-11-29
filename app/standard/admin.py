from django.contrib import admin
from .models import Standard, InspectionRequirement, PeriodicTest

class InspectionRequirementInline(admin.TabularInline):
    model = InspectionRequirement
    extra = 1

class PeriodicTestInline(admin.TabularInline):
    model = PeriodicTest
    extra = 1
    
@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    list_display = ('name', 'revision', 'author')
    inlines = [InspectionRequirementInline]
    inlines = [PeriodicTestInline]

