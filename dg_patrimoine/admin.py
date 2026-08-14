from django.contrib import admin

from .models import Bien, InventairePatrimoine, MaintenanceBien, MouvementBien


@admin.register(Bien)
class BienAdmin(admin.ModelAdmin):
    list_display = ["code", "designation", "categorie", "statut", "valeur_acquisition", "valeur_actuelle"]
    list_filter = ["categorie", "statut"]
    search_fields = ["code", "designation"]


@admin.register(MouvementBien)
class MouvementBienAdmin(admin.ModelAdmin):
    list_display = ["bien", "type_mouvement", "date_mouvement", "effectue_par"]
    list_filter = ["type_mouvement"]


@admin.register(MaintenanceBien)
class MaintenanceBienAdmin(admin.ModelAdmin):
    list_display = ["bien", "type_maintenance", "date_maintenance", "cout"]
    list_filter = ["type_maintenance"]


@admin.register(InventairePatrimoine)
class InventairePatrimoineAdmin(admin.ModelAdmin):
    list_display = ["date_inventaire", "responsable", "nombre_biens_verifies", "ecarts_constates"]
