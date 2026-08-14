from django.contrib import admin

from .models import PrestationDMCT


@admin.register(PrestationDMCT)
class PrestationDMCTAdmin(admin.ModelAdmin):
    list_display = ["reference", "type_prestation", "lieu", "agent", "statut", "conforme"]
    list_filter = ["type_prestation", "lieu", "statut"]
    search_fields = ["reference"]
