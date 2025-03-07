from django.shortcuts import render
from .models import Tank, ProductionLine
from collections import OrderedDict
import pandas as pd
from django.http import HttpResponse

def tank_list(request):
    """Displays all tanks grouped by production line."""
    tanks = Tank.objects.all().order_by("production_line__name")

    # Group tanks by production line
    tanks_by_production_line = OrderedDict()
    for production_line in ProductionLine.objects.all():
        tanks_by_production_line[production_line] = tanks.filter(production_line=production_line)

    return render(request, "tanks/tank_list.html", {"tanks_by_production_line": tanks_by_production_line})


def export_tanks_to_excel(request):
    """Exports tank data to an Excel file grouped by Production Line."""

    # Fetch all tank data
    tanks = Tank.objects.select_related("production_line").all()

    # Convert tank data into a DataFrame
    data = []
    for tank in tanks:
        data.append({
            "Production Line": tank.production_line.name if tank.production_line else "N/A",
            "Tank Name": tank.name,
            "Chemical Composition": tank.chemical_composition,
            "Length (in)": tank.length or "N/A",
            "Width (in)": tank.width or "N/A",
            "Height (in)": tank.height or "N/A",
            "Liquid Level (in)": tank.liquid_level or "N/A",
            "Surface Area (sq in)": tank.surface_area or "N/A",
            "Vented": "Yes" if tank.is_vented else "No",
            "Scrubber": tank.scrubber or "N/A",
            "Max Amps": tank.max_amps or "N/A",
            "Last Updated": tank.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
        })

    # Create DataFrame and group by Production Line
    df = pd.DataFrame(data)
    df.sort_values(by=["Production Line", "Tank Name"], inplace=True)  # Sort by line and tank name

    # Create HTTP response with Excel content
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="tanks_inventory.xlsx"'

    # Write DataFrame to an Excel file in memory
    with pd.ExcelWriter(response, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Tanks Data")

    return response
