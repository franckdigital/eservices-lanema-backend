from rest_framework import serializers

from .models import ArticleStock, LotStock, MouvementStockAdmin


class ArticleStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleStock
        fields = ["id", "reference", "designation", "categorie", "unite", "quantite_stock", "seuil_alerte", "prix_unitaire"]
        read_only_fields = ["id"]


class LotStockSerializer(serializers.ModelSerializer):
    article_designation = serializers.CharField(source="article.designation", read_only=True)

    class Meta:
        model = LotStock
        fields = ["id", "article", "article_designation", "numero_lot", "quantite", "date_peremption"]
        read_only_fields = ["id"]


class MouvementStockAdminSerializer(serializers.ModelSerializer):
    article_designation = serializers.CharField(source="article.designation", read_only=True)

    class Meta:
        model = MouvementStockAdmin
        fields = ["id", "article", "article_designation", "type", "quantite", "date_mouvement"]
        read_only_fields = ["id", "date_mouvement"]
