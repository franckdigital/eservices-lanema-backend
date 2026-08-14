from django.contrib import admin

from .models import DemandeDMCT


@admin.register(DemandeDMCT)
class DemandeDMCTAdmin(admin.ModelAdmin):
    list_display = ["reference", "type_demande", "client", "statut", "date_demande"]
    list_filter = ["type_demande", "statut"]
    search_fields = ["reference"]
