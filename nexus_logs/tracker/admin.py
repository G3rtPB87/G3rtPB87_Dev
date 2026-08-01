from django.contrib import admin

from .models import AppConfig, TimelineEntry


@admin.register(TimelineEntry)
class TimelineEntryAdmin(admin.ModelAdmin):
    list_display = ["visit_date", "entry_type", "source", "location_name", "start_time", "end_time"]
    list_filter = ["entry_type", "source", "visit_date"]
    search_fields = ["location_name", "address", "parts_used", "comments"]
    date_hierarchy = "visit_date"


@admin.register(AppConfig)
class AppConfigAdmin(admin.ModelAdmin):
    list_display = ["default_export_format", "home_address"]
