from django.contrib import admin

from .models import ClientDMCT, ReclamationClientDMCT


@admin.register(ClientDMCT)
class ClientDMCTAdmin(admin.ModelAdmin):
    list_display = ["nom", "secteur_activite", "contact", "actif", "created_at"]
    list_filter = ["secteur_activite", "actif"]
    search_fields = ["nom", "contact"]


@admin.register(ReclamationClientDMCT)
class ReclamationClientDMCTAdmin(admin.ModelAdmin):
    list_display = ["client", "date_reception", "date_traitement", "statut", "note_satisfaction"]
    list_filter = ["statut"]
