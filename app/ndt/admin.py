# ndt/admin.py
from __future__ import annotations

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet
from django.utils import timezone

from .models import (
    ConcentrationCurve,
    CurvePoint,
    EmulsifierMix,
    EmulsifierProduct,
    EmulsifierProductLot,
    WeeklyEmulsifierCheck,
)


# -----------------------------
# Inlines
# -----------------------------
class CurvePointInlineFormSet(BaseInlineFormSet):
    """
    Enforce a minimum of 2 curve points and require ascending readings.
    """

    def clean(self) -> None:
        super().clean()

        points = []
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("DELETE"):
                continue

            reading = form.cleaned_data.get("reading")
            conc = form.cleaned_data.get("concentration_percent")
            if reading is None or conc is None:
                continue

            points.append((reading, conc))

        if len(points) < 2:
            raise ValidationError("A curve must have at least 2 calibration points.")

        readings = [p[0] for p in points]
        if len(readings) != len(set(readings)):
            raise ValidationError(
                "Duplicate refractometer readings are not allowed in a curve."
            )

        if readings != sorted(readings):
            raise ValidationError("Curve points must be entered in ascending order.")


class CurvePointInline(admin.TabularInline):
    model = CurvePoint
    formset = CurvePointInlineFormSet
    extra = 0
    min_num = 2
    fields = ("reading", "concentration_percent")
    ordering = ("reading",)


# -----------------------------
# Admin actions
# -----------------------------
@admin.action(description="Mark selected curves as ACTIVE")
def make_curves_active(modeladmin: admin.ModelAdmin, request, queryset) -> None:
    updated = queryset.update(is_active=True)
    modeladmin.message_user(
        request,
        f"Activated {updated} curve(s).",
        level=messages.SUCCESS,
    )


@admin.action(description="Mark selected curves as INACTIVE")
def make_curves_inactive(modeladmin: admin.ModelAdmin, request, queryset) -> None:
    updated = queryset.update(is_active=False)
    modeladmin.message_user(
        request,
        f"Deactivated {updated} curve(s).",
        level=messages.SUCCESS,
    )


# -----------------------------
# ModelAdmins
# -----------------------------
@admin.register(EmulsifierProduct)
class EmulsifierProductAdmin(admin.ModelAdmin):
    list_display = ("manufacturer", "name")
    search_fields = ("manufacturer", "name")
    ordering = ("manufacturer", "name")


@admin.register(EmulsifierProductLot)
class EmulsifierProductLotAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "lot_number",
        "is_active",
        "received_date",
        "expiration_date",
        "vendor",
    )
    list_filter = ("is_active", "product__manufacturer", "product__name")
    search_fields = (
        "lot_number",
        "vendor",
        "product__name",
        "product__manufacturer",
    )
    autocomplete_fields = ("product",)
    ordering = ("-is_active", "product__manufacturer", "product__name", "lot_number")


@admin.register(ConcentrationCurve)
class ConcentrationCurveAdmin(admin.ModelAdmin):
    inlines = [CurvePointInline]

    list_display = (
        "name",
        "product_lot",
        "is_active",
        "created_at",
        "created_by",
        "refractometer_id",
        "target_percent",
        "low_limit_percent",
        "high_limit_percent",
    )
    list_filter = ("is_active", "product_lot", "created_at")
    search_fields = (
        "name",
        "refractometer_id",
        "product_lot__lot_number",
        "product_lot__product__name",
        "product_lot__product__manufacturer",
    )
    autocomplete_fields = ("product_lot", "created_by")
    date_hierarchy = "created_at"
    actions = [make_curves_active, make_curves_inactive]

    fieldsets = (
        ("Curve", {"fields": ("name", "product_lot", "is_active")}),
        (
            "Limits / Targets (optional)",
            {"fields": ("target_percent", "low_limit_percent", "high_limit_percent")},
        ),
        (
            "Instrumentation / Conditions (optional)",
            {"fields": ("refractometer_id", "water_source", "temperature_note")},
        ),
        ("Traceability", {"fields": ("created_by",)}),
    )

    def save_model(self, request, obj, form, change) -> None:
        if not change and not obj.created_by_id and request.user.is_authenticated:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EmulsifierMix)
class EmulsifierMixAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "product_lot",
        "curve_used",
        "mixed_at",
        "mixed_by",
        "is_active",
    )
    list_filter = (
        "is_active",
        "product_lot__product__manufacturer",
        "product_lot__product__name",
        "mixed_at",
    )
    search_fields = (
        "name",
        "product_lot__lot_number",
        "product_lot__product__name",
        "product_lot__product__manufacturer",
        "curve_used__name",
        "mixed_by__username",
        "mixed_by__first_name",
        "mixed_by__last_name",
    )
    autocomplete_fields = ("product_lot", "curve_used", "mixed_by")
    date_hierarchy = "mixed_at"
    ordering = ("-is_active", "-mixed_at", "name")

    fieldsets = (
        ("Mix", {"fields": ("name", "is_active")}),
        ("Lot / Curve", {"fields": ("product_lot", "curve_used")}),
        ("Traceability", {"fields": ("mixed_at", "mixed_by")}),
        ("Optional", {"fields": ("target_percent", "notes")}),
    )

    def save_model(self, request, obj, form, change) -> None:
        if not change and not obj.mixed_by_id and request.user.is_authenticated:
            obj.mixed_by = request.user
        if not obj.mixed_at:
            obj.mixed_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(WeeklyEmulsifierCheck)
class WeeklyEmulsifierCheckAdmin(admin.ModelAdmin):
    list_display = (
        "checked_at",
        "mix",
        "operator",
        "refractometer_reading",
        "calculated_concentration_percent",
        "in_limits",
        "curve_used",
    )
    list_filter = ("in_limits", "mix", "curve_used", "checked_at")
    search_fields = (
        "mix__name",
        "mix__product_lot__lot_number",
        "mix__product_lot__product__name",
        "mix__product_lot__product__manufacturer",
        "operator__username",
        "operator__first_name",
        "operator__last_name",
        "curve_used__name",
    )
    date_hierarchy = "checked_at"
    autocomplete_fields = ("mix", "curve_used", "operator")
    readonly_fields = ("calculated_concentration_percent", "in_limits")
    ordering = ("-checked_at",)

    fieldsets = (
        ("Entry", {"fields": ("mix", "checked_at", "operator", "refractometer_reading")}),
        (
            "Calculation (auto)",
            {"fields": ("curve_used", "calculated_concentration_percent", "in_limits")},
        ),
        ("Notes", {"fields": ("comments",)}),
    )

    def save_model(self, request, obj, form, change) -> None:
        if not obj.operator_id and request.user.is_authenticated:
            obj.operator = request.user
        if not obj.checked_at:
            obj.checked_at = timezone.now()
        super().save_model(request, obj, form, change)
