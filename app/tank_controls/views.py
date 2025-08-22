from typing import Any, Dict

from django.db.models import Prefetch
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import (
    ChemicalSpec,
    ControlSet,
    Tank,
    TemperatureSpec,
    PeriodicTestSpec,
)


def tank_list(request: HttpRequest) -> HttpResponse:
    """
    Read-only list of tanks with their chemical contents and temperature specs.
    Optional filter: ?process=<process name>
    """
    process = request.GET.get("process") or None

    qs = (
        Tank.objects.all()
        .prefetch_related(
            Prefetch(
                "control_sets",
                queryset=ControlSet.objects.all().prefetch_related(
                    Prefetch(
                        "chemical_specs",
                        queryset=ChemicalSpec.objects.all().order_by("chemical_name"),
                    ),
                    Prefetch(
                        "temperature_specs",
                        queryset=TemperatureSpec.objects.all().order_by("frequency"),
                    ),
                ),
            )
        )
        .order_by("name")
    )
    if process:
        qs = qs.filter(process=process)

    context: Dict[str, Any] = {
        "tanks": qs,
        "active_process": process,
    }
    return render(request, "tank_controls/tank_list.html", context)


def tank_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Read-only detail for a single tank with control sets, chemicals,
    temperature specs, and periodic tests (with linked standards).
    """
    periodic_tests_qs = PeriodicTestSpec.objects.prefetch_related(
        # Pull standards linked through the mapping model in `standard` app
        "standard_links__standard",
    ).order_by("name")

    control_sets_qs = ControlSet.objects.prefetch_related(
        Prefetch(
            "chemical_specs",
            queryset=ChemicalSpec.objects.all().order_by("chemical_name"),
        ),
        Prefetch(
            "temperature_specs",
            queryset=TemperatureSpec.objects.all().order_by("frequency"),
        ),
        Prefetch(
            "periodic_tests",
            queryset=periodic_tests_qs,
        ),
    )

    tank = get_object_or_404(
        Tank.objects.prefetch_related(
            Prefetch("control_sets", queryset=control_sets_qs)
        ),
        pk=pk,
    )

    context: Dict[str, Any] = {"tank": tank}
    return render(request, "tank_controls/tank_detail.html", context)
