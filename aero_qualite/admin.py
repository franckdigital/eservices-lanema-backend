from django.contrib import admin

from .models import ActionCorrectiveDAE, AuditQualiteDAE, NonConformiteDAE


@admin.register(NonConformiteDAE)
class NonConformiteDAEAdmin(admin.ModelAdmin):
    list_display = ["reference", "gravite", "statut", "responsable", "date_creation"]
    list_filter = ["gravite", "statut"]
    search_fields = ["reference"]


@admin.register(ActionCorrectiveDAE)
class ActionCorrectiveDAEAdmin(admin.ModelAdmin):
    list_display = ["non_conformite", "responsable", "statut", "date_prevue", "date_realisation"]
    list_filter = ["statut"]


@admin.register(AuditQualiteDAE)
class AuditQualiteDAEAdmin(admin.ModelAdmin):
    list_display = ["reference", "type_audit", "date_audit", "resultat"]
    list_filter = ["resultat"]
