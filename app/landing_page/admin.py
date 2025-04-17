from django.contrib import admin

from .models import (
    Capability,
    CapabilityCategory,
    CapabilityTag,
    AddOn,
    AddOnTag
)


@admin.register(CapabilityCategory)
class CapabilityCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(CapabilityTag)
class CapabilityTagAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(AddOnTag)
class AddOnTagAdmin(admin.ModelAdmin):
    list_display = ['name']


class AddOnTagInline(admin.TabularInline):
    model = AddOn.tags.through
    extra = 1
    verbose_name = "Tag"
    verbose_name_plural = "Tags"


@admin.register(AddOn)
class AddOnAdmin(admin.ModelAdmin):
    list_display = ['name', 'price']
    inlines = [AddOnTagInline]
    exclude = ('tags',)


class CapabilityTagInline(admin.TabularInline):
    model = Capability.tags.through
    extra = 1
    verbose_name = "Tag"
    verbose_name_plural = "Tags"


@admin.register(Capability)
class CapabilityAdmin(admin.ModelAdmin):
    list_display = ['name', 'standard', 'category', 'total_cost_display']
    list_filter = ['category']
    search_fields = ['name', 'standard']
    inlines = [CapabilityTagInline]
    exclude = ('tags',)

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
                'addons',
            )
        }),
    )

    def total_cost_display(self, obj):
        return f"${obj.total_with_addons():.2f}"

    total_cost_display.short_description = "Total with Add-ons"
