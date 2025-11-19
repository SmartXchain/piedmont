from django.shortcuts import render, get_object_or_404
from .models import Part, WorkOrder, PDFSettings, PartStandard
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
from methods.models import ParameterToBeRecorded
from django.db.models import Prefetch, Count


# 📌 List all parts (Read-Only)
def part_list_view(request):
    query = request.GET.get('q', '')
    sort = request.GET.get('sort', 'part_number')

    parts = Part.objects.all()

    parts = parts.annotate(
        standards_count=Count('standards')
    ).prefetch_related(
        Prefetch(
            'standards',
            queryset=PartStandard.objects.select_related('standard').order_by('pk'),
            to_attr='prefetched_standards'
        )
    )

    if query:
        parts = parts.filter(part_number__icontains=query)

    parts = parts.order_by(sort)

    paginator = Paginator(parts, 40)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,
        'sort': sort,
    }
    return render(request, 'part/part_list.html', context)


# part/views.py (in part_detail_view)
def part_detail_view(request, part_id):
    # Fetch the Part
    part = get_object_or_404(Part, id=part_id)
    
    # EFFICIENT QUERY 1: Fetch standards and prefetch the linked Standard and Classification models
    # This avoids N+1 for the Standards Assignment Card
    standards = part.standards.select_related('standard', 'classification')
    
    # EFFICIENT QUERY 2: Fetch work orders and prefetch the linked Standard and Classification models
    # This avoids N+1 for the Work Orders Table
    work_orders = part.work_orders.select_related('standard', 'classification')
    
    context = {
        'part': part, 
        'standards': standards, 
        'work_orders': work_orders
    }
    return render(request, 'part/part_detail.html', context)


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

# part/views.py (in work_order_detail_view)

def work_order_detail_view(request, work_order_id):
    # Fetch work order and related FKs (Part, Standard, Classification) in one go
    work_order = get_object_or_404(
        WorkOrder.objects.select_related('part', 'standard', 'classification'), 
        id=work_order_id
    )
    
    # Use the method from the WorkOrder model to find and fetch the steps
    # We must explicitly use select_related('method') inside get_process_steps() 
    # or chain it here for efficiency.
    # Assuming get_process_steps() returns a ProcessStep QuerySet:
    process_steps_qs = work_order.get_process_steps()
    
    # Ensure the query set includes select_related('method') if it doesn't already.
    # If the method returns a QuerySet, we can chain:
    process_steps = process_steps_qs.select_related('method') if process_steps_qs else []
    
    # Check the actual type returned by get_process_steps. If it returns steps.all(),
    # then the view is correct, but let's confirm the efficiency in the view itself.

    # NOTE: The definition of work_order.get_process_steps() is in your models.py.
    # It must look like this to be efficient:
    # return process.steps.select_related('method') if process else []
    
    # Assuming the underlying logic in get_process_steps is fixed:
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

    # Define flags based on work order requirements
    requires_masking = work_order.requires_masking
    requires_stress_relief = work_order.requires_stress_relief
    requires_hydrogen_relief = work_order.requires_hydrogen_relief

    # Build the filter/exclusion logic
    exclusion_query = Q()

    # If masking is NOT required, exclude masking steps
    if not requires_masking:
        exclusion_query |= Q(method__is_masking_operation=True)

    # If stress relief is NOT required, exclude stress relief steps
    if not requires_stress_relief:
        exclusion_query |= Q(method__is_stress_relief_operation=True)

    # If hydrogen relief is NOT required, exclude H.E.R. steps
    if not requires_hydrogen_relief:
        exclusion_query |= Q(method__is_hydrogen_relief_operation=True)

    # Fetch all process steps related to the process
    process_steps = (
        ProcessStep.objects
        .filter(process=process)
        .exclude(exclusion_query)
        .select_related('method')
        .prefetch_related(
            Prefetch(
                'method__recorded_parameters',
                queryset=ParameterToBeRecorded.objects.order_by('id'),
                to_attr='prefetched_recorded_parameters',
            )
        )
        .order_by('step_number')
    )

    # If no steps are found, return an error message
    if not process_steps.exists():
        return HttpResponse("No process steps found for this work order.", content_type="text/plain")

    current_date = timezone.now().strftime("%m-%d-%Y")

    # Fetch the latest footer settings (or use defaults)
    pdf_settings = PDFSettings.objects.first()

    # ----------------------------------------------------------------------------
    # Calculate amps (only from data we actually have)
    # ----------------------------------------------------------------------------
    amps = None
    strike_amps = None
    strike_label = None
    time_label = None
    plating_time = ""
    normal_plate_amps = None
    normal_label = None

    classification = work_order.classification

    # we'll reuse this in a couple places
    surface_area_in2 = work_order.surface_area
    surface_area_ft2 = None
    if surface_area_in2:
        surface_area_ft2 = float(surface_area_in2) / 144.0

    # plating / rectified jobs that use ASF from classification
    if classification and surface_area_ft2 and work_order.job_identity in ('cadmium_plate', 'ni_plate', 'chrome_plate'):

        plate_asf = getattr(classification, 'plate_asf', None)
        strike_asf = getattr(classification, 'strike_asf', None)
        plating_time_minutes = getattr(classification, 'plating_time_minutes', None)

        # common labels
        if plating_time_minutes:
            time_label = f"Plating Time ({plating_time_minutes} minutes)"
            plating_time = plating_time_minutes

        # cad / ni: use plate_asf and maybe strike_asf
        if work_order.job_identity in ('cadmium_plate', 'ni_plate', 'chrome_plate'):
            if plate_asf:
                normal_plate_amps = surface_area_ft2 * float(plate_asf)
                normal_label = f"Normal Plate Amps / Part ({plate_asf} ASF)"
                amps = normal_plate_amps  # main amps value

            if strike_asf:
                strike_amps = surface_area_ft2 * float(strike_asf)
                strike_label = f"Strike Amps / Part ({strike_asf} ASF)"

    # build job_data so the template doesn't explode
    job_data = {
        'surface_area': surface_area_in2,
        # we no longer have work_order.current_density, so just give None
        'current_density': None,
        'amps': amps,
        'strike_amps': strike_amps,
        'strike_label': strike_label,
        'normal_plate_amps': normal_plate_amps,
        'normal_label': normal_label,
        'time_label': time_label,
        'plating_time': plating_time,
        'is_chrome_or_cadmium_or_nickel': work_order.job_identity in ['chrome_plate', 'cadmium_plate', 'ni_plate'],
        'is_chrome_plate': work_order.job_identity == 'chrome_plate',
        'instructions': ["Record amps, ramp as required, record thickness start/finish"],
    }

    inspections_qs = getattr(work_order.standard, 'inspections', None)
    inspections = inspections_qs.all() if inspections_qs else []
    
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
