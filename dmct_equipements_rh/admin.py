from django.contrib import admin

from .models import (
    CertificationAgentDMCT,
    EquipementReference,
    EtalonnageReference,
    FormationDMCT,
    MaintenancePreventiveReference,
    PanneEquipementReference,
)


@admin.register(EquipementReference)
class EquipementReferenceAdmin(admin.ModelAdmin):
    list_display = ["code", "designation", "est_etalon", "statut"]
    list_filter = ["est_etalon", "statut"]
    search_fields = ["code", "designation"]


@admin.register(PanneEquipementReference)
class PanneEquipementReferenceAdmin(admin.ModelAdmin):
    list_display = ["equipement", "date_panne", "date_reparation"]


@admin.register(MaintenancePreventiveReference)
class MaintenancePreventiveReferenceAdmin(admin.ModelAdmin):
    list_display = ["equipement", "date_prevue", "date_realisee", "statut"]
    list_filter = ["statut"]


@admin.register(EtalonnageReference)
class EtalonnageReferenceAdmin(admin.ModelAdmin):
    list_display = ["equipement", "date_etalonnage", "date_prochain", "resultat"]


@admin.register(CertificationAgentDMCT)
class CertificationAgentDMCTAdmin(admin.ModelAdmin):
    list_display = ["agent", "competence", "date_obtention", "date_expiration"]


@admin.register(FormationDMCT)
class FormationDMCTAdmin(admin.ModelAdmin):
    list_display = ["titre", "date_formation", "nombre_participants", "duree_heures"]
