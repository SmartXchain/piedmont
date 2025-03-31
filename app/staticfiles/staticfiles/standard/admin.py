from django.contrib import admin
from .models import Standard, StandardRevisionNotification, InspectionRequirement, PeriodicTest, Classification


@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    list_display = ('name', 'revision', 'author', 'requires_process_review', 'created_at', 'updated_at')
    search_fields = ('name', 'revision', 'author')
    list_filter = ('requires_process_review', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-updated_at',)


@admin.register(StandardRevisionNotification)
class StandardRevisionNotificationAdmin(admin.ModelAdmin):
    list_display = ('standard', 'message', 'notified_at', 'is_acknowledged')
    search_fields = ('standard__name', 'message')
    list_filter = ('is_acknowledged', 'notified_at')


@admin.register(InspectionRequirement)
class InspectionRequirementAdmin(admin.ModelAdmin):
    list_display = ('standard', 'name', 'description')
    search_fields = ('standard__name', 'name')
    list_filter = ('standard',)


@admin.register(PeriodicTest)
class PeriodicTestAdmin(admin.ModelAdmin):
    list_display = ('standard', 'name', 'time_period', 'number_of_specimens', 'material', 'dimensions')
    search_fields = ('standard__name', 'name', 'time_period')
    list_filter = ('time_period', 'standard')


@admin.register(Classification)
class ClassificationAdmin(admin.ModelAdmin):
    list_display = ('standard', 'method', 'class_name', 'type')
    search_fields = ('standard__name', 'method', 'class_name', 'type')
    list_filter = ('standard',)


# Optional: Registering all models at once
# admin.site.register([Standard, StandardRevisionNotification, InspectionRequirement, PeriodicTest, Classification])
