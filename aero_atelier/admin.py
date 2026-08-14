from django.contrib import admin

from .models import (
    CertificationTechnicien,
    EquipementAtelier,
    EtalonnageAtelier,
    MaintenancePreventiveAtelier,
    PanneEquipementAtelier,
)


@admin.register(EquipementAtelier)
class EquipementAtelierAdmin(admin.ModelAdmin):
    list_display = ["code", "designation", "statut"]
    list_filter = ["statut"]
    search_fields = ["code", "designation"]


@admin.register(PanneEquipementAtelier)
class PanneEquipementAtelierAdmin(admin.ModelAdmin):
    list_display = ["equipement", "date_panne", "date_reparation"]


@admin.register(MaintenancePreventiveAtelier)
class MaintenancePreventiveAtelierAdmin(admin.ModelAdmin):
    list_display = ["equipement", "date_prevue", "date_realisee", "statut"]
    list_filter = ["statut"]


@admin.register(EtalonnageAtelier)
class EtalonnageAtelierAdmin(admin.ModelAdmin):
    list_display = ["equipement", "date_etalonnage", "date_prochain", "resultat"]


@admin.register(CertificationTechnicien)
class CertificationTechnicienAdmin(admin.ModelAdmin):
    list_display = ["technicien", "competence", "date_obtention", "date_expiration"]
