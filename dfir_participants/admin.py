from django.contrib import admin

from .models import EntrepriseDFIR, ParticipantDFIR


@admin.register(EntrepriseDFIR)
class EntrepriseDFIRAdmin(admin.ModelAdmin):
    list_display = ["nom", "secteur_activite", "contact", "actif", "created_at"]
    list_filter = ["actif"]
    search_fields = ["nom", "contact"]


@admin.register(ParticipantDFIR)
class ParticipantDFIRAdmin(admin.ModelAdmin):
    list_display = ["nom", "prenom", "entreprise", "email", "created_at"]
    search_fields = ["nom", "prenom", "email"]
