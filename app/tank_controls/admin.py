from django.contrib import admin

from .models import (
    ChemicalSpec,
    CheckSpec,
    ControlSet,
    PeriodicTestExecution,
    PeriodicTestSpec,
    Tank,
    TemperatureSpec,
)


class TemperatureSpecInline(admin.TabularInline):
    model = TemperatureSpec
    extra = 0
    fields = ("min_c", "max_c", "frequency")
    show_change_link = True


class ChemicalSpecInline(admin.TabularInline):
    model = ChemicalSpec
    extra = 0
    fields = ("chemical_name", "units", "target", "min_val", "max_val", "frequency")
    show_change_link = True


class CheckSpecInline(admin.TabularInline):
    model = CheckSpec
    extra = 0
    fields = ("name", "check_type", "frequency")
    show_change_link = True


class PeriodicTestSpecInline(admin.TabularInline):
    model = PeriodicTestSpec
    extra = 0
    fields = ("name", "frequency", "number_of_specimens", "material", "dimensions")
    show_change_link = True


@admin.register(Tank)
class TankAdmin(admin.ModelAdmin):
    list_display = ("name", "process")
    search_fields = ("name", "process")
    ordering = ("name",)
    list_filter = ("process",)


@admin.register(ControlSet)
class ControlSetAdmin(admin.ModelAdmin):
    list_display = ("name", "tank")
    search_fields = ("name", "tank__name")
    list_filter = ("tank__process",)
    ordering = ("tank__name", "name")
    inlines = [
        TemperatureSpecInline,
        ChemicalSpecInline,
        CheckSpecInline,
        PeriodicTestSpecInline,
    ]


@admin.register(TemperatureSpec)
class TemperatureSpecAdmin(admin.ModelAdmin):
    list_display = ("control_set", "min_c", "max_c", "frequency")
    list_filter = ("frequency", "control_set__tank__process")
    search_fields = ("control_set__name",)
    ordering = ("control_set__name", "min_c", "max_c")


@admin.register(ChemicalSpec)
class ChemicalSpecAdmin(admin.ModelAdmin):
    list_display = ("control_set", "chemical_name", "units", "target", "frequency")
    list_filter = ("frequency", "control_set__tank__process", "units")
    search_fields = ("chemical_name", "control_set__name")
    ordering = ("control_set__name", "chemical_name")


@admin.register(CheckSpec)
class CheckSpecAdmin(admin.ModelAdmin):
    list_display = ("control_set", "name", "check_type", "frequency")
    list_filter = ("check_type", "frequency", "control_set__tank__process")
    search_fields = ("name", "control_set__name")
    ordering = ("control_set__name", "name")


@admin.register(PeriodicTestSpec)
class PeriodicTestSpecAdmin(admin.ModelAdmin):
    list_display = ("control_set", "name", "frequency", "number_of_specimens")
    list_filter = ("frequency", "control_set__tank__process")
    search_fields = ("name", "control_set__name", "control_set__tank__name")
    ordering = ("control_set__name", "name")


@admin.register(PeriodicTestExecution)
class PeriodicTestExecutionAdmin(admin.ModelAdmin):
    list_display = ("test_spec", "performed_on", "performed_by", "passed")
    list_filter = ("passed", "performed_on", "test_spec__frequency")
    search_fields = ("test_spec__name", "test_spec__control_set__name")
    autocomplete_fields = ("test_spec", "performed_by")
    date_hierarchy = "performed_on"
    ordering = ("-performed_on",)

