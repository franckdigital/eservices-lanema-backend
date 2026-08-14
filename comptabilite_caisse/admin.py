from django.contrib import admin

from .models import Caisse, MouvementCaisse


@admin.register(Caisse)
class CaisseAdmin(admin.ModelAdmin):
    list_display = ["nom", "responsable", "solde_initial", "actif"]
    list_filter = ["actif"]


@admin.register(MouvementCaisse)
class MouvementCaisseAdmin(admin.ModelAdmin):
    list_display = ["caisse", "type_mouvement", "montant", "date_mouvement"]
    list_filter = ["type_mouvement"]
