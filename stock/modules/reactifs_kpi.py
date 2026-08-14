from django.db.models import F, Sum
from django.utils import timezone

from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Article, Lot, MouvementStock


def compute_reactifs_kpis(date_debut=None, date_fin=None):
    """Calcule les 7 KPI des reactifs et consommables de laboratoire."""
    articles = Article.objects.all()
    total_articles = articles.count()

    valeur_stock = sum(float(a.quantite_stock) * float(a.prix_unitaire) for a in articles)

    nb_ruptures = articles.filter(quantite_stock__lte=0).count()
    nb_niveau_suffisant = articles.filter(quantite_stock__gt=F("seuil_alerte")).count()

    mouvements = MouvementStock.objects.filter(type_mouvement="SORTIE")
    if date_debut and date_fin:
        mouvements_periode = mouvements.filter(date_mouvement__date__range=(date_debut, date_fin))
    else:
        today = timezone.now().date()
        mouvements_periode = mouvements.filter(date_mouvement__date__gte=today.replace(day=1))
    consommation_mensuelle = mouvements_periode.aggregate(t=Sum("quantite"))["t"] or 0

    stock_moyen = sum(float(a.quantite_stock) for a in articles) / total_articles if total_articles else 0
    rotation_stock = round(float(consommation_mensuelle) / stock_moyen, 2) if stock_moyen else None

    today = timezone.now().date()
    nb_proches_expiration = Lot.objects.filter(
        date_peremption__gte=today, date_peremption__lte=today + timezone.timedelta(days=30)
    ).count()
    nb_expires = Lot.objects.filter(date_peremption__lt=today).count()

    return {
        "niveau_stock_suffisant": nb_niveau_suffisant,
        "nombre_ruptures_stock": nb_ruptures,
        "consommation_mensuelle": float(consommation_mensuelle),
        "produits_proches_expiration": nb_proches_expiration,
        "produits_expires": nb_expires,
        "valeur_stock": valeur_stock,
        "rotation_stock": rotation_stock,
    }


class ReactifsKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(compute_reactifs_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
