from django.contrib import admin

from .models import Aeronef, ClientAeronautique, ReclamationClientDAE


@admin.register(ClientAeronautique)
class ClientAeronautiqueAdmin(admin.ModelAdmin):
    list_display = ["nom", "contact", "actif", "created_at"]
    search_fields = ["nom", "contact"]


@admin.register(Aeronef)
class AeronefAdmin(admin.ModelAdmin):
    list_display = ["immatriculation", "type_aeronef", "client", "statut"]
    list_filter = ["statut"]
    search_fields = ["immatriculation", "type_aeronef"]


@admin.register(ReclamationClientDAE)
class ReclamationClientDAEAdmin(admin.ModelAdmin):
    list_display = ["client", "date_reception", "date_traitement", "statut", "note_satisfaction"]
    list_filter = ["statut"]
