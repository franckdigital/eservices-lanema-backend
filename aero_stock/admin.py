from django.contrib import admin

from .models import MouvementPieceRechange, PieceRechange


@admin.register(PieceRechange)
class PieceRechangeAdmin(admin.ModelAdmin):
    list_display = ["reference", "designation", "categorie", "quantite_stock", "seuil_alerte", "est_critique"]
    list_filter = ["categorie", "est_critique"]
    search_fields = ["reference", "designation"]


@admin.register(MouvementPieceRechange)
class MouvementPieceRechangeAdmin(admin.ModelAdmin):
    list_display = ["piece", "type_mouvement", "quantite", "date"]
    list_filter = ["type_mouvement"]
