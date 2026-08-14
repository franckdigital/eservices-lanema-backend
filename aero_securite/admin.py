from django.contrib import admin

from .models import ControleReglementaire, EcartReglementaire, FormationSecurite, IncidentTechnique, RapportSecurite


@admin.register(IncidentTechnique)
class IncidentTechniqueAdmin(admin.ModelAdmin):
    list_display = ["reference", "gravite", "est_accident", "date_incident"]
    list_filter = ["gravite", "est_accident"]
    search_fields = ["reference"]


@admin.register(EcartReglementaire)
class EcartReglementaireAdmin(admin.ModelAdmin):
    list_display = ["reference", "date_constat", "resolu"]
    list_filter = ["resolu"]


@admin.register(RapportSecurite)
class RapportSecuriteAdmin(admin.ModelAdmin):
    list_display = ["reference", "date_creation"]


@admin.register(ControleReglementaire)
class ControleReglementaireAdmin(admin.ModelAdmin):
    list_display = ["reference", "organisme", "date_controle", "resultat"]
    list_filter = ["organisme", "resultat"]


@admin.register(FormationSecurite)
class FormationSecuriteAdmin(admin.ModelAdmin):
    list_display = ["titre", "date_formation", "nombre_participants", "duree_heures"]
