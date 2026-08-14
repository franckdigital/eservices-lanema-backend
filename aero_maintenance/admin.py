from django.contrib import admin

from .models import BatterieAeronef, InspectionRoue, OrdreTravail, RoueAeronef


@admin.register(OrdreTravail)
class OrdreTravailAdmin(admin.ModelAdmin):
    list_display = ["reference", "aeronef", "type_intervention", "technicien", "statut", "date_demande"]
    list_filter = ["type_intervention", "statut"]
    search_fields = ["reference"]


@admin.register(RoueAeronef)
class RoueAeronefAdmin(admin.ModelAdmin):
    list_display = ["numero_serie", "aeronef", "statut", "nombre_cycles"]
    list_filter = ["statut"]


@admin.register(InspectionRoue)
class InspectionRoueAdmin(admin.ModelAdmin):
    list_display = ["roue", "type_inspection", "conforme", "date_inspection"]
    list_filter = ["type_inspection", "conforme"]


@admin.register(BatterieAeronef)
class BatterieAeronefAdmin(admin.ModelAdmin):
    list_display = ["numero_serie", "aeronef", "statut", "date_mise_en_service", "date_derniere_maintenance"]
    list_filter = ["statut"]
