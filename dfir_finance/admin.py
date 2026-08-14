from django.contrib import admin

from .models import FactureDFIR


@admin.register(FactureDFIR)
class FactureDFIRAdmin(admin.ModelAdmin):
    list_display = ["reference", "type_prestation", "entreprise", "montant_ttc", "statut", "date_emission"]
    list_filter = ["type_prestation", "statut"]
    search_fields = ["reference"]
