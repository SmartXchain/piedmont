# admin.py
from django.contrib import admin
from .models import Capability, CapabilityCategory

@admin.register(CapabilityCategory)
class CapabilityCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


# admin.py

@admin.register(Capability)
class CapabilityAdmin(admin.ModelAdmin):
    list_display = ['name', 'standard', 'category', 'total_cost_display']
    list_filter = ['category']
    search_fields = ['name', 'standard']

    fieldsets = (
        ("Basic Information", {
            'fields': ('name', 'standard', 'category')
        }),
        ("Base & Breakdown Costs", {
            'fields': (
                'cost_usd',
                'setup_cost',
                'size_adjustment',
                'material_surcharge',
                'testing_cert_cost',
                'post_process_cost',
                'env_fee',
            )
        }),
        ("Extended Pricing", {
            'fields': (
                'base_job_setup_fee',
                'min_per_part_price',
                'simple_part_price',
                'complex_part_price',
                'optional_addons',
            )
        }),
    )

    def total_cost_display(self, obj):
        return f"${obj.total_cost():.2f}"
    total_cost_display.short_description = "Total Cost"

    def has_change_permission(self, request, obj=None):
        return request.user.groups.filter(name='Sales Leads').exists() or request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.groups.filter(name='Sales Leads').exists() or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.groups.filter(name='Sales Leads').exists() or request.user.is_superuser
