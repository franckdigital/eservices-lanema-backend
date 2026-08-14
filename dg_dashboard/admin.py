from django.contrib import admin

from .models import ObjectifStrategique


@admin.register(ObjectifStrategique)
class ObjectifStrategiqueAdmin(admin.ModelAdmin):
    list_display = ["nom", "type", "direction", "service", "cible", "valeur_actuelle", "periode", "statut"]
    list_filter = ["type", "statut"]
