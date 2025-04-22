# customer_links/admin.py
from django.contrib import admin
from .models import CustomerLink


@admin.register(CustomerLink)
class CustomerLinkAdmin(admin.ModelAdmin):
    list_display = ('name', 'link_type', 'url')
    list_filter = ('link_type',)
