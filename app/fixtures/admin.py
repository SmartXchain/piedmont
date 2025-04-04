from django.contrib import admin
from .models import Rack, RackPhoto, PMTask, RackPM, RackPMPlan


class RackPhotoInline(admin.TabularInline):
    model = RackPhoto
    extra = 1
    readonly_fields = ['thumbnail']


@admin.register(Rack)
class RackAdmin(admin.ModelAdmin):
    list_display = ['rack_id', 'location', 'coating_type', 'in_service_date']
    search_fields = ['rack_id', 'location']
    inlines = [RackPhotoInline]


@admin.register(RackPhoto)
class RackPhotoAdmin(admin.ModelAdmin):
    list_display = ['rack', 'thumbnail']
    readonly_fields = ['thumbnail']


@admin.register(PMTask)
class PMTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'frequency_days', 'thumbnail']
    search_fields = ['title']
    readonly_fields = ['thumbnail']


@admin.register(RackPM)
class RackPMAdmin(admin.ModelAdmin):
    list_display = ['rack', 'pm_task', 'performed_by', 'passed', 'date_performed']
    list_filter = ['passed', 'date_performed', 'performed_by']
    search_fields = ['rack__rack_id', 'pm_task__title', 'notes']
    readonly_fields = ['created_by', 'modified_by', 'created_at', 'modified_at']

    def save_model(self, request, obj, form, change):
        """
        Automatically set created_by and modified_by based on request.user.
        """
        if not obj.pk:
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(RackPMPlan)
class RackPMPlanAdmin(admin.ModelAdmin):
    list_display = ['rack', 'task', 'due_every_days']
    list_filter = ['rack', 'task']
    search_fields = ['rack__rack_id', 'task__title']
