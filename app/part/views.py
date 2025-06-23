from django.shortcuts import render, get_object_or_404
from .models import Part, WorkOrder, PDFSettings
import tempfile
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML
from process.models import Process, ProcessStep
from django.core.paginator import Paginator
from .forms import WorkOrderForm, PartForm, PartStandardForm
from django.shortcuts import redirect
from django.contrib import messages
from standard.models import Classification
from django.db import IntegrityError
from django.db.models import Q


# 📌 List all parts (Read-Only)
def part_list_view(request):
    query = request.GET.get('q', '')
    sort = request.GET.get('sort', 'part_number')  # default sort
    parts = Part.objects.all()

    if query:
        parts = parts.filter(part_number__icontains=query)

    parts = parts.order_by(sort)

    paginator = Paginator(parts, 40)  # Show 20 parts per page
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


def part_create_view(request):
    if request.method == 'POST':
        form = PartForm(request.POST)
        if form.is_valid():
            part_number = form.cleaned_data['part_number']
            part_revision = form.cleaned_data['part_revision']

            # Check if part already exists
            if Part.objects.filter(part_number=part_number, part_revision=part_revision).exists():
                messages.warning(request, "⚠️ This part already exists. Use the Back button to return or check the part list.")
            else:
                part = form.save()
                messages.success(request, "✅ Part created. Now assign a standard to continue.")
                return redirect('part_assign_standard', part_id=part.id)
    else:
        form = PartForm()

    return render(request, 'part/part_form.html', {'form': form})


def part_assign_standard_view(request, part_id):
    part = get_object_or_404(Part, id=part_id)

    if request.method == 'POST':
        form = PartStandardForm(request.POST)
        if form.is_valid():
            standard = form.cleaned_data['standard']
            classification = form.cleaned_data['classification']
            existing = part.standards.filter(standard=standard, classification=classification).first()

            if existing:
                messages.warning(request, "⚠️ This standard/classification is already assigned. Redirecting.")
                return redirect('work_order_create', part_id=part.id)

            part_standard = form.save(commit=False)
            part_standard.part = part
            part_standard.save()
            messages.success(request, "✅ Standard assigned successfully.")
            return redirect('work_order_create', part_id=part.id)
    else:
        form = PartStandardForm()

    if form.data.get('standard'):
        selected_standard_id = form.data.get('standard')
        form.fields['classification'].queryset = Classification.objects.filter(standard_id=selected_standard_id)
    else:
        form.fields['classification'].queryset = Classification.objects.none()

    return render(request, 'part/part_assign_standard_form.html', {'form': form, 'part': part})


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
    assigned_standards = part.standards.all()

    if request.method == 'POST':
        form = WorkOrderForm(request.POST, part=part)
        if form.is_valid():
            work_order = form.save(commit=False)
            work_order.part = part

            # Check for duplicates before save
            existing = WorkOrder.objects.filter(
                part=part,
                work_order_number=work_order.work_order_number,
                standard=work_order.standard,
                classification=work_order.classification,
                surface_repaired=work_order.surface_repaired
            ).first()

            if existing:
                messages.warning(request, "⚠️ This work order already exists. Redirecting.")
                return redirect('work_order_detail', work_order_id=existing.id)

            work_order.save()
            messages.success(request, "✅ Work order saved successfully.")
            return redirect('part_detail', part_id=part.id)
    else:
        initial_data = {}
        if assigned_standards.count() == 1:
            part_standard = assigned_standards.first()
            initial_data = {
                'standard': part_standard.standard,
                'classification': part_standard.classification
            }
        form = WorkOrderForm(part=part, initial=initial_data)

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

    # Calculate amps
    amps = None
    strike_amps = None
    strike_label = None
    time_label = None
    plating_time = None
    normal_plate_amps = None
    normal_label = None

    classification = Classification.objects.filter(
        standard=work_order.standard,
        class_name=work_order.classification.class_name,
        type=work_order.classification.type
    ).first()

    if work_order.surface_area and work_order.current_density:
        if work_order.job_identity == 'chrome_plate':
            amps = work_order.surface_area * work_order.current_density
            # strike amps not calculated for chrome per request
        elif classification and work_order.job_identity == 'cadmium_plate':
            surface_area_ft2 = work_order.surface_area / 144
            amps = surface_area_ft2 * float(classification.plate_asf or 0)
            strike_amps = surface_area_ft2 * float(classification.strike_asf or 0)
            time_label = f"Plating Time ({classification.plating_time_minutes} minutes)" if classification.plating_time_minutes else None
            plating_time = classification.plating_time_minutes
            strike_label = f"Strike Amps ({classification.strike_asf} ASF)" if classification.strike_asf else None
            normal_label = f"Normal Plate Amps ({classification.plate_asf} ASF)" if classification.plate_asf else None
        elif work_order.job_identity == 'ni_plate':
            surface_area_ft2 = work_order.surface_area / 144
            amps = surface_area_ft2 * work_order.current_density
            strike_amps = surface_area_ft2 * 100  # 100 ASF
            strike_label = "Strike Amps (100 ASF)"
        else:
            # fallback if job identity is unknown
            amps = None

    # Optional normal plating amps (50 ASF Ni, 40 ASF Cd)
    if work_order.job_identity == 'ni_plate':
        normal_plate_amps = (work_order.surface_area / 144) * 50
        normal_label = "Normal Plate Amps (50 ASF)"

    job_data = {
        'surface_area': work_order.surface_area,
        'current_density': work_order.current_density,
        'amps': amps,
        'strike_amps': strike_amps,
        'strike_label': strike_label,
        'normal_plate_amps': normal_plate_amps,
        'normal_label': normal_label,
        'time_label': time_label,
        'plating_time': plating_time,
        'is_chrome_or_cadmium_or_nickel': work_order.job_identity in ['chrome_plate', 'cadmium_plate', 'ni_plate'],
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


def standard_classifications_json(request, standard_id):
    classifications = Classification.objects.filter(standard_id=standard_id)
    data = [{"id": c.id, "label": str(c)} for c in classifications]
    return JsonResponse(data, safe=False)
