from django.contrib import admin
from .models import Method


@admin.register(Method)
class MethodAdmin(admin.ModelAdmin):
    list_display = ('title', 'method_type', 'description')

    def get_fields(self, request, obj=None):
        fields = ['method_type', 'title', 'description']
        if obj and obj.method_type == 'processing_tank':
            fields += ['tank_name', 'temp_min', 'temp_max', 'immersion_time_min', 'immersion_time_max', 'chemical', 'is_rectified']
        return fields
