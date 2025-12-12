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
    template_name = "scheduler/main.html"


class SchedulerDataView(View):
    """Generates a nested waterfall: Work Order > Individual Steps."""

    def get(self, request, *args, **kwargs):
        orders = ManufacturingOrder.objects.select_related("process").all()
        events = []
        resources = []

        for order in orders:
            order_color = self._generate_color(order.work_order)

            # 1. Parent Resource: The Work Order Folder
            resources.append({
                "id": f"order-{order.id}",
                "title": order.work_order,
                "partNumber": order.part_number,
                "status": order.get_status_display(),
                "color": order_color,
            })

            steps = (
                order.process.steps.all()
                .select_related("method")
                .order_by("step_number")
            )
            
            current_pointer = order.planned_start_time
            delays = {d.step_number: d.added_minutes for d in order.delays.all()}

            for step in steps:
                method = step.method
                if not method:
                    continue

                # 2. Child Resource: The specific step row under the order
                child_resource_id = f"step-{order.id}-{step.step_number}"
                resources.append({
                    "id": child_resource_id,
                    "parentId": f"order-{order.id}",
                    "title": f"Step {step.step_number}: {method.title}",
                    "tank": method.tank_name or "N/A",
                })

                # Calculate times
                t_max = getattr(method, "touch_time_max", 0) or 0
                r_max = getattr(method, "run_time_max", 0) or 0
                extra = delays.get(step.step_number, 0)
                duration = max(int(t_max) + int(r_max), 1) + extra
                
                end_pointer = current_pointer + timedelta(minutes=duration)

                # 3. Create the Event on the Child Resource Row
                events.append({
                    "id": f"evt-{order.id}-{step.step_number}",
                    "resourceId": child_resource_id,
                    "start": current_pointer.isoformat(),
                    "end": end_pointer.isoformat(),
                    "title": f"{method.title}",
                    "backgroundColor": order_color,
                    "extendedProps": {
                        "orderId": order.id,
                        "stepNumber": step.step_number,
                        "tank": method.tank_name,
                        "isDelayed": extra > 0,
                        "details": (
                            f"Process: {method.title}\n"
                            f"Tank: {method.tank_name}\n"
                            f"Duration: {duration} min"
                        )
                    }
                })
                # Ripple effect
                current_pointer = end_pointer

        return JsonResponse({"events": events, "resources": resources})

    def _generate_color(self, text):
        hash_obj = hashlib.md5(text.encode())
        return f"#{hash_obj.hexdigest()[:6]}"


@method_decorator(csrf_exempt, name='dispatch')
class AddDelayView(View):
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
