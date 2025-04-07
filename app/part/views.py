from django.shortcuts import render, get_object_or_404
from .models import Part, WorkOrder, PDFSettings
import tempfile
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML
from process.models import Process, ProcessStep
from django.core.paginator import Paginator
from .forms import WorkOrderForm
from django.shortcuts import redirect


# 📌 List all parts (Read-Only)
def part_list_view(request):
    query = request.GET.get('q', '')
    sort = request.GET.get('sort', 'part_number')  # default sort
    parts = Part.objects.all()

    if query:
        parts = parts.filter(part_number__icontains=query)

    parts = parts.order_by(sort)

    paginator = Paginator(parts, 20)  # Show 20 parts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'sort': sort,
    }
    return render(request, 'part/part_list.html', context)


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


def work_order_create_view(request, part_id):
    part = get_object_or_404(Part, id=part_id)

    if request.method == 'POST':
        form = WorkOrderForm(request.POST, part=part)
        if form.is_valid():
            work_order = form.save(commit=False)
            work_order.part = part
            work_order.save()
            return redirect('part_detail', part_id=part.id)
    else:
        form = WorkOrderForm(part=part)

    return render(request, 'work_order/work_order_form.html', {
        'form': form,
        'part': part
    })


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

    # Fetch the latest footer settings (or use defaults)
    pdf_settings = PDFSettings.objects.first()

    amps = None
    if work_order.surface_area and work_order.current_density:
        if work_order.job_identity == 'chrome_plate':
            amps = work_order.surface_area * work_order.current_density
        elif work_order.job_identity == 'cadmium_plate':
            amps = (work_order.surface_area / 144) * work_order.current_density

    job_data = {
        'surface_area': work_order.surface_area,
        'current_density': work_order.current_density,
        'amps': amps,
        'is_chrome_or_cadmium': work_order.job_identity in ['chrome_plate', 'cadmium_plate'],
        'is_chrome_plate': work_order.job_identity == 'chrome_plate',
        'instructions': ["Record amp, current density, Dim Thickness Started and Dim Thickness Finish"]
    }

    inspections = work_order.standard.inspections.all() if hasattr(work_order.standard, 'inspections') else []
    print(inspections)

    bake_labels = [
        "Date and Time of Start of Baking",
        "Date and Time of Start of Soak",
        "Date and Time of Completion of Baking",
        "Furnace Control Instrument Set Temperature",
        "Furnace Identification",
        "Graph Number"
    ]

    context = {
        'work_order': work_order,
        'process_steps': process_steps,
        'current_date': current_date,
        'doc_id': pdf_settings.doc_id if pdf_settings else 'CPTS',
        'revision': pdf_settings.revision if pdf_settings else '0',
        'date': pdf_settings.date.strftime('%m-%d-%Y') if pdf_settings else current_date,
        'repair_station': pdf_settings.repair_station if pdf_settings else 'QKPR504X',
        'footer_text': pdf_settings.footer_text if pdf_settings else f"Printed on: {current_date}",
        'job_data': job_data,
        'inspections': inspections,
        'bake_labels': bake_labels,
    }

    # Render the template with context
    html_content = render_to_string('work_order/work_order_steps_pdf.html', context)

    # Generate PDF and return response
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        HTML(string=html_content).write_pdf(temp_file.name)
        temp_file.seek(0)
        pdf_file = temp_file.read()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Work_Order_{work_order.work_order_number}_Steps.pdf"'
    return response
