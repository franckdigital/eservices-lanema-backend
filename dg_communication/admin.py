from django.contrib import admin

from .models import ActionCommunication, Partenariat, Prospect, SatisfactionClient


@admin.register(ActionCommunication)
class ActionCommunicationAdmin(admin.ModelAdmin):
    list_display = ["titre", "type", "statut", "date_debut", "date_fin", "budget", "chiffre_affaires_genere"]
    list_filter = ["type", "statut"]
    search_fields = ["titre", "description"]


@admin.register(Prospect)
class ProspectAdmin(admin.ModelAdmin):
    list_display = ["nom", "organisation", "statut", "source", "date_creation"]
    list_filter = ["statut", "source"]
    search_fields = ["nom", "organisation", "contact_email"]


@admin.register(Partenariat)
class PartenariatAdmin(admin.ModelAdmin):
    list_display = ["nom_partenaire", "statut", "date_signature"]
    list_filter = ["statut"]


@admin.register(SatisfactionClient)
class SatisfactionClientAdmin(admin.ModelAdmin):
    list_display = ["client_nom", "note", "fidele", "date_enquete"]
    list_filter = ["fidele"]
