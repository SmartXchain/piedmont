from django.contrib import admin
from .models import Fixture

@admin.register(Fixture)
class FixtureAdmin(admin.ModelAdmin):
    list_display = ['fixture_id', 'author','publish','status']
    list_filter = ['status', 'created', 'publish', 'author']
    search_field = ['fixture_id', 'notes']
    prepopulated_fields = {'slug': ('fixture_id',)}
    raw_id_fields = ['author']
    date_hierarchy = 'publish'
    ordering = ['status', 'publish']
    show_facets = admin.ShowFacets.ALWAYS
