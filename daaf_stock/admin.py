from django.contrib import admin

from .models import ArticleStock, LotStock, MouvementStockAdmin


@admin.register(ArticleStock)
class ArticleStockAdmin(admin.ModelAdmin):
    list_display = ["reference", "designation", "categorie", "quantite_stock", "seuil_alerte", "prix_unitaire"]
    search_fields = ["reference", "designation"]


@admin.register(LotStock)
class LotStockAdmin(admin.ModelAdmin):
    list_display = ["article", "numero_lot", "quantite", "date_peremption"]


@admin.register(MouvementStockAdmin)
class MouvementStockAdminAdmin(admin.ModelAdmin):
    list_display = ["article", "type", "quantite", "date_mouvement"]
    list_filter = ["type"]
