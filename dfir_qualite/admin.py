from django.contrib import admin

from .models import AmeliorationProgramme, AuditDFIR, ReclamationDFIR


@admin.register(ReclamationDFIR)
class ReclamationDFIRAdmin(admin.ModelAdmin):
    list_display = ["entreprise", "participant", "statut", "date_reception"]
    list_filter = ["statut"]


@admin.register(AmeliorationProgramme)
class AmeliorationProgrammeAdmin(admin.ModelAdmin):
    list_display = ["formation", "date_mise_en_oeuvre"]


@admin.register(AuditDFIR)
class AuditDFIRAdmin(admin.ModelAdmin):
    list_display = ["reference", "type_audit", "date_audit", "resultat"]
    list_filter = ["resultat"]
