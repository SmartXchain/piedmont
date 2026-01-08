# ndt/forms.py
from __future__ import annotations

from django import forms

from .models import (
    ConcentrationCurve,
    CurvePoint,
    EmulsifierMix,
    EmulsifierProduct,
    EmulsifierProductLot,
    WeeklyEmulsifierCheck,
)

DT_LOCAL_FORMAT = "%Y-%m-%dT%H:%M"


class EmulsifierProductForm(forms.ModelForm):
    class Meta:
        model = EmulsifierProduct
        fields = ["manufacturer", "name", "notes"]
        widgets = {
            "manufacturer": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }


class EmulsifierProductLotForm(forms.ModelForm):
    class Meta:
        model = EmulsifierProductLot
        fields = [
            "product",
            "lot_number",
            "received_date",
            "expiration_date",
            "vendor",
            "is_active",
            "notes",
        ]
        widgets = {
            "product": forms.Select(attrs={"class": "form-select"}),
            "lot_number": forms.TextInput(attrs={"class": "form-control"}),
            "received_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "expiration_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "vendor": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = EmulsifierProduct.objects.order_by(
            "manufacturer", "name"
        )


class ConcentrationCurveForm(forms.ModelForm):
    class Meta:
        model = ConcentrationCurve
        fields = [
            "name",
            "product_lot",
            "is_active",
            "refractometer_id",
            "water_source",
            "temperature_note",
            "target_percent",
            "low_limit_percent",
            "high_limit_percent",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "product_lot": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "refractometer_id": forms.TextInput(attrs={"class": "form-control"}),
            "water_source": forms.TextInput(attrs={"class": "form-control"}),
            "temperature_note": forms.TextInput(attrs={"class": "form-control"}),
            "target_percent": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "low_limit_percent": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "high_limit_percent": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["product_lot"].queryset = (
            EmulsifierProductLot.objects.select_related("product").order_by(
                "-is_active",
                "product__manufacturer",
                "product__name",
                "lot_number",
            )
        )


class CurvePointForm(forms.ModelForm):
    class Meta:
        model = CurvePoint
        fields = ["reading", "concentration_percent"]
        widgets = {
            "reading": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
            "concentration_percent": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
        }

    def clean(self):
        cleaned = super().clean()

        reading = cleaned.get("reading")
        curve = getattr(self.instance, "curve", None)

        # If the curve is not attached yet (it gets attached in the view), skip here.
        if reading is None or curve is None or curve.pk is None:
            return cleaned

        qs = CurvePoint.objects.filter(curve=curve, reading=reading)

        # If editing an existing point, exclude itself
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            self.add_error(
                "reading",
                "That refractometer reading already exists for this curve. "
                "Edit the existing point instead of adding a duplicate.",
            )

        return cleaned


class EmulsifierMixForm(forms.ModelForm):
    class Meta:
        model = EmulsifierMix
        fields = [
            "name",
            "product_lot",
            "curve_used",
            "mixed_at",
            "target_percent",
            "is_active",
            "notes",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "product_lot": forms.Select(attrs={"class": "form-select"}),
            "curve_used": forms.Select(attrs={"class": "form-select"}),
            "mixed_at": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "target_percent": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Make curve optional in the UI
        self.fields["curve_used"].required = False

        self.fields["product_lot"].queryset = (
            EmulsifierProductLot.objects.select_related("product")
            .order_by("-is_active", "product__manufacturer", "product__name", "lot_number")
        )

        self.fields["curve_used"].queryset = (
            ConcentrationCurve.objects.select_related("product_lot", "product_lot__product")
            .filter(is_active=True)
            .order_by("-created_at", "name")
        )

        # If product_lot is known, narrow curves to that lot
        lot = None
        if self.is_bound:
            lot_id = self.data.get("product_lot")
            if lot_id and str(lot_id).isdigit():
                lot = EmulsifierProductLot.objects.filter(pk=int(lot_id)).first()
        elif self.instance and self.instance.product_lot_id:
            lot = self.instance.product_lot

        if lot:
            self.fields["curve_used"].queryset = self.fields["curve_used"].queryset.filter(
                product_lot=lot
            )


class WeeklyEmulsifierCheckForm(forms.ModelForm):
    checked_at = forms.DateTimeField(
        input_formats=[DT_LOCAL_FORMAT],
        widget=forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
        required=False,
    )

    class Meta:
        model = WeeklyEmulsifierCheck
        fields = [
            "mix",
            "checked_at",
            "curve_used",
            "refractometer_reading",
            "comments",
        ]
        widgets = {
            "mix": forms.Select(attrs={"class": "form-select"}),
            "curve_used": forms.Select(attrs={"class": "form-select"}),
            "refractometer_reading": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.001"}
            ),
            "comments": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.fields["mix"].queryset = (
            EmulsifierMix.objects.select_related("product_lot", "product_lot__product")
            .order_by("-is_active", "-mixed_at", "name")
        )

        self.fields["curve_used"].required = False
        self.fields["curve_used"].queryset = (
            ConcentrationCurve.objects.select_related("product_lot", "product_lot__product")
            .filter(is_active=True)
            .order_by("-created_at", "name")
        )

        mix = None
        if self.is_bound:
            mix_id = self.data.get("mix")
            if mix_id and str(mix_id).isdigit():
                mix = (
                    EmulsifierMix.objects.select_related("product_lot")
                    .filter(pk=int(mix_id))
                    .first()
                )
        elif self.instance and self.instance.mix_id:
            mix = self.instance.mix

        if mix and mix.product_lot_id:
            self.fields["curve_used"].queryset = self.fields["curve_used"].queryset.filter(
                product_lot=mix.product_lot
            )

