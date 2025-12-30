# drawings/views.py
from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, Optional

import fitz  # PyMuPDF
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from .models import Drawing, DrawingZone, PlatingAreaCard, PlatingCardZoneSelection


# -------------------------
# Permissions
# -------------------------
def is_engineer(user) -> bool:
    """Engineer = staff user (simple rule for now)."""
    return bool(user and user.is_authenticated and user.is_staff)


def is_operator(user) -> bool:
    """Operator = any authenticated user (tighten later with Groups if needed)."""
    return bool(user and user.is_authenticated)


# -------------------------
# Constants / Helpers
# -------------------------
PLATING_TYPES = ("cadmium", "chrome", "nickel")


def _normalize_plating_type(raw: Any) -> Optional[str]:
    if raw is None:
        return None
    val = str(raw).strip().lower()
    if val in PLATING_TYPES:
        return val
    return None


def _json_payload(request: HttpRequest) -> Dict[str, Any]:
    """Parse JSON body as dict."""
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception as exc:
        raise ValueError("Invalid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("JSON must be an object")
    return payload


def _validate_normalized_geometry(geom_type: str, geometry: Any) -> Optional[str]:
    """
    Ensures geometry uses normalized coordinates in [0..1].

    polygon: [{"x":..,"y":..}, ...] >= 3 points
    rect: {"x":..,"y":..,"w":..,"h":..} w/h > 0
    """

    def in01(v: Any) -> bool:
        return isinstance(v, (int, float)) and 0.0 <= float(v) <= 1.0

    if geom_type == "polygon":
        if not isinstance(geometry, list) or len(geometry) < 3:
            return "Polygon requires at least 3 points"
        for p in geometry:
            if not isinstance(p, dict) or "x" not in p or "y" not in p:
                return "Polygon points must be objects with x,y"
            if not (in01(p["x"]) and in01(p["y"])):
                return "Polygon x,y must be normalized 0..1"
        return None

    if geom_type == "rect":
        if not isinstance(geometry, dict):
            return "Rect geometry must be an object"
        for key in ("x", "y", "w", "h"):
            if key not in geometry or not in01(geometry[key]):
                return "Rect x,y,w,h must be normalized 0..1"
        if float(geometry["w"]) <= 0.0 or float(geometry["h"]) <= 0.0:
            return "Rect w and h must be > 0"
        return None

    return "Invalid geom_type (must be 'polygon' or 'rect')"


def _zone_to_dict(zone: DrawingZone) -> Dict[str, Any]:
    return {
        "id": zone.id,
        "drawing_id": zone.drawing_id,
        "plating_type": getattr(zone, "plating_type", None),
        "label": zone.label,
        "geom_type": zone.geom_type,
        "geometry": zone.geometry,
        "area_value": str(zone.area_value),
        "area_unit": zone.area_unit,
        "is_exclusion_zone": zone.is_exclusion_zone,
        "default_selected": zone.default_selected,
        "notes": zone.notes or "",
    }


def _card_to_context(card: PlatingAreaCard) -> Dict[str, Any]:
    return {
        "card": card,
        "drawing": card.drawing,
        "plating_type": card.plating_type,
    }


# -------------------------
# Engineering (Annotate)
# -------------------------
@require_GET
@login_required
@user_passes_test(is_engineer)
def annotate_drawing_view(request: HttpRequest, drawing_id: int) -> HttpResponse:
    """
    Engineer annotate view.

    Workflow:
    1) Engineer selects plating_type (cadmium/chrome/nickel)
    2) A unique PlatingAreaCard is created/get for (drawing + plating_type)
    3) All zones created/edited during this session are tied to (drawing + plating_type)
    """
    drawing = get_object_or_404(Drawing, pk=drawing_id, is_active=True)

    plating_type = _normalize_plating_type(request.GET.get("plating_type"))
    card: Optional[PlatingAreaCard] = None

    if plating_type:
        card, _ = PlatingAreaCard.objects.get_or_create(
            drawing=drawing,
            plating_type=plating_type,
            defaults={"created_by": request.user, "is_active": True},
        )

    context: Dict[str, Any] = {
        "drawing": drawing,
        "plating_types": PLATING_TYPES,
        "plating_type": plating_type,
        "card": card,
        "page_image_url": reverse("drawings:page_image", kwargs={"drawing_id": drawing.id}),
        # NOTE: these endpoints now require plating_type (querystring or payload)
        "zones_json_url": reverse("drawings:zones_json", kwargs={"drawing_id": drawing.id}),
        "save_zone_url": reverse("drawings:save_zone", kwargs={"drawing_id": drawing.id}),
    }
    return render(request, "drawings/annotate.html", context)


@require_GET
@login_required
@user_passes_test(is_engineer)
def zones_json_view(request: HttpRequest, drawing_id: int) -> JsonResponse:
    """
    Engineer zones JSON.
    Requires ?plating_type=<cadmium|chrome|nickel>
    """
    drawing = get_object_or_404(Drawing, pk=drawing_id, is_active=True)

    plating_type = _normalize_plating_type(request.GET.get("plating_type"))
    if not plating_type:
        return JsonResponse(
            {"ok": False, "error": "plating_type is required (cadmium/chrome/nickel)."},
            status=400,
        )

    qs = (
        DrawingZone.objects.filter(drawing=drawing, plating_type=plating_type)
        .order_by("id")
    )
    zones = [_zone_to_dict(z) for z in qs]
    return JsonResponse({"ok": True, "plating_type": plating_type, "zones": zones})


@require_POST
@login_required
@user_passes_test(is_engineer)
def save_zone_view(request: HttpRequest, drawing_id: int) -> JsonResponse:
    """
    Create or update a zone (polygon or rect).
    Single-page: no page_number.

    Requires plating_type in payload (or it will 400).
    Ensures a unique PlatingAreaCard exists for (drawing + plating_type).
    Ensures a PlatingCardZoneSelection exists linking the zone to that card.
    """
    drawing = get_object_or_404(Drawing, pk=drawing_id, is_active=True)

    try:
        payload = _json_payload(request)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    plating_type = _normalize_plating_type(payload.get("plating_type"))
    if not plating_type:
        return JsonResponse(
            {"ok": False, "error": "plating_type is required (cadmium/chrome/nickel)."},
            status=400,
        )

    zone_id = payload.get("id")
    label = (payload.get("label") or "").strip()
    geom_type = str(payload.get("geom_type") or "")
    geometry = payload.get("geometry")
    area_unit = payload.get("area_unit") or "in2"
    is_exclusion_zone = bool(payload.get("is_exclusion_zone", False))
    default_selected = bool(payload.get("default_selected", True))
    notes = payload.get("notes") or ""

    if not label:
        return JsonResponse({"ok": False, "error": "label is required"}, status=400)

    try:
        area_value = Decimal(str(payload.get("area_value")))
        if area_value < 0:
            raise InvalidOperation
    except (InvalidOperation, TypeError):
        return JsonResponse(
            {"ok": False, "error": "area_value must be a number >= 0"},
            status=400,
        )

    geom_error = _validate_normalized_geometry(geom_type, geometry)
    if geom_error:
        return JsonResponse({"ok": False, "error": geom_error}, status=400)

    with transaction.atomic():
        card, _ = PlatingAreaCard.objects.get_or_create(
            drawing=drawing,
            plating_type=plating_type,
            defaults={"created_by": request.user, "is_active": True},
        )

        if zone_id:
            zone = get_object_or_404(
                DrawingZone,
                pk=zone_id,
                drawing=drawing,
                plating_type=plating_type,
            )
        else:
            zone = DrawingZone(
                drawing=drawing,
                plating_type=plating_type,
                created_by=request.user,
            )

        zone.label = label
        zone.geom_type = geom_type
        zone.geometry = geometry
        zone.area_value = area_value
        zone.area_unit = area_unit
        zone.is_exclusion_zone = is_exclusion_zone
        zone.default_selected = default_selected
        zone.notes = notes
        zone.save()

        # Ensure link exists for this card + zone, and default selected state.
        PlatingCardZoneSelection.objects.update_or_create(
            plating_card=card,
            zone=zone,
            defaults={"selected": True},
        )

    return JsonResponse(
        {
            "ok": True,
            "plating_type": plating_type,
            "card_id": card.id,
            "zone": _zone_to_dict(zone),
        }
    )


@require_POST
@login_required
@user_passes_test(is_engineer)
def delete_zone_view(request: HttpRequest, drawing_id: int, zone_id: int) -> JsonResponse:
    """
    Delete a zone for a given drawing.

    Requires ?plating_type=...
    (So we don't accidentally delete a zone from a different plating type.)
    """
    drawing = get_object_or_404(Drawing, pk=drawing_id, is_active=True)

    plating_type = _normalize_plating_type(request.GET.get("plating_type"))
    if not plating_type:
        return JsonResponse(
            {"ok": False, "error": "plating_type is required (cadmium/chrome/nickel)."},
            status=400,
        )

    zone = get_object_or_404(
        DrawingZone,
        pk=zone_id,
        drawing=drawing,
        plating_type=plating_type,
    )
    zone.delete()
    return JsonResponse({"ok": True})


@require_GET
@login_required
@user_passes_test(is_engineer)
def page_image_view(request: HttpRequest, drawing_id: int) -> HttpResponse:
    """
    Render the (single) PDF page to PNG and return it.

    Query params:
      dpi (int) default 150, clamped 72..300
    """
    drawing = get_object_or_404(Drawing, pk=drawing_id, is_active=True)

    pdf_field = getattr(drawing, "pdf_file", None)
    if not pdf_field:
        return JsonResponse(
            {"ok": False, "error": "Drawing has no PDF attached."},
            status=400,
        )

    try:
        dpi = int(request.GET.get("dpi", "150"))
    except ValueError:
        dpi = 150
    dpi = max(72, min(300, dpi))

    pdf_path = Path(pdf_field.path)
    if not pdf_path.exists():
        return JsonResponse(
            {
                "ok": False,
                "error": "PDF file not found on disk.",
                "pdf_path": str(pdf_path),
            },
            status=404,
        )

    try:
        doc = fitz.open(str(pdf_path))
        try:
            if doc.page_count < 1:
                return JsonResponse(
                    {"ok": False, "error": "PDF has no pages."},
                    status=400,
                )
            page = doc.load_page(0)  # single-page behavior
            scale = dpi / 72.0
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            png_bytes = pix.tobytes("png")
        finally:
            doc.close()
    except Exception as exc:
        return JsonResponse({"ok": False, "error": f"Render failed: {exc}"}, status=500)

    return HttpResponse(png_bytes, content_type="image/png")


# -------------------------
# Operators (Card-based)
# -------------------------
@require_GET
@login_required
@user_passes_test(is_operator)
def operator_drawing_list_view(request: HttpRequest) -> HttpResponse:
    """
    Operator landing page:
    - Search drawings
    - (Recommended) show available plating cards per drawing
    """
    q = (request.GET.get("q") or "").strip()

    drawings_qs = Drawing.objects.filter(is_active=True).order_by("drawing_number", "id")
    if q:
        drawings_qs = drawings_qs.filter(
            Q(drawing_number__icontains=q) | Q(title__icontains=q)
        )

    # If your operator_home.html is updated later, you can show cards grouped by drawing.
    cards_qs = (
        PlatingAreaCard.objects.select_related("drawing")
        .filter(is_active=True, drawing__is_active=True)
        .order_by("drawing__drawing_number", "plating_type", "id")
    )

    context = {"query": q, "drawings": drawings_qs, "cards": cards_qs}
    return render(request, "drawings/operator_home.html", context)


@require_GET
@login_required
@user_passes_test(is_operator)
def operator_plating_card_view(request: HttpRequest, card_id: int) -> HttpResponse:
    """
    Operator detail view: Plating Area Card (card-based)
    """
    card = get_object_or_404(
        PlatingAreaCard.objects.select_related("drawing"),
        pk=card_id,
        is_active=True,
        drawing__is_active=True,
    )

    context = {
        **_card_to_context(card),
        "zones_json_url": reverse(
            "drawings:operator_zones_json",
            kwargs={"card_id": card.id},
        ),
        "page_image_url": reverse(
            "drawings:page_image",
            kwargs={"drawing_id": card.drawing_id},
        ),
    }
    return render(request, "drawings/operator_plating_card.html", context)


@require_GET
@login_required
@user_passes_test(is_operator)
def operator_zones_json_view(request: HttpRequest, card_id: int) -> JsonResponse:
    """
    Operator-safe zones JSON (read-only)
    - Returns zones linked to the card (PlatingCardZoneSelection)
    - Includes 'selected' state so the UI can default correctly
    """
    card = get_object_or_404(
        PlatingAreaCard.objects.select_related("drawing"),
        pk=card_id,
        is_active=True,
        drawing__is_active=True,
    )

    selection_qs = (
        PlatingCardZoneSelection.objects.select_related("zone")
        .filter(plating_card=card, zone__drawing=card.drawing, zone__plating_type=card.plating_type)
        .order_by("zone__id")
    )

    zones: list[Dict[str, Any]] = []
    for sel in selection_qs:
        z = sel.zone
        zones.append(
            {
                "id": z.id,
                "label": z.label,
                "geom_type": z.geom_type,
                "geometry": z.geometry,
                "area_value": str(z.area_value),
                "area_unit": z.area_unit,
                "is_exclusion_zone": z.is_exclusion_zone,
                "default_selected": z.default_selected,
                "notes": z.notes or "",
                "selected": bool(sel.selected),
                "plating_type": card.plating_type,
            }
        )

    return JsonResponse(
        {"ok": True, "card_id": card.id, "plating_type": card.plating_type, "zones": zones}
    )

