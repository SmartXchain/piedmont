from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils.timezone import now
from .models import Chemical
from .forms import ChemicalForm
from datetime import timedelta
from django.db.models import F


def chemical_list(request):
    """Display all chemicals with their status."""
    chemicals = Chemical.objects.all().order_by("name")
    return render(request, "kanban/chemical_list.html", {"chemicals": chemicals})


def chemical_detail(request, chemical_id):
    """Show details for a single chemical."""
    chemical = get_object_or_404(Chemical, id=chemical_id)
    return render(request, "kanban/chemical_detail.html", {"chemical": chemical})

def chemical_create(request):
    """Add a new chemical to inventory."""
    print("DEBUG: Entered chemical_create view")  # ✅ Check if function is called

    if request.method == "POST":
        print("DEBUG: Received POST request with data:", request.POST)  # ✅ Check if data is received

        form = ChemicalForm(request.POST, request.FILES)
        
        if form.is_valid():
            print("DEBUG: Form is valid, saving data...")  # ✅ Form is valid, saving chemical
            form.save()
            messages.success(request, "Chemical added successfully.")
            return redirect("kanban_dashboard")
        else:
            print("DEBUG: Form errors:", form.errors)  # ❌ Form errors detected!
            messages.error(request, "Error: Please correct the form errors.")

    else:
        form = ChemicalForm()
        print("DEBUG: Displaying empty form")  # ✅ Ensure form is displayed

    return render(request, "kanban/chemical_form.html", {"form": form})

def chemical_edit(request, chemical_id):
    """Edit an existing chemical in inventory."""
    chemical = get_object_or_404(Chemical, id=chemical_id)

    if request.method == "POST":
        form = ChemicalForm(request.POST, request.FILES, instance=chemical)
        if form.is_valid():
            form.save()
            messages.success(request, "Chemical updated successfully.")
            return redirect("chemical_detail", chemical_id=chemical.id)
    else:
        form = ChemicalForm(instance=chemical)

    return render(request, "kanban/chemical_form.html", {"form": form, "chemical": chemical})


def chemical_expired_list(request):
    """Show all expired chemicals."""
    expired_chemicals = Chemical.objects.filter(expiry_date__lt=now().date())
    return render(request, "kanban/chemical_expired_list.html", {"chemicals": expired_chemicals})


def chemical_expiring_list(request):
    """Show chemicals expiring soon (within 7 days)."""
    expiring_soon = now().date() + timedelta(days=7)
    chemicals = Chemical.objects.filter(expiry_date__lte=expiring_soon, expiry_date__gte=now().date())
    return render(request, "kanban/chemical_expiring_list.html", {"chemicals": chemicals})

def kanban_dashboard(request):
    """Displays an overview of inventory status, expiring chemicals, and auto-reorder alerts."""
    
    # Fetch all chemicals
    chemicals = Chemical.objects.all()
    
    # Filter chemicals based on status
    expired_chemicals = chemicals.filter(expiry_date__lt=now().date())
    expiring_chemicals = chemicals.filter(expiry_date__range=[now().date(), now().date() + timedelta(days=7)])
    low_stock_chemicals = chemicals.filter(quantity__lte=F("reorder_level"))  # ✅ Fix: Correctly using F()

    return render(request, "kanban/kanban_dashboard.html", {
        "total_chemicals": chemicals.count(),
        "expired_chemicals": expired_chemicals,
        "expiring_chemicals": expiring_chemicals,
        "low_stock_chemicals": low_stock_chemicals,
        "recent_chemicals": chemicals.order_by("-created_at")[:5],  # ✅ Show the 5 latest chemicals
    })