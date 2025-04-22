# customer_links/views.py
from django.shortcuts import render
from .models import CustomerLink


def customer_links_list(request):
    links = CustomerLink.objects.all()
    return render(request, 'customer_links/link_list.html', {'links': links})
