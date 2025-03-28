from django.shortcuts import render


def pm_landing_page(request):
    """Landing page for the Preventive Maintenance (PM) system."""
    return render(request, 'pm/pm_landing.html')
