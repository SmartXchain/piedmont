from django.shortcuts import render, get_object_or_404
from .models import Part, WorkOrder
import tempfile
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML
from process.models import Process, ProcessStep


# 📌 List all parts (Read-Only)
def part_list_view(request):
    parts = Part.objects.all()
    return render(request, 'part/part_list.html', {'parts': parts})


# 📌 View part details (Read-Only)
def part_detail_view(request, part_id):
    part = get_object_or_404(Part, id=part_id)
    standards = part.standards.all()
    work_orders = part.work_orders.all()
    return render(request, 'part/part_detail.html', {'part': part, 'standards': standards, 'work_orders': work_orders})



# 📌 List all work orders (Read-Only)
def work_order_list_view(request):
    work_orders = WorkOrder.objects.all()
    return render(request, 'work_order/work_order_list.html', {'work_orders': work_orders})


# 📌 View work order details (Read-Only)
def work_order_detail_view(request, work_order_id):
    work_order = get_object_or_404(WorkOrder, id=work_order_id)
    process_steps = work_order.get_process_steps()
    return render(request, 'work_order/work_order_detail.html', {'work_order': work_order, 'process_steps': process_steps})


def work_order_print_steps_view(request, work_order_id):
    work_order = get_object_or_404(WorkOrder, id=work_order_id)

    # Fetch the process for the work order based on its standard and classification
    process = Process.objects.filter(
        standard=work_order.standard,
        classification=work_order.classification
    ).first()

    # If no process is found, return an error message
    if not process:
        return HttpResponse("No process steps found for this work order.", content_type="text/plain")

    # Fetch all process steps related to the process
    process_steps = ProcessStep.objects.filter(process=process).order_by('step_number')

    # If no steps are found, return an error message
    if not process_steps.exists():
        return HttpResponse("No process steps found for this work order.", content_type="text/plain")

    current_date = timezone.now().strftime("%m-%d-%Y")

    # Render the template with context
    html_content = render_to_string('work_order/work_order_steps_pdf.html', {
        'work_order': work_order,
        'process_steps': process_steps,
        'current_date': current_date,
        'footer_text': f"Printed on: {current_date}",
    })

    # Generate PDF and return response
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        HTML(string=html_content).write_pdf(temp_file.name)
        temp_file.seek(0)
        pdf_file = temp_file.read()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Work_Order_{work_order.work_order_number}_Steps.pdf"'
    return response