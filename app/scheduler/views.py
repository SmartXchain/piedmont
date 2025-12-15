# scheduler/views.py
import hashlib
import json
from datetime import timedelta

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, View

from .models import DelayLog, ManufacturingOrder


class SchedulerView(TemplateView):
    """Renders the Gantt chart page."""

    template_name = "scheduler/main.html"


class SchedulerDataView(View):
    """Generates a nested waterfall with a summary bar for parent rows."""

    def get(self, request, *args, **kwargs):
        orders = ManufacturingOrder.objects.select_related("process").all()
        events = []
        resources = []

        for order in orders:
            order_color = self._generate_color(order.work_order)
            parent_id = f"order-{order.id}"

            # 1. Parent Resource Definition
            resources.append({
                "id": parent_id,
                "title": order.work_order,
                "partNumber": order.part_number,
                "status": order.get_status_display(),
                "color": order_color,
                "uiOrder": 0
            })

            steps = (
                order.process.steps.all()
                .select_related("method")
                .order_by("step_number")
            )

            # Waterfall track parameters
            current_pointer = order.planned_start_time
            mo_start_time = order.planned_start_time
            delays = {d.step_number: d.added_minutes for d in order.delays.all()}

            for step in steps:
                method = step.method
                if not method:
                    continue

                child_resource_id = f"step-{order.id}-{step.step_number}"
                resources.append({
                    "id": child_resource_id,
                    "parentId": parent_id,
                    "title": f"Step {step.step_number}: {method.title}",
                    "tank": method.tank_name or "N/A",
                    "uiOrder": step.step_number
                })

                t_max = getattr(method, "touch_time_max", 0) or 0
                r_max = getattr(method, "run_time_max", 0) or 0
                extra = delays.get(step.step_number, 0)
                duration = max(int(t_max) + int(r_max), 1) + extra

                end_pointer = current_pointer + timedelta(minutes=duration)

                # Individual Step Event
                events.append({
                    "id": f"evt-{order.id}-{step.step_number}",
                    "resourceId": child_resource_id,
                    "start": current_pointer.isoformat(),
                    "end": end_pointer.isoformat(),
                    "title": f"{method.title}",
                    "backgroundColor": order_color,
                    "extendedProps": {
                        "isSummary": False,
                        "orderId": order.id,
                        "stepNumber": step.step_number,
                        "isDelayed": extra > 0,
                        "details": f"Step {step.step_number}: {method.title}"
                    }
                })
                current_pointer = end_pointer

            # 2. Add the Summary Event (visible on the parent row)
            if steps.exists():
                events.append({
                    "id": f"summary-{order.id}",
                    "resourceId": parent_id,
                    "start": mo_start_time.isoformat(),
                    "end": current_pointer.isoformat(),
                    "title": f"Total Order: {order.work_order}",
                    "display": "block",
                    "backgroundColor": order_color,
                    "opacity": "0.6",  # Make it look like a summary
                    "extendedProps": {
                        "isSummary": True,
                        "details": f"Work Order: {order.work_order}\nTotal Duration"
                    }
                })

        return JsonResponse({"events": events, "resources": resources})

    def _generate_color(self, text):
        hash_obj = hashlib.md5(text.encode())
        return f"#{hash_obj.hexdigest()[:6]}"


@method_decorator(csrf_exempt, name='dispatch')
class AddDelayView(View):
    """Endpoint to record a delay and the mandatory reason."""

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        try:
            order = ManufacturingOrder.objects.get(id=data['orderId'])
            delay, _ = DelayLog.objects.get_or_create(
                order=order,
                step_number=data['stepNumber'],
                defaults={'added_minutes': 0, 'reason': ''}
            )
            delay.added_minutes += int(data['minutes'])
            delay.reason += f"\n[{data['minutes']}m]: {data['reason']}"
            delay.save()
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

