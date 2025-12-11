# scheduler/views.py
from datetime import datetime, timedelta
import json

from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import ManufacturingOrder, Operation, Resource


def schedule_dashboard(request):
    """
    Landing page:
      - Overview table of all manufacturing orders
      - Time-based chart of all operations below (Plotly on frontend).
    """
    orders = (
        ManufacturingOrder.objects
        .select_related("process", "assigned_to")
        .order_by("due_date", "work_order")
    )

    departments = (
        Resource.objects
        .exclude(department="")
        .values_list("department", flat=True)
        .distinct()
        .order_by("department")
    )

    context = {
        "orders": orders,
        "departments": departments,
    }
    return render(request, "scheduler/dashboard.html", context)


def gantt_data(request):
    """
    JSON data for the main schedule chart.

    Optional filters (GET params):
      - start: YYYY-MM-DD
      - end:   YYYY-MM-DD
      - department: resource.department
      - hide_completed: "1" to exclude completed ops
      - hide_cancelled: "1" to exclude cancelled ops
    """
    ops = (
        Operation.objects
        .select_related("manufacturing_order", "resource")
        .order_by("planned_start")
    )

    start_str = request.GET.get("start")
    end_str = request.GET.get("end")
    department = request.GET.get("department")
    hide_completed = request.GET.get("hide_completed") == "1"
    hide_cancelled = request.GET.get("hide_cancelled") == "1"

    if start_str:
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            ops = ops.filter(planned_end__date__gte=start_date)
        except ValueError:
            start_date = None

    if end_str:
        try:
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
            ops = ops.filter(planned_start__date__lte=end_date)
        except ValueError:
            end_date = None

    if department:
        ops = ops.filter(resource__department=department)

    if hide_completed:
        ops = ops.exclude(status="completed")

    if hide_cancelled:
        ops = ops.exclude(status="cancelled")

    data = []
    for op in ops:
        order = op.manufacturing_order
        data.append(
            {
                "id": op.id,
                "sequence": op.sequence,
                "order_id": order.id,
                "work_order": order.work_order,
                "part_number": order.part_number,
                "status": op.status,
                "resource": op.resource.name if op.resource else "",
                "start": op.planned_start.isoformat(),
                "end": op.planned_end.isoformat(),
            }
        )

    return JsonResponse(data, safe=False)


def order_detail(request, pk):
    """
    Detail view for a single ManufacturingOrder, including a Plotly timeline.
    """
    order = get_object_or_404(
        ManufacturingOrder.objects.select_related("process", "assigned_to"),
        pk=pk,
    )
    return render(request, "scheduler/order_detail.html", {"order": order})


def order_gantt_data(request, pk):
    """
    JSON data for a single work order's operations, used by Plotly timeline.
    """
    order = get_object_or_404(ManufacturingOrder, pk=pk)
    ops = (
        Operation.objects
        .filter(manufacturing_order=order)
        .select_related("resource")
        .order_by("planned_start")
    )

    data = []
    for op in ops:
        data.append(
            {
                "id": op.id,
                "sequence": op.sequence,
                "name": f"Op {op.sequence} – {op.process_step}",
                "status": op.status,
                "resource": op.resource.name if op.resource else "",
                "start": op.planned_start.isoformat(),
                "end": op.planned_end.isoformat(),
            }
        )

    return JsonResponse(data, safe=False)


@require_POST
def operation_reschedule(request, pk):
    """
    Update planned_start/planned_end for a single operation.
    Expects JSON body:
      { "start": iso8601, "end": iso8601 }
    """
    op = get_object_or_404(Operation, pk=pk)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        start_str = payload.get("start")
        end_str = payload.get("end")
        if not start_str or not end_str:
            return HttpResponseBadRequest("Missing start or end")

        start_dt = datetime.fromisoformat(start_str)
        end_dt = datetime.fromisoformat(end_str)

        if timezone.is_naive(start_dt):
            start_dt = timezone.make_aware(start_dt)
        if timezone.is_naive(end_dt):
            end_dt = timezone.make_aware(end_dt)

        op.planned_start = start_dt
        op.planned_end = end_dt
        op.save(update_fields=["planned_start", "planned_end"])

        return JsonResponse({"status": "ok"})
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        return HttpResponseBadRequest(str(exc))


@require_POST
def order_shift(request, pk):
    """
    Shift all operations for a ManufacturingOrder by a delta in minutes.

    Expects JSON body:
      { "delta_minutes": 120 }
    """
    order = get_object_or_404(ManufacturingOrder, pk=pk)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        delta_minutes = int(payload.get("delta_minutes", 0))
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        return HttpResponseBadRequest(f"Invalid delta_minutes: {exc}")

    if delta_minutes == 0:
        return JsonResponse({"status": "no_change"})

    delta = timedelta(minutes=delta_minutes)

    ops = (
        Operation.objects
        .filter(manufacturing_order=order)
        .order_by("planned_start")
    )

    for op in ops:
        op.planned_start += delta
        op.planned_end += delta
        op.save(update_fields=["planned_start", "planned_end"])

    last = ops.last()
    if last:
        order.estimated_finish_date = last.planned_end.date()
        order.save(update_fields=["estimated_finish_date"])

    return JsonResponse({"status": "ok"})

