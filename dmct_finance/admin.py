from django.contrib import admin

from .models import FactureDMCT


@admin.register(FactureDMCT)
class FactureDMCTAdmin(admin.ModelAdmin):
    list_display = ["reference", "client", "montant_ttc", "statut", "date_emission", "date_paiement"]
    list_filter = ["statut"]
    search_fields = ["reference"]
