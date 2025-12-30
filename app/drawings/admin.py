# drawings/admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Drawing, DrawingZone, PlatingAreaCard, PlatingCardZoneSelection


class DrawingZoneInline(admin.TabularInline):
    model = DrawingZone
    extra = 0
    fields = (
        "plating_type",
        "label",
        "geom_type",
        "area_value",
        "area_unit",
        "is_exclusion_zone",
        "default_selected",
        "updated_at",
    )
    readonly_fields = ("updated_at",)
    show_change_link = True


class PlatingCardZoneSelectionInline(admin.TabularInline):
    model = PlatingCardZoneSelection
    extra = 0
    autocomplete_fields = ("zone",)
    fields = ("zone", "selected")


@admin.register(Drawing)
class DrawingAdmin(admin.ModelAdmin):
    list_display = (
        "drawing_number",
        "revision",
        "title",
        "is_active",
        "pdf_link",
        "annotate_link",
    )
    search_fields = ("drawing_number",)
    ordering = ("drawing_number", "-uploaded_at")
    date_hierarchy = "uploaded_at"

    fieldsets = (
        ("Identification", {"fields": ("drawing_number", "title", "revision", "is_active")}),
        ("File", {"fields": ("pdf_file",)}),
        ("Control", {"fields": ("effective_date", "superseded_date", "notes")}),
        ("Audit", {"fields": ("uploaded_by", "uploaded_at"), "classes": ("collapse",)}),
    )
    readonly_fields = ("uploaded_at",)

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description="PDF")
    def pdf_link(self, obj):
        if not obj.pdf_file:
            return "-"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">Open PDF</a>',
            obj.pdf_file.url,
        )

    @admin.display(description="Annotate")
    def annotate_link(self, obj):
        try:
            url = reverse("drawings:annotate", kwargs={"drawing_id": obj.id})
        except Exception:
            return "— (add drawings:annotate url)"
        return format_html('<a class="button" href="{}">Annotate</a>', url)


@admin.register(DrawingZone)
class DrawingZoneAdmin(admin.ModelAdmin):
    list_display = (
        "drawing",
        "plating_type",
        "label",
        "geom_type",
        "area_value",
        "area_unit",
        "is_exclusion_zone",
        "default_selected",
        "updated_at",
    )
    search_fields = ("drawing__drawing_number",)
    ordering = ("drawing", "plating_type", "id")
    autocomplete_fields = ("drawing",)
    readonly_fields = ("created_by", "created_at", "updated_at")

    fieldsets = (
        ("Zone", {"fields": ("drawing", "plating_type", "label", "geom_type")}),
        ("Geometry", {"fields": ("geometry",)}),
        ("Area", {"fields": ("area_value", "area_unit", "is_exclusion_zone", "default_selected")}),
        ("Notes", {"fields": ("notes",)}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PlatingAreaCard)
class PlatingAreaCardAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "drawing",
        "plating_type",
        "part_number",
        "net_area_value",
        "area_unit",
        "is_active",
        "approved_at",
        "updated_at",
    )
    search_fields = ("drawing__drawing_number",)
    ordering = ("-updated_at",)
    date_hierarchy = "updated_at"
    autocomplete_fields = ("drawing",)
    readonly_fields = ("created_by", "created_at", "updated_at")
    inlines = (PlatingCardZoneSelectionInline,)

    fieldsets = (
        ("Linkage", {"fields": ("drawing", "plating_type", "part_number", "is_active")}),
        ("Area Totals", {"fields": ("gross_area_value", "excluded_area_value", "net_area_value", "area_unit")}),
        ("Basis & Traceability", {"fields": ("basis", "assumptions", "drawing_reference")}),
        ("Approval", {"fields": ("approved_by", "approved_at")}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PlatingCardZoneSelection)
class PlatingCardZoneSelectionAdmin(admin.ModelAdmin):
    list_display = ("plating_card", "zone", "selected")
    search_fields = ("plating_card__drawing__drawing_number",)
    autocomplete_fields = ("plating_card", "zone")

