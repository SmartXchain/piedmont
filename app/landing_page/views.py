import csv
from collections import defaultdict

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Capability, CapabilityCategory


def landing_page(request):
    categories = CapabilityCategory.objects.all()
    capabilities = Capability.objects.select_related('category').all()

    # Group capabilities by category
    grouped_capabilities = defaultdict(list)
    for cap in capabilities:
        grouped_capabilities[cap.category].append(cap)

    return render(request, 'landing_page/index.html', {
        'categories': categories,
        'grouped_capabilities': grouped_capabilities,
    })


def customer_pricing_view(request):
    categories = CapabilityCategory.objects.all()
    capabilities = Capability.objects.all()

    selected_category = request.GET.get("category")
    selected_standard = request.GET.get("standard")

    if selected_category:
        capabilities = capabilities.filter(category__name=selected_category)

    if selected_standard:
        capabilities = capabilities.filter(standard__icontains=selected_standard)

    return render(request, 'customer_pricing.html', {
        'capabilities': capabilities,
        'categories': categories,
        'selected_category': selected_category,
        'selected_standard': selected_standard,
    })


def capability_pricing_detail(request, pk):
    capability = get_object_or_404(Capability, pk=pk)
    return render(request, 'landing_page/pricing_detail.html', {
        'capability': capability,
    })


def export_capabilities_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="capabilities_pricing.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Name', 'Standard', 'Category', 'Base Rate (USD)', 'Setup Cost',
        'Size Adjustment', 'Material Surcharge', 'Testing & Certs',
        'Post-Processing', 'Environmental Fee', 'Base Job Setup Fee',
        'Minimum Per Part Price', 'Simple Part Price', 'Complex Part Price',
        'Optional Add-ons', 'Total Estimated Cost'
    ])

    for cap in Capability.objects.all():
        addons_str = ", ".join([f"{a.name} (${a.price})" for a in cap.addons.all()])
        writer.writerow([
            cap.name,
            cap.standard,
            cap.category.name,
            cap.cost_usd,
            cap.setup_cost,
            cap.size_adjustment,
            cap.material_surcharge,
            cap.testing_cert_cost,
            cap.post_process_cost,
            cap.env_fee,
            cap.base_job_setup_fee,
            cap.min_per_part_price,
            cap.simple_part_price,
            cap.complex_part_price,
            addons_str,
            cap.total_with_addons()
        ])

    return response
