from django.contrib import admin

from .models import ProjetInnovation


@admin.register(ProjetInnovation)
class ProjetInnovationAdmin(admin.ModelAdmin):
    list_display = ["reference", "titre", "statut", "date_lancement"]
    list_filter = ["statut"]
    search_fields = ["reference", "titre"]
