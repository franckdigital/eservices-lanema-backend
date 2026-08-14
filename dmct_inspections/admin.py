from django.contrib import admin

from .models import ContreVisiteDMCT, InspectionDMCT


@admin.register(InspectionDMCT)
class InspectionDMCTAdmin(admin.ModelAdmin):
    list_display = ["reference", "etablissement", "categorie", "type_controle", "conforme", "date_inspection"]
    list_filter = ["categorie", "type_controle", "conforme"]
    search_fields = ["reference"]


@admin.register(ContreVisiteDMCT)
class ContreVisiteDMCTAdmin(admin.ModelAdmin):
    list_display = ["inspection", "date_contre_visite", "resultat"]
