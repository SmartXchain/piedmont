# views.py
from django.shortcuts import render, redirect
from django.utils.timezone import now
from .models import Chemical


def index(request):
    chemicals = Chemical.objects.all()
    available = [chem for chem in chemicals if chem.status == 'Available']
    expiring_soon = [chem for chem in chemicals if chem.status == 'Expiring Soon']
    expired = [chem for chem in chemicals if chem.status == 'Expired']

    context = {
        'available': available,
        'expiring_soon': expiring_soon,
        'expired': expired,
    }

    return render(request, 'kanban/index.html', context)


def add_chemical(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        quantity = int(request.POST.get('quantity'))
        expiry_date = request.POST.get('expiry_date')

        Chemical.objects.create(
            name=name,
            quantity=quantity,
            expiry_date=expiry_date
        )

        return redirect('index')
    return render(request, 'kanban/add_chemical.html')
