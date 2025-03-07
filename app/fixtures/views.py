from django.shortcuts import render, get_object_or_404, redirect
from django.utils.timezone import now
from .models import Fixture
from .forms import FixtureForm


def kanban_dashboard(request):
    """Displays the Kanban-style dashboard for tracking fixture status."""
    today = now().date()

    # Get all fixtures
    all_fixtures = Fixture.objects.all()

    # Fixtures needing repair
    fixtures_needing_repair = all_fixtures.filter(fixtures_due_for_repair__gt=0)

    # Fixtures with due inspections
    fixtures_inspection_due = all_fixtures.filter(inspection_schedule__lte=today)

    # Available Fixtures (Corrected Calculation)
    fixtures_available = all_fixtures.exclude(id__in=fixtures_needing_repair.values_list('id', flat=True))\
                                     .exclude(id__in=fixtures_inspection_due.values_list('id', flat=True))\
                                     .filter(quantity_available__gt=0)

    return render(request, "fixtures/kanban_dashboard.html", {
        "fixtures_available": fixtures_available,
        "fixtures_needing_repair": fixtures_needing_repair,
        "fixtures_inspection_due": fixtures_inspection_due,
    })


def fixture_list(request):
    """Displays a list of all fixtures."""
    fixtures = Fixture.objects.all()
    return render(request, "fixtures/fixture_list.html", {"fixtures": fixtures})


def fixture_create(request):
    """Creates a new fixture."""
    if request.method == "POST":
        form = FixtureForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("fixture_kanban_dashboard")
    else:
        form = FixtureForm()

    return render(request, "fixtures/fixture_form.html", {"form": form})


def fixture_edit(request, fixture_id):
    """Edits an existing fixture."""
    fixture = get_object_or_404(Fixture, id=fixture_id)

    if request.method == "POST":
        form = FixtureForm(request.POST, request.FILES, instance=fixture)
        if form.is_valid():
            form.save()
            return redirect("fixture_kanban_dashboard")
    else:
        form = FixtureForm(instance=fixture)

    return render(request, "fixtures/fixture_form.html", {"form": form, "fixture": fixture})


def fixture_detail(request, fixture_id):
    """View fixture details, including its status and drawings."""
    fixture = get_object_or_404(Fixture, id=fixture_id)
    return render(request, 'fixtures/fixture_detail.html', {'fixture': fixture})
