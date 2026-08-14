from django.contrib import admin

from .models import AvisJuridique, Contentieux, Contrat, DossierJuridique, ProcedureDisciplinaire


@admin.register(DossierJuridique)
class DossierJuridiqueAdmin(admin.ModelAdmin):
    list_display = ["reference", "type_dossier", "titre", "statut", "date_ouverture", "date_cloture"]
    list_filter = ["type_dossier", "statut"]
    search_fields = ["reference", "titre"]


@admin.register(Contrat)
class ContratAdmin(admin.ModelAdmin):
    list_display = ["reference", "intitule", "partie_prenante", "statut", "date_expiration"]
    list_filter = ["statut"]


@admin.register(Contentieux)
class ContentieuxAdmin(admin.ModelAdmin):
    list_display = ["reference", "partie_adverse", "statut", "issue", "date_ouverture"]
    list_filter = ["statut"]


@admin.register(AvisJuridique)
class AvisJuridiqueAdmin(admin.ModelAdmin):
    list_display = ["sujet", "demandeur", "date_demande", "date_reponse"]


@admin.register(ProcedureDisciplinaire)
class ProcedureDisciplinaireAdmin(admin.ModelAdmin):
    list_display = ["reference", "agent_concerne", "statut", "date_ouverture"]
    list_filter = ["statut"]
