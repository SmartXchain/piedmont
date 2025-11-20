from django.shortcuts import render, get_object_or_404, redirect
from .models import Part, WorkOrder, PDFSettings, PartStandard
import tempfile
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML
from process.models import Process, ProcessStep
from django.core.paginator import Paginator
from .forms import WorkOrderForm, PartForm, PartStandardForm
from django.contrib import messages
from standard.models import Classification
from django.db import IntegrityError
from django.db.models import Q, Prefetch, Count
from methods.models import ParameterToBeRecorded
from django.db import transaction # Needed for AJAX handler

# ----------------------------------------------------------------------
# PART MANAGEMENT VIEWS
# ----------------------------------------------------------------------

# 📌 List all parts (Read-Only)
def part_list_view(request):
    query = request.GET.get('q', '')
    sort = request.GET.get('sort', 'part_number')

    parts = Part.objects.all()

    # Efficiently fetch count and first related standard for the list view
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


# 📌 View part details (Read-Only)
def part_detail_view(request, part_id):
    # Fetch the Part
    part = get_object_or_404(Part, id=part_id)
    
    # EFFICIENT QUERY 1: Fetch standards and prefetch the linked Standard and Classification models
    standards = part.standards.select_related('standard', 'classification')
    
    # EFFICIENT QUERY 2: Fetch work orders and prefetch the linked Standard and Classification models
    work_orders = part.work_orders.select_related('standard', 'classification')
    
    context = {
        'part': part,
        'standards': standards,
        'work_orders': work_orders
    }
    return render(request, 'part/part_detail.html', context)


# 📌 Create part
def part_create_view(request):
    if request.method == 'POST':
        form = PartForm(request.POST)
        if form.is_valid():
            part_number = form.cleaned_data['part_number']
            part_revision = form.cleaned_data['part_revision']

            # Check if part already exists (redundant if constraint exists, but keeps UX clean)
            if Part.objects.filter(part_number=part_number, part_revision=part_revision).exists():
                messages.warning(request, "⚠️ This part already exists. Use the Back button to return or check the part list.")
            else:
                part = form.save()
                messages.success(request, "✅ Part created. Now assign a standard to continue.")
                return redirect('part_assign_standard', part_id=part.id)
    else:
        form = PartForm()

    return render(request, 'part/part_form.html', {'form': form})


# 📌 Assign standard to part
def part_assign_standard_view(request, part_id):
    part = get_object_or_404(Part, id=part_id)

    if request.method == 'POST':
        form = PartStandardForm(request.POST)
        if form.is_valid():
            standard = form.cleaned_data['standard']
            classification = form.cleaned_data['classification']
            
            # Use Part.standards manager to check for existence
            existing = part.standards.filter(standard=standard, classification=classification).first()

            if existing:
                messages.warning(request, "⚠️ This standard/classification is already assigned. Redirecting.")
                return redirect('work_order_create', part_id=part.id)

            part_standard = form.save(commit=False)
            part_standard.part = part
            
            try:
                part_standard.save()
                messages.success(request, "✅ Standard assigned successfully.")
                return redirect('work_order_create', part_id=part.id)
            except IntegrityError:
                 # Catch database constraint violation if the form check was bypassed (e.g., race condition)
                 messages.error(request, "A duplicate entry was blocked by the database constraint.")
                 # Fall through to re-render form

    else:
        form = PartStandardForm()

    # Logic to filter Classification queryset on GET or form error re-render
    if form.data.get('standard'):
        selected_standard_id = form.data.get('standard')
        form.fields['classification'].queryset = Classification.objects.filter(standard_id=selected_standard_id)
    else:
        form.fields['classification'].queryset = Classification.objects.none()

    return render(request, 'part/part_assign_standard_form.html', {'form': form, 'part': part})


# ----------------------------------------------------------------------
# WORK ORDER (TRACKED) VIEWS
# ----------------------------------------------------------------------

# 📌 View work order details (Read-Only) + AJAX Toggle Handler
def work_order_detail_view(request, work_order_id):
    work_order = get_object_or_404(
        WorkOrder.objects.select_related('part', 'standard', 'classification'), 
        id=work_order_id
    )

    # --- AJAX POST Handler for Toggling ---
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        
        field_name = request.POST.get('field_name')
        new_value_str = request.POST.get('new_value')
        
        allowed_fields = [
            'requires_masking', 'requires_stress_relief', 'requires_hydrogen_relief'
        ]

        if field_name not in allowed_fields:
            return JsonResponse({'success': False, 'error': 'Invalid field.'}, status=400)

        try:
            # Convert 'True'/'False' strings to actual booleans
            new_value = True if new_value_str == 'True' else False
            
            with transaction.atomic():
                setattr(work_order, field_name, new_value)
                # Use update_fields for efficiency
                work_order.save(update_fields=[field_name, 'date']) # Add date to update_fields if date represents last modification
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    # --- Standard GET Request ---
    
    # Assuming work_order.get_process_steps() is optimized in models.py to fetch Method
    process_steps = work_order.get_process_steps() 

    context = {
        'work_order': work_order, 
        'process_steps': process_steps
    }
    return render(request, 'work_order/work_order_detail.html', context)


# 📌 Create work order
def work_order_create_view(request, part_id):
    part = get_object_or_404(Part, id=part_id)
    assigned_standards = part.standards.all()

    if request.method == 'POST':
        form = WorkOrderForm(request.POST, part=part)
        if form.is_valid():
            work_order = form.save(commit=False)
            work_order.part = part

            # Check for duplicates before save (uses models.py constraint fields)
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
        # Set initial values if only one standard is assigned
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


# 📌 Print work order steps PDF
def work_order_print_steps_view(request, work_order_id):
    work_order = get_object_or_404(WorkOrder, id=work_order_id)

    # Fetch the process for the work order
    process = Process.objects.filter(
        standard=work_order.standard,
        classification=work_order.classification
    ).first()

    if not process:
        return HttpResponse("No process steps found for this work order.", content_type="text/plain")

    # Define exclusion logic based on WorkOrder toggles
    exclusion_query = Q()

    if not work_order.requires_masking:
        exclusion_query |= Q(method__is_masking_operation=True)
    if not work_order.requires_stress_relief:
        exclusion_query |= Q(method__is_stress_relief_operation=True)
    if not work_order.requires_hydrogen_relief:
        exclusion_query |= Q(method__is_hydrogen_relief_operation=True)

    # Fetch all process steps, applying exclusion filter and prefetching data
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

    if not process_steps.exists():
        return HttpResponse("No process steps found for this work order.", content_type="text/plain")

    current_date = timezone.now().strftime("%m-%d-%Y")
    pdf_settings = PDFSettings.objects.first()
    classification = work_order.classification

    # --- Calculation Logic ---
    amps, strike_amps, normal_plate_amps, strike_label, normal_label = [None] * 5
    time_label, plating_time = [None] * 2
    
    surface_area_in2 = work_order.surface_area
    surface_area_ft2 = float(surface_area_in2) / 144.0 if surface_area_in2 else None
    
    if classification and surface_area_ft2 and work_order.job_identity in ('cadmium_plate', 'ni_plate', 'chrome_plate'):

        plate_asf = getattr(classification, 'plate_asf', None)
        strike_asf = getattr(classification, 'strike_asf', None)
        plating_time_minutes = getattr(classification, 'plating_time_minutes', None)

        if plating_time_minutes:
            time_label = f"Plating Time ({plating_time_minutes} minutes)"
            plating_time = plating_time_minutes

        if plate_asf:
            normal_plate_amps = surface_area_ft2 * float(plate_asf)
            normal_label = f"Normal Plate Amps / Part ({plate_asf} ASF)"
            amps = normal_plate_amps

        if strike_asf:
            strike_amps = surface_area_ft2 * float(strike_asf)
            strike_label = f"Strike Amps / Part ({strike_asf} ASF)"

    # Build context data
    job_data = {
        'surface_area': surface_area_in2,
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
        "Date and Time of Start of Baking", "Date and Time of Start of Soak", "Date and Time of Completion of Baking", 
        "Furnace Control Instrument Set Temperature", "Furnace Identification", "Graph Number"
    ]

    context = {
        'work_order': work_order, 'process_steps': process_steps, 'current_date': current_date,
        'doc_id': pdf_settings.doc_id if pdf_settings else 'CPTS',
        'revision': pdf_settings.revision if pdf_settings else '0',
        'date': pdf_settings.date.strftime('%m-%d-%Y') if pdf_settings else current_date,
        'repair_station': pdf_settings.repair_station if pdf_settings else 'QKPR504X',
        'footer_text': pdf_settings.footer_text if pdf_settings else f"Printed on: {current_date}",
        'job_data': job_data, 'inspections': inspections, 'bake_labels': bake_labels,
    }

    # Render and Generate PDF
    html_content = render_to_string('work_order/work_order_steps_pdf.html', context)

    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        HTML(string=html_content).write_pdf(temp_file.name)
        temp_file.seek(0)
        pdf_file = temp_file.read()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Work_Order_{work_order.work_order_number}_Steps.pdf"'
    return response


# ----------------------------------------------------------------------
# TEMPLATE (UNTRACKED) VIEWS
# ----------------------------------------------------------------------

# 📌 1. List all Processes marked as templates
def global_template_list_view(request):
    """Lists all Process objects where is_template=True."""
    
    templates = Process.objects.filter(is_template=True).select_related(
        'standard',
        'classification'
    ).order_by('standard__name', 'classification')

    context = {
        'templates': templates
    }
    return render(request, 'part/global_template_list.html', context)


# 📌 2. View to set masking toggle before final print
def template_selection_view(request, process_id):
    # Fetch the Process and prefetch its steps for review.
    process = get_object_or_404(
        Process.objects
            .select_related('standard', 'classification')
            .prefetch_related(
                Prefetch(
                    'steps',
                    queryset=ProcessStep.objects.select_related('method').order_by('step_number'),
                    to_attr='prefetched_steps'
                )
            ),
        id=process_id,
        is_template=True
    )
    
    context = {
        'process': process,
        'process_steps': process.prefetched_steps 
    }
    return render(request, 'part/template_selection.html', context)


# 📌 3. Generate the untracked template PDF
def template_process_print_view(request, process_id):
    """
    Generates an untracked (no WorkOrder record) PDF traveler based on a Process ID
    and the masking GET toggle.
    """
    
    process = get_object_or_404(
        Process.objects.select_related('standard', 'classification'),
        id=process_id,
        is_template=True
    )
    
    requires_masking = request.GET.get('masking') != 'False'
    
    exclusion_query = Q()
    if not requires_masking:
        exclusion_query |= Q(method__is_masking_operation=True)

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

    if not process_steps.exists():
        return HttpResponse("Process steps not found or all steps were excluded.", content_type="text/plain")

    pdf_settings = PDFSettings.objects.first()
    current_date = timezone.now().strftime("%m-%d-%Y")
    
    job_data = {
        'surface_area': 'N/A (Template)',
        'amps': 'N/A (Template)',
        'instructions': ["TEMPLATE ONLY: Manually record all required data."],
    }
    
    inspections_qs = getattr(process.standard, 'inspections', None)
    inspections = inspections_qs.all() if inspections_qs else []

    context = {
        'process': process,
        'standard': process.standard,
        'classification': process.classification,
        'process_steps': process_steps,
        'inspections': inspections,
        'untracked_mode': True,
        
        'job_data': job_data,
        'bake_labels': ["Date and Time of Start of Baking", "Date and Time of Start of Soak", "Furnace Control Instrument Set Temperature", "Furnace Identification", "Graph Number"],

        'current_date': current_date,
        'doc_id': pdf_settings.doc_id if pdf_settings else 'CPTS',
        'revision': pdf_settings.revision if pdf_settings else '0',
        'date': pdf_settings.date.strftime('%m-%d-%Y') if pdf_settings else current_date,
        'repair_station': pdf_settings.repair_station if pdf_settings else 'QKPR504X',
        'footer_text': pdf_settings.footer_text if pdf_settings else f"Printed on: {current_date}",
    }

    # Render and Generate PDF
    html_content = render_to_string('work_order/work_order_steps_pdf.html', context)

    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        HTML(string=html_content).write_pdf(temp_file.name)
        temp_file.seek(0)
        pdf_file = temp_file.read()
    
    # Return HTTP Response
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f"Process_{process.standard.name}_{process.classification.class_name if process.classification else 'Unclassified'}_Template.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


# ----------------------------------------------------------------------
# API VIEWS
# ----------------------------------------------------------------------

def standard_classifications_json(request, standard_id):
    classifications = Classification.objects.filter(standard_id=standard_id)
    data = [{"id": c.id, "label": str(c)} for c in classifications]
    return JsonResponse(data, safe=False)
