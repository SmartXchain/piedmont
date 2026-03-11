import csv
from collections import defaultdict

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Capability
from process.models import Process


def landing_page(request):
    """
    Home page: displays all configured processes grouped by Standard.
    Data is pulled live from the Process app (Standard → StandardProcess →
    Classification) rather than the legacy Capability pricing catalog.
    """
    processes = (
        Process.objects
        .select_related('standard', 'standard_process', 'classification')
        .order_by(
            'standard__name',
            'standard__revision',
            'standard_process__title',
        )
    )

    grouped = defaultdict(list)
    for p in processes:
        parts = []
        if p.classification:
            if p.classification.method:
                parts.append(f"Method {p.classification.method}")
            if p.classification.class_name:
                parts.append(f"Class {p.classification.class_name}")
            if p.classification.type:
                parts.append(f"Type {p.classification.type}")
        grouped[p.standard].append({
            'process': p,
            'classification_label': ", ".join(parts) if parts else None,
        })

    return render(request, 'landing_page/index.html', {
        'grouped': grouped.items(),
    })


def capability_pricing_detail(request, pk):
    capability = get_object_or_404(
        Capability.objects.select_related('category').prefetch_related('tags', 'addons'),
        pk=pk,
    )
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

    for cap in Capability.objects.select_related('category').prefetch_related('addons'):
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
