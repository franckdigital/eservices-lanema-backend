from django.contrib import admin

from .models import ActionCorrectiveDMCT, AuditDMCT, NonConformiteDMCT


@admin.register(NonConformiteDMCT)
class NonConformiteDMCTAdmin(admin.ModelAdmin):
    list_display = ["reference", "gravite", "statut", "responsable", "date_creation"]
    list_filter = ["gravite", "statut"]
    search_fields = ["reference"]


@admin.register(ActionCorrectiveDMCT)
class ActionCorrectiveDMCTAdmin(admin.ModelAdmin):
    list_display = ["non_conformite", "responsable", "statut", "date_prevue", "date_realisation"]
    list_filter = ["statut"]


@admin.register(AuditDMCT)
class AuditDMCTAdmin(admin.ModelAdmin):
    list_display = ["reference", "type_audit", "date_audit", "resultat"]
    list_filter = ["resultat"]
