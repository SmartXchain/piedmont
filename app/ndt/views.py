# ndt/views.py
from __future__ import annotations

from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView
from django.core.exceptions import ValidationError

from .forms import (
    ConcentrationCurveForm,
    CurvePointForm,
    EmulsifierMixForm,
    EmulsifierProductForm,
    EmulsifierProductLotForm,
    WeeklyEmulsifierCheckForm,
)
from .models import (
    ConcentrationCurve,
    CurvePoint,
    EmulsifierMix,
    EmulsifierProduct,
    EmulsifierProductLot,
    WeeklyEmulsifierCheck,
)


class NDTLandingView(TemplateView):
    template_name = "ndt/index.html"


# -----------------------
# Products
# -----------------------
class ProductListView(ListView):
    model = EmulsifierProduct
    template_name = "ndt/product_list.html"
    context_object_name = "products"
    paginate_by = 25

    def get_queryset(self):
        qs = (
            EmulsifierProduct.objects.all()
            .annotate(lot_count=Count("lots", distinct=True))
            .order_by("manufacturer", "name")
        )
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(manufacturer__icontains=q) | Q(name__icontains=q))
        return qs


class ProductCreateView(CreateView):
    model = EmulsifierProduct
    form_class = EmulsifierProductForm
    template_name = "ndt/product_form.html"

    def get_success_url(self):
        return reverse("ndt:product_list")

    def form_valid(self, form):
        messages.success(self.request, "Product created.")
        return super().form_valid(form)


class ProductUpdateView(UpdateView):
    model = EmulsifierProduct
    form_class = EmulsifierProductForm
    template_name = "ndt/product_form.html"

    def get_success_url(self):
        return reverse("ndt:product_list")

    def form_valid(self, form):
        messages.success(self.request, "Product updated.")
        return super().form_valid(form)


# -----------------------
# Lots
# -----------------------
class LotListView(ListView):
    model = EmulsifierProductLot
    template_name = "ndt/lot_list.html"
    context_object_name = "lots"
    paginate_by = 50

    def get_queryset(self):
        qs = (
            EmulsifierProductLot.objects.select_related("product")
            .all()
            .order_by("-is_active", "product__manufacturer", "product__name", "lot_number")
        )

        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(lot_number__icontains=q)
                | Q(vendor__icontains=q)
                | Q(product__name__icontains=q)
                | Q(product__manufacturer__icontains=q)
            )
        return qs


class ProductLotListView(ListView):
    model = EmulsifierProductLot
    template_name = "ndt/lot_list.html"
    context_object_name = "lots"
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(EmulsifierProduct, pk=kwargs["product_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            EmulsifierProductLot.objects.select_related("product")
            .filter(product=self.product)
            .order_by("-is_active", "lot_number")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["product"] = self.product
        return ctx


class LotCreateView(CreateView):
    model = EmulsifierProductLot
    form_class = EmulsifierProductLotForm
    template_name = "ndt/lot_form.html"

    def get_initial(self):
        initial = super().get_initial()
        product_id = self.request.GET.get("product")
        if product_id and product_id.isdigit():
            initial["product"] = int(product_id)
        return initial

    def get_success_url(self):
        return reverse("ndt:product_lot_list", kwargs={"product_id": self.object.product_id})

    def form_valid(self, form):
        messages.success(self.request, "Lot created.")
        return super().form_valid(form)


class LotUpdateView(UpdateView):
    model = EmulsifierProductLot
    form_class = EmulsifierProductLotForm
    template_name = "ndt/lot_form.html"

    def get_success_url(self):
        return reverse("ndt:product_lot_list", kwargs={"product_id": self.object.product_id})

    def form_valid(self, form):
        messages.success(self.request, "Lot updated.")
        return super().form_valid(form)


# -----------------------
# Mixes (solution batch events)
# -----------------------
class MixListView(ListView):
    model = EmulsifierMix
    template_name = "ndt/mix_list.html"
    context_object_name = "mixes"
    paginate_by = 50

    def get_queryset(self):
        qs = (
            EmulsifierMix.objects.select_related(
                "product_lot",
                "product_lot__product",
                "curve_used",
            )
            .all()
            .order_by("-is_active", "-mixed_at", "name")
        )

        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(product_lot__lot_number__icontains=q)
                | Q(product_lot__product__name__icontains=q)
                | Q(product_lot__product__manufacturer__icontains=q)
                | Q(curve_used__name__icontains=q)
            )

        active = (self.request.GET.get("active") or "").strip().lower()
        if active in {"0", "1"}:
            qs = qs.filter(is_active=(active == "1"))

        return qs


class MixCreateView(CreateView):
    model = EmulsifierMix
    form_class = EmulsifierMixForm
    template_name = "ndt/mix_form.html"

    def get_initial(self):
        initial = super().get_initial()
        initial["mixed_at"] = timezone.localtime(timezone.now()).strftime("%Y-%m-%dT%H:%M")

        lot_id = self.request.GET.get("product_lot")
        if lot_id and lot_id.isdigit():
            initial["product_lot"] = int(lot_id)

        curve_id = self.request.GET.get("curve_used")
        if curve_id and curve_id.isdigit():
            initial["curve_used"] = int(curve_id)

        return initial

    def form_valid(self, form):
        if not form.instance.mixed_by_id and self.request.user.is_authenticated:
            form.instance.mixed_by = self.request.user
        messages.success(self.request, "Mix created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("ndt:mix_list")


class MixUpdateView(UpdateView):
    model = EmulsifierMix
    form_class = EmulsifierMixForm
    template_name = "ndt/mix_form.html"
    context_object_name = "mix"

    def form_valid(self, form):
        if not form.instance.mixed_by_id and self.request.user.is_authenticated:
            form.instance.mixed_by = self.request.user
        messages.success(self.request, "Mix updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("ndt:mix_list")


# -----------------------
# Curves
# -----------------------
class CurveListView(ListView):
    model = ConcentrationCurve
    template_name = "ndt/curve_list.html"
    context_object_name = "curves"
    paginate_by = 25

    def get_queryset(self):
        qs = (
            ConcentrationCurve.objects.select_related("product_lot", "product_lot__product")
            .annotate(point_count=Count("curve_points", distinct=True))
            .order_by("-is_active", "-created_at", "name")
        )

        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(product_lot__lot_number__icontains=q)
                | Q(product_lot__product__name__icontains=q)
                | Q(product_lot__product__manufacturer__icontains=q)
            )

        active = (self.request.GET.get("active") or "").strip().lower()
        if active in {"0", "1"}:
            qs = qs.filter(is_active=(active == "1"))

        return qs


class CurveCreateView(CreateView):
    model = ConcentrationCurve
    form_class = ConcentrationCurveForm
    template_name = "ndt/curve_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.mix = None
        mix_id = request.GET.get("mix")
        if mix_id and str(mix_id).isdigit():
            self.mix = EmulsifierMix.objects.select_related("product_lot").filter(
                pk=int(mix_id)
            ).first()
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()

        # If creating from a mix, prefill the lot
        if self.mix and self.mix.product_lot_id:
            initial["product_lot"] = self.mix.product_lot_id

        # Keep your existing querystring support
        product_lot_id = self.request.GET.get("product_lot")
        if product_lot_id:
            initial["product_lot"] = product_lot_id

        return initial

    def form_valid(self, form):
        if not form.instance.created_by_id and self.request.user.is_authenticated:
            form.instance.created_by = self.request.user

        response = super().form_valid(form)

        # ✅ If we started from a mix, assign the new curve back to the mix
        if self.mix:
            self.mix.curve_used = self.object
            if self.request.user.is_authenticated and not self.mix.mixed_by_id:
                self.mix.mixed_by = self.request.user
            self.mix.save(update_fields=["curve_used", "mixed_by"])

        messages.success(self.request, "Curve created.")
        return response

    def get_success_url(self):
        return reverse("ndt:curve_detail", kwargs={"pk": self.object.pk})


class CurveUpdateView(UpdateView):
    model = ConcentrationCurve
    form_class = ConcentrationCurveForm
    template_name = "ndt/curve_form.html"

    def get_success_url(self):
        return reverse("ndt:curve_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Curve updated.")
        return super().form_valid(form)


class CurveDetailView(DetailView):
    model = ConcentrationCurve
    template_name = "ndt/curve_detail.html"
    context_object_name = "curve"

    def get_queryset(self):
        return ConcentrationCurve.objects.select_related(
            "product_lot",
            "product_lot__product",
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        points_qs = self.object.curve_points.order_by("reading")

        # For the table (QuerySet is fine)
        ctx["points"] = points_qs

        # For Chart.js (serialize to JSON-safe primitives)
        ctx["points_json"] = list(
            points_qs.values("reading", "concentration_percent")
        )

        return ctx


class CurvePointCreateView(CreateView):
    model = CurvePoint
    form_class = CurvePointForm
    template_name = "ndt/curvepoint_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.curve = get_object_or_404(ConcentrationCurve, pk=kwargs["curve_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Attach curve early so form.clean() can validate duplicates cleanly
        form.instance.curve = self.curve
        return form

    def form_valid(self, form):
        form.instance.curve = self.curve
        messages.success(self.request, "Curve point added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("ndt:curve_detail", kwargs={"pk": self.curve.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["curve"] = self.curve
        return ctx


class CurvePointUpdateView(UpdateView):
    model = CurvePoint
    form_class = CurvePointForm
    template_name = "ndt/curvepoint_form.html"
    context_object_name = "point"

    def get_success_url(self):
        return reverse("ndt:curve_detail", kwargs={"pk": self.object.curve_id})

    def form_valid(self, form):
        messages.success(self.request, "Curve point updated.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["curve"] = self.object.curve
        return ctx


class CurvePointDeleteView(DeleteView):
    model = CurvePoint
    template_name = "ndt/confirm_delete.html"
    context_object_name = "point"

    def get_success_url(self):
        return reverse("ndt:curve_detail", kwargs={"pk": self.object.curve_id})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Delete curve point"
        ctx["message"] = (
            f"Delete point {self.object.reading} → {self.object.concentration_percent}%?"
        )
        return ctx


# -----------------------
# Weekly checks
# -----------------------
class WeeklyCheckListView(ListView):
    model = WeeklyEmulsifierCheck
    template_name = "ndt/log_list.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        qs = (
            WeeklyEmulsifierCheck.objects.select_related(
                "mix",
                "mix__product_lot",
                "mix__product_lot__product",
                "operator",
                "curve_used",
                "curve_used__product_lot",
                "curve_used__product_lot__product",
            )
            .all()
            .order_by("-checked_at")
        )

        mix_id = (self.request.GET.get("mix") or "").strip()
        if mix_id.isdigit():
            qs = qs.filter(mix_id=int(mix_id))

        in_limits = (self.request.GET.get("in_limits") or "").strip().lower()
        if in_limits in {"0", "1"}:
            qs = qs.filter(in_limits=(in_limits == "1"))

        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                Q(mix__name__icontains=q)
                | Q(mix__product_lot__lot_number__icontains=q)
                | Q(mix__product_lot__product__name__icontains=q)
                | Q(mix__product_lot__product__manufacturer__icontains=q)
                | Q(operator__username__icontains=q)
                | Q(operator__first_name__icontains=q)
                | Q(operator__last_name__icontains=q)
                | Q(curve_used__name__icontains=q)
                | Q(curve_used__product_lot__lot_number__icontains=q)
                | Q(curve_used__product_lot__product__name__icontains=q)
                | Q(curve_used__product_lot__product__manufacturer__icontains=q)
            )

        return qs

class WeeklyCheckDetailView(DetailView):
    model = WeeklyEmulsifierCheck
    template_name = "ndt/log_detail.html"
    context_object_name = "log"

    def get_queryset(self):
        return WeeklyEmulsifierCheck.objects.select_related(
            "mix",
            "mix__product_lot",
            "mix__product_lot__product",
            "operator",
            "curve_used",
            "curve_used__product_lot",
            "curve_used__product_lot__product",
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        curve = self.object.curve_used
        points_qs = curve.curve_points.order_by("reading")

        ctx["curve"] = curve
        ctx["points"] = points_qs

        # Chart.js-safe primitives
        ctx["points_json"] = list(points_qs.values("reading", "concentration_percent"))

        # Weekly check point (x = concentration, y = reading)
        ctx["weekly_point"] = {
            "x": float(self.object.calculated_concentration_percent),
            "y": float(self.object.refractometer_reading),
        }

        # Limits as floats (or None)
        ctx["limits"] = {
            "low": float(curve.low_limit_percent) if curve.low_limit_percent is not None else None,
            "high": float(curve.high_limit_percent) if curve.high_limit_percent is not None else None,
            "target": float(curve.target_percent) if curve.target_percent is not None else None,
        }

        return ctx


class WeeklyCheckCreateView(CreateView):
    model = WeeklyEmulsifierCheck
    form_class = WeeklyEmulsifierCheckForm
    template_name = "ndt/log_form.html"

    def get_initial(self):
        initial = super().get_initial()
        initial["checked_at"] = timezone.localtime(timezone.now()).strftime("%Y-%m-%dT%H:%M")

        mix_id = self.request.GET.get("mix")
        if mix_id and mix_id.isdigit():
            initial["mix"] = int(mix_id)

        curve_id = self.request.GET.get("curve_used")
        if curve_id and curve_id.isdigit():
            initial["curve_used"] = int(curve_id)

        return initial

    def form_valid(self, form):
        # ✅ Set operator on the instance BEFORE saving
        if self.request.user.is_authenticated:
            form.instance.operator = self.request.user
        else:
            form.add_error(None, "You must be logged in to record a weekly check.")
            return self.form_invalid(form)

        messages.success(self.request, "Weekly check saved.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("ndt:log_detail", kwargs={"pk": self.object.pk})


class WeeklyCheckUpdateView(UpdateView):
    model = WeeklyEmulsifierCheck
    form_class = WeeklyEmulsifierCheckForm
    template_name = "ndt/log_form.html"

    def get_queryset(self):
        return WeeklyEmulsifierCheck.objects.select_related("mix", "curve_used")

    def form_valid(self, form):
        # keep existing operator if already set; otherwise set to current user
        if not form.instance.operator_id:
            if self.request.user.is_authenticated:
                form.instance.operator = self.request.user
            else:
                form.add_error(None, "You must be logged in to record a weekly check.")
                return self.form_invalid(form)

        messages.success(self.request, "Weekly check updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("ndt:log_detail", kwargs={"pk": self.object.pk})

