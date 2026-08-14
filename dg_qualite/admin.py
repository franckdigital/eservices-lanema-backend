from django.contrib import admin

from .models import (
    ActionQualite,
    AuditQualite,
    IndicateurQualite,
    NonConformiteQualite,
    ReclamationClient,
    RevueDirection,
)


@admin.register(NonConformiteQualite)
class NonConformiteQualiteAdmin(admin.ModelAdmin):
    list_display = ["reference", "gravite", "statut", "service_concerne", "date_detection"]
    list_filter = ["gravite", "statut"]


@admin.register(ActionQualite)
class ActionQualiteAdmin(admin.ModelAdmin):
    list_display = ["type", "non_conformite", "statut", "responsable", "date_planification"]
    list_filter = ["type", "statut"]


@admin.register(AuditQualite)
class AuditQualiteAdmin(admin.ModelAdmin):
    list_display = ["reference", "type_audit", "date_audit", "resultat"]
    list_filter = ["type_audit", "resultat"]


@admin.register(ReclamationClient)
class ReclamationClientAdmin(admin.ModelAdmin):
    list_display = ["client_nom", "statut", "date_reception", "date_traitement", "note_satisfaction"]
    list_filter = ["statut"]


@admin.register(RevueDirection)
class RevueDirectionAdmin(admin.ModelAdmin):
    list_display = ["date_revue"]


@admin.register(IndicateurQualite)
class IndicateurQualiteAdmin(admin.ModelAdmin):
    list_display = ["nom", "cible", "valeur_actuelle", "periode", "atteint"]
