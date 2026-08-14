from django.db.models import Count

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Article, Alerte, Lot, Quarantaine


class StockDashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = {
            "total_articles": Article.objects.count(),
            "total_lots": Lot.objects.count(),
            "lots_ouverts": Lot.objects.filter(ouvert=True).count(),
            "alertes_ouvertes": Alerte.objects.filter(traitee=False).count(),
            "lots_en_quarantaine": Quarantaine.objects.filter(levee=False).count(),
            "articles_par_categorie": list(
                Article.objects.values("categorie__nom").annotate(total=Count("id"))
            ),
        }
        return Response(data)
