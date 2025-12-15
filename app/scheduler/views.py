# scheduler/views.py
import hashlib
import json
from datetime import timedelta
from typing import Any, Dict, List

from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, View

from .models import DelayLog, ManufacturingOrder


class SchedulerView(TemplateView):
    """Renders the scheduler page."""
    template_name = "scheduler/main.html"


class SchedulerDataView(View):
    """Builds FullCalendar Scheduler resources/events (waterfall) for each MO."""

    STATUS_COLORS = {
        "planned": None,           # uses hashed color per WO
        "in_progress": "#0d6efd",  # blue
        "hold": "#ffc107",         # yellow
        "done": "#dc3545",         # red
    }

    def get(self, request, *args, **kwargs) -> JsonResponse:
        orders = ManufacturingOrder.objects.select_related("process").all()

        events: List[Dict[str, Any]] = []
        resources: List[Dict[str, Any]] = []

        for order in orders:
            base_color = self._generate_color(order.work_order)
            status_override = self.STATUS_COLORS.get(order.status)
            order_color = status_override or base_color
            is_done = order.status == "done"

            parent_id = f"order-{order.id}"

            resources.append(
                {
                    "id": parent_id,
                    "title": f"{order.work_order} #{order.occurrence}",
                    "partNumber": order.part_number,
                    "status": order.get_status_display(),
                    "color": order_color,
                    "uiOrder": 0,
                }
            )

            steps_qs = (
                order.process.steps.all()
                .select_related("method")
                .order_by("step_number")
            )

            current_pointer = order.planned_start_time
            mo_start_time = order.planned_start_time

            delays: Dict[int, int] = {}
            for delay in order.delays.all():
                step_no = int(delay.step_number)
                delays[step_no] = delays.get(step_no, 0) + int(delay.added_minutes or 0)

            for step in steps_qs:
                method = step.method
                if not method:
                    continue

                child_resource_id = f"step-{order.id}-{step.step_number}"

                resources.append(
                    {
                        "id": child_resource_id,
                        "parentId": parent_id,
                        "title": f"Step {step.step_number}: {method.title}",
                        "tank": getattr(method, "tank_name", None) or "N/A",
                        "uiOrder": step.step_number,
                    }
                )

                t_max = int(getattr(method, "touch_time_max", 0) or 0)
                r_max = int(getattr(method, "run_time_max", 0) or 0)
                extra = int(delays.get(step.step_number, 0) or 0)

                duration = max(t_max + r_max, 1) + extra
                end_pointer = current_pointer + timedelta(minutes=duration)

                events.append(
                    {
                        "id": f"evt-{order.id}-{step.step_number}",
                        "resourceId": child_resource_id,
                        "start": current_pointer.isoformat(),
                        "end": end_pointer.isoformat(),
                        "title": method.title,
                        "backgroundColor": order_color,
                        "extendedProps": {
                            "isSummary": False,
                            "orderId": order.id,
                            "stepNumber": step.step_number,
                            "isDelayed": extra > 0,
                            "isCompleted": is_done,
                            "status": order.status,
                            "details": (
                                f"WO: {order.work_order}\n"
                                f"Step {step.step_number}: {method.title}\n"
                                f"Status: {order.get_status_display()}"
                            ),
                        },
                    }
                )

                current_pointer = end_pointer

            if steps_qs.exists():
                events.append(
                    {
                        "id": f"summary-{order.id}",
                        "resourceId": parent_id,
                        "start": mo_start_time.isoformat(),
                        "end": current_pointer.isoformat(),
                        "title": "Completed"
                        if is_done
                        else f"Total Order: {order.work_order}",
                        "display": "block",
                        "backgroundColor": order_color,
                        "extendedProps": {
                            "isSummary": True,
                            "orderId": order.id,
                            "isCompleted": is_done,
                            "status": order.status,
                            "details": (
                                f"WO: {order.work_order}\n"
                                f"Status: {order.get_status_display()}"
                            ),
                        },
                    }
                )

        return JsonResponse({"events": events, "resources": resources})

    @staticmethod
    def _generate_color(text: str) -> str:
        hash_obj = hashlib.md5(text.encode())
        return f"#{hash_obj.hexdigest()[:6]}"


@method_decorator(csrf_exempt, name="dispatch")
class AddDelayView(View):
    """Adds delay minutes and appends a mandatory reason to the DelayLog."""

    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            data = json.loads(request.body or "{}")
            order_id = data.get("orderId")
            step_number = data.get("stepNumber")
            minutes = int(data.get("minutes", 0))
            reason = (data.get("reason") or "").strip()

            if not order_id or step_number is None:
                return JsonResponse(
                    {"status": "error", "message": "Missing orderId or stepNumber"},
                    status=400,
                )
            if minutes <= 0:
                return JsonResponse(
                    {"status": "error", "message": "Minutes must be > 0"},
                    status=400,
                )
            if not reason:
                return JsonResponse(
                    {"status": "error", "message": "Reason is required"},
                    status=400,
                )

            order = ManufacturingOrder.objects.get(id=order_id)

            if order.status == "done":
                return JsonResponse(
                    {"status": "error", "message": "Order is completed (read-only)."},
                    status=400,
                )

            delay, _ = DelayLog.objects.get_or_create(
                order=order,
                step_number=int(step_number),
                defaults={"added_minutes": 0, "reason": ""},
            )

            delay.added_minutes = int(delay.added_minutes or 0) + minutes
            delay.reason = (delay.reason or "") + f"\n[{minutes}m] {reason}"
            delay.save()

            return JsonResponse({"status": "success"})

        except ManufacturingOrder.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Order not found"},
                status=404,
            )
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            return JsonResponse(
                {"status": "error", "message": f"Bad request: {exc}"},
                status=400,
            )
        except Exception as exc:
            return JsonResponse(
                {"status": "error", "message": str(exc)},
                status=400,
            )


@method_decorator(csrf_exempt, name="dispatch")
class UpdateStatusView(View):
    """Updates order status via UI (right-click menu)."""

    ALLOWED = {"planned", "in_progress", "hold", "done"}

    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            data = json.loads(request.body or "{}")
            order_id = data.get("orderId")
            new_status = data.get("status")

            if not order_id or not new_status:
                return JsonResponse(
                    {"status": "error", "message": "Missing orderId or status"},
                    status=400,
                )
            if new_status not in self.ALLOWED:
                return JsonResponse(
                    {"status": "error", "message": "Invalid status"},
                    status=400,
                )

            order = ManufacturingOrder.objects.get(id=order_id)
            order.status = new_status

            if new_status == "done":
                order.completed_at = timezone.now()
            else:
                order.completed_at = None

            order.save(update_fields=["status", "completed_at", "updated_at"])
            return JsonResponse({"status": "success"})

        except ManufacturingOrder.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Order not found"},
                status=404,
            )
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            return JsonResponse(
                {"status": "error", "message": f"Bad request: {exc}"},
                status=400,
            )
        except Exception as exc:
            return JsonResponse(
                {"status": "error", "message": str(exc)},
                status=400,
            )

