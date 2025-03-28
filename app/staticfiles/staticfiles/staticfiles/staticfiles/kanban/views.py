from django.shortcuts import render
from django.utils.timezone import now
from datetime import timedelta
from django.http import HttpResponse
import pandas as pd
from .models import Product, ChemicalLot


def kanban_dashboard(request):
    """Displays the Kanban Inventory Dashboard."""

    # Fetch all products
    products = Product.objects.all()

    # Separate products into categories based on their status
    available_products = [product for product in products if product.get_current_stock() > product.trigger_level]
    expiring_soon_products = [product for product in products if any(lot.is_expiring_soon() for lot in product.chemical_lots.all())]
    expired_products = [product for product in products if any(lot.is_expired() for lot in product.chemical_lots.all())]
    needs_reorder_products = [product for product in products if product.get_current_stock() <= product.trigger_level]

    return render(request, 'kanban/kanban_dashboard.html', {
        'available_products': available_products,
        'expiring_soon_products': expiring_soon_products,
        'expired_products': expired_products,
        'needs_reorder_products': needs_reorder_products
    })


def product_list(request):
    """Displays a list of all products and their stock status."""
    products = Product.objects.all()
    return render(request, "kanban/product_list.html", {"products": products})


def product_detail(request, product_id):
    """Displays details of a specific product, including lots."""
    product = Product.objects.get(id=product_id)
    chemical_lots = ChemicalLot.objects.filter(product=product).order_by('expiry_date')
    return render(request, "kanban/product_detail.html", {"product": product, "chemical_lots": chemical_lots})


def export_inventory_report(request):
    """Exports the inventory data as an Excel file."""
    today = now().date()

    # Fetch product data
    products = Product.objects.all().values(
        'name', 'supplier_name', 'supplier_part_number', 'min_quantity', 'max_quantity', 'trigger_level'
    )

    # Fetch chemical lots and manually compute status
    chemical_lots = []
    for lot in ChemicalLot.objects.select_related("product").all():
        if lot.expiry_date:
            if lot.expiry_date < today:
                lot_status = "Expired"
            elif lot.expiry_date <= today + timedelta(days=7):
                lot_status = "Expiring Soon"
            else:
                lot_status = "Available"
        else:
            lot_status = "N/A"

        chemical_lots.append({
            "Product Name": lot.product.name,
            "Purchase Order": lot.purchase_order,
            "Lot Number": lot.lot_number,
            "Expiry Date": lot.expiry_date if lot.expiry_date else "N/A",
            "Quantity": lot.quantity,
            "Status": lot_status,
        })

    # Convert to DataFrames
    product_df = pd.DataFrame(list(products))
    chemical_lot_df = pd.DataFrame(chemical_lots)

    # Create Excel file
    with pd.ExcelWriter("inventory_report.xlsx") as writer:
        product_df.to_excel(writer, sheet_name="Products", index=False)
        chemical_lot_df.to_excel(writer, sheet_name="Chemical Lots", index=False)

    # Return as downloadable response
    with open("inventory_report.xlsx", "rb") as excel:
        response = HttpResponse(excel.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="inventory_report.xlsx"'
        return response
