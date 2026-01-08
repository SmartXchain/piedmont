# ndt/models.py
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import UniqueConstraint
from django.utils import timezone


class EmulsifierProduct(models.Model):
    """
    Track which hydrophilic emulsifier/remover product the curve applies to.
    Different products/lots can have different refractometer-to-% behavior.
    """

    name = models.CharField(max_length=120)  # e.g., "ZR-10B"
    manufacturer = models.CharField(max_length=120, blank=True)  # e.g., "Magnaflux"
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["manufacturer", "name"]

    def __str__(self) -> str:
        return f"{self.manufacturer} {self.name}".strip()


class EmulsifierProductLot(models.Model):
    """
    A specific lot/batch of an emulsifier product.
    Curves and mixes should be tied to the lot used to build/prepare them.
    """

    product = models.ForeignKey(
        EmulsifierProduct,
        on_delete=models.CASCADE,
        related_name="lots",
        db_index=True,
    )
    lot_number = models.CharField(max_length=80, db_index=True)
    received_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    vendor = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-is_active", "product__manufacturer", "product__name", "lot_number"]
        constraints = [
            UniqueConstraint(
                fields=["product", "lot_number"],
                name="uniq_product_lot_number",
            )
        ]

    def __str__(self) -> str:
        return f"{self.product} | Lot {self.lot_number}"


class ConcentrationCurve(models.Model):
    """
    Calibration curve mapping refractometer reading -> % concentration.

    Practice:
    - Prepare known concentrations (e.g., 5/10/15/20/25/30%)
    - Measure refractometer readings
    - Use the curve to convert weekly readings to % concentration
    """

    name = models.CharField(max_length=150)

    product_lot = models.ForeignKey(
        EmulsifierProductLot,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="curves",
        help_text="Lot number used to build this calibration curve.",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="emulsifier_curves_created",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    # Optional metadata (audit-friendly)
    refractometer_id = models.CharField(max_length=80, blank=True)
    water_source = models.CharField(max_length=120, blank=True)
    temperature_note = models.CharField(max_length=120, blank=True)

    # Optional working range
    target_percent = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    low_limit_percent = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    high_limit_percent = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["-is_active", "-created_at", "name"]

    def __str__(self) -> str:
        if self.product_lot_id:
            return f"{self.name} ({self.product_lot})"
        return self.name

    @property
    def product(self) -> Optional[EmulsifierProduct]:
        """
        Convenience accessor: returns the product via product_lot.
        """
        if not self.product_lot_id:
            return None
        return self.product_lot.product

    def clean(self) -> None:
        if self.low_limit_percent is not None and self.high_limit_percent is not None:
            if self.low_limit_percent > self.high_limit_percent:
                raise ValidationError("Low limit % cannot be greater than high limit %.")

    def points(self) -> List["CurvePoint"]:
        """
        Return curve points in ascending refractometer reading order.
        """
        return list(self.curve_points.order_by("reading"))

    def concentration_from_reading(self, reading: Decimal) -> Decimal:
        """
        Convert a refractometer reading to concentration using piecewise linear interpolation.

        - Requires at least 2 points.
        - Raises ValidationError if reading is outside curve bounds.
        """
        pts = self.points()
        if len(pts) < 2:
            raise ValidationError("Curve must have at least 2 points to compute concentration.")

        xs = [p.reading for p in pts]
        ys = [p.concentration_percent for p in pts]

        if reading < xs[0] or reading > xs[-1]:
            raise ValidationError(
                f"Reading {reading} is outside curve bounds ({xs[0]} to {xs[-1]})."
            )

        # Exact match
        for x, y in zip(xs, ys):
            if reading == x:
                return y

        # Find segment containing reading
        for i in range(len(xs) - 1):
            x0, x1 = xs[i], xs[i + 1]
            if x0 <= reading <= x1:
                y0, y1 = ys[i], ys[i + 1]
                if x1 == x0:
                    return y0
                return y0 + (reading - x0) * (y1 - y0) / (x1 - x0)

        raise ValidationError("Unable to interpolate concentration for this reading.")


class CurvePoint(models.Model):
    """
    One calibration point on the curve.
    Example: reading=14.000, concentration_percent=17.00
    """

    curve = models.ForeignKey(
        ConcentrationCurve,
        on_delete=models.CASCADE,
        related_name="curve_points",
    )

    reading = models.DecimalField(max_digits=7, decimal_places=3)
    concentration_percent = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        ordering = ["reading"]
        constraints = [
            UniqueConstraint(
                fields=["curve", "reading"],
                name="uniq_curve_reading",
            )
        ]

    def __str__(self) -> str:
        return f"{self.curve}: {self.reading} -> {self.concentration_percent}%"

    def clean(self) -> None:
        if self.concentration_percent < 0:
            raise ValidationError("Concentration % cannot be negative.")


class EmulsifierMix(models.Model):
    """
    Represents the event when the solution was mixed.
    Weekly checks reference this for traceability.
    """

    name = models.CharField(
        max_length=160,
        help_text="Example: 'PT Line Method D Mix - Jan 2026 - Batch 1'",
    )

    product_lot = models.ForeignKey(
        EmulsifierProductLot,
        on_delete=models.PROTECT,
        related_name="mixes",
    )

    curve_used = models.ForeignKey(
        ConcentrationCurve,
        on_delete=models.PROTECT,
        related_name="mixes",
        null=True,
        blank=True,
        help_text="Optional: lock the intended curve for this mix (recommended).",
    )

    mixed_at = models.DateTimeField(default=timezone.now)

    mixed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="emulsifier_mixes",
        null=True,
        blank=True,
    )

    target_percent = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-is_active", "-mixed_at", "name"]

    def __str__(self) -> str:
        return f"{self.name} | {self.product_lot}"

    def clean(self) -> None:
        if self.curve_used_id and self.curve_used.product_lot_id:
            if self.curve_used.product_lot_id != self.product_lot_id:
                raise ValidationError(
                    "Selected curve lot does not match the mix product lot."
                )


class WeeklyEmulsifierCheck(models.Model):
    """
    Weekly record: operator enters refractometer reading; app stores computed concentration.
    References the MIX event (solution batch).
    """

    mix = models.ForeignKey(
        EmulsifierMix,
        on_delete=models.PROTECT,
        related_name="weekly_checks",
    )

    curve_used = models.ForeignKey(
        ConcentrationCurve,
        on_delete=models.PROTECT,
        related_name="weekly_checks",
        help_text="Curve used for the calculation (captured for traceability).",
    )

    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="emulsifier_checks",
    )

    checked_at = models.DateTimeField(default=timezone.now)

    refractometer_reading = models.DecimalField(max_digits=7, decimal_places=3)
    calculated_concentration_percent = models.DecimalField(
        max_digits=6, decimal_places=2, editable=False
    )

    in_limits = models.BooleanField(default=True, editable=False)
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ["-checked_at"]
        constraints = [
            UniqueConstraint(
                fields=["mix", "checked_at"],
                name="uniq_mix_checked_at",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.mix} @ {self.checked_at:%Y-%m-%d} = "
            f"{self.calculated_concentration_percent}%"
        )

    def save(self, *args, **kwargs) -> None:
        # Default curve selection:
        # 1) Use mix.curve_used if provided
        if not self.curve_used_id and self.mix_id and self.mix.curve_used_id:
            self.curve_used = self.mix.curve_used

        if not self.curve_used_id:
            raise ValidationError("A concentration curve must be selected (curve_used).")

        # Hard guard: curve lot must match mix lot (if curve has a lot)
        if self.curve_used.product_lot_id and self.mix.product_lot_id:
            if self.curve_used.product_lot_id != self.mix.product_lot_id:
                raise ValidationError("Curve lot does not match the mix product lot.")

        conc = self.curve_used.concentration_from_reading(self.refractometer_reading)
        self.calculated_concentration_percent = conc.quantize(Decimal("0.01"))

        low = self.curve_used.low_limit_percent
        high = self.curve_used.high_limit_percent
        if low is not None and self.calculated_concentration_percent < low:
            self.in_limits = False
        elif high is not None and self.calculated_concentration_percent > high:
            self.in_limits = False
        else:
            self.in_limits = True

        super().save(*args, **kwargs)

