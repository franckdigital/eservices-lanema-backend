from django.contrib import admin

from .models import Batiment, InterventionTechnique, PanneVehicule, ReservationSalle, Salle, Vehicule


@admin.register(Vehicule)
class VehiculeAdmin(admin.ModelAdmin):
    list_display = ["immatriculation", "marque", "modele", "statut", "kilometrage"]
    list_filter = ["statut"]


@admin.register(PanneVehicule)
class PanneVehiculeAdmin(admin.ModelAdmin):
    list_display = ["vehicule", "date_panne", "date_reparation", "cout"]


@admin.register(Batiment)
class BatimentAdmin(admin.ModelAdmin):
    list_display = ["nom", "site", "disponible", "etat"]
    list_filter = ["disponible"]


@admin.register(Salle)
class SalleAdmin(admin.ModelAdmin):
    list_display = ["nom", "capacite", "batiment"]


@admin.register(ReservationSalle)
class ReservationSalleAdmin(admin.ModelAdmin):
    list_display = ["salle", "date_debut", "date_fin", "motif"]


@admin.register(InterventionTechnique)
class InterventionTechniqueAdmin(admin.ModelAdmin):
    list_display = ["type_intervention", "batiment", "date_intervention"]
