from django.db.models import F, Sum
from django.utils import timezone

from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ArticleStock, LotStock, MouvementStockAdmin
from .serializers import ArticleStockSerializer, LotStockSerializer, MouvementStockAdminSerializer


def compute_stock_kpis(date_debut=None, date_fin=None):
    """Calcule les 7 KPI Stock administratif. Reutilisable directement par le
    tableau de bord DAAF."""
    articles = ArticleStock.objects.all()
    total_articles = articles.count()

    valeur_stock = sum(float(a.quantite_stock) * float(a.prix_unitaire) for a in articles)

    mouvements = MouvementStockAdmin.objects.all()
    if date_debut and date_fin:
        mouvements = mouvements.filter(date_mouvement__date__range=(date_debut, date_fin))
    sorties_periode = mouvements.filter(type="SORTIE").aggregate(t=Sum("quantite"))["t"] or 0
    stock_moyen = sum(float(a.quantite_stock) for a in articles) / total_articles if total_articles else 0
    rotation_stock = round(float(sorties_periode) / stock_moyen, 2) if stock_moyen else None

    nb_ruptures = articles.filter(quantite_stock__lte=0).count()
    nb_sous_seuil = articles.filter(quantite_stock__lte=F("seuil_alerte"), seuil_alerte__gt=0).count()

    today = timezone.now().date()
    nb_perimes = LotStock.objects.filter(date_peremption__lt=today).count()

    taux_disponibilite = round((total_articles - nb_ruptures) / total_articles * 100, 1) if total_articles else None

    delais_reappro = []
    for article in articles:
        entrees = list(
            MouvementStockAdmin.objects.filter(article=article, type="ENTREE").order_by("date_mouvement")
        )
        for prev, curr in zip(entrees, entrees[1:]):
            delais_reappro.append((curr.date_mouvement - prev.date_mouvement).days)
    delai_moyen_reappro = round(sum(delais_reappro) / len(delais_reappro), 1) if delais_reappro else None

    return {
        "valeur_stock": valeur_stock,
        "rotation_stocks": rotation_stock,
        "nombre_ruptures_stock": nb_ruptures,
        "nombre_articles_sous_seuil": nb_sous_seuil,
        "nombre_articles_perimes": nb_perimes,
        "taux_disponibilite_fournitures": taux_disponibilite,
        "delai_moyen_reapprovisionnement_jours": delai_moyen_reappro,
    }


class ArticleStockViewSet(viewsets.ModelViewSet):
    queryset = ArticleStock.objects.all()
    serializer_class = ArticleStockSerializer
    permission_classes = [permissions.IsAuthenticated]


class LotStockViewSet(viewsets.ModelViewSet):
    queryset = LotStock.objects.select_related("article").all()
    serializer_class = LotStockSerializer
    permission_classes = [permissions.IsAuthenticated]


class MouvementStockAdminViewSet(viewsets.ModelViewSet):
    queryset = MouvementStockAdmin.objects.select_related("article").all()
    serializer_class = MouvementStockAdminSerializer
    permission_classes = [permissions.IsAuthenticated]


class StockKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")
        return Response(compute_stock_kpis(date_debut, date_fin))
