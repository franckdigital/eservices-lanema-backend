from django.contrib import admin

from .models import Formation, InscriptionParticipant, SessionFormation, SupportPedagogique


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ["reference", "titre", "type_formation", "modalite", "certifiante"]
    list_filter = ["type_formation", "modalite", "certifiante"]
    search_fields = ["reference", "titre"]


@admin.register(SessionFormation)
class SessionFormationAdmin(admin.ModelAdmin):
    list_display = ["formation", "formateur", "entreprise", "statut", "date_debut"]
    list_filter = ["statut"]


@admin.register(InscriptionParticipant)
class InscriptionParticipantAdmin(admin.ModelAdmin):
    list_display = ["session", "participant", "present", "reussite", "certifie", "abandon"]
    list_filter = ["present", "reussite", "certifie", "abandon"]


@admin.register(SupportPedagogique)
class SupportPedagogiqueAdmin(admin.ModelAdmin):
    list_display = ["titre", "formation", "type_contenu", "date_creation", "nombre_telechargements"]
    list_filter = ["type_contenu"]
