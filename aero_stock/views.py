from django.db.models import Sum
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission

from .models import MouvementPieceRechange, PieceRechange
from .serializers import MouvementPieceRechangeSerializer, PieceRechangeSerializer

DAE_ENCADREMENT = direction_permission('DAE', min_tier='encadrement')
DAE_MEMBRE = direction_permission('DAE')


def compute_stock_kpis(date_debut=None, date_fin=None):
    """Calcule les 6 KPI Stock pieces de rechange de la DAE. Reutilisable
    directement par le tableau de bord DAE."""
    pieces = PieceRechange.objects.all()
    total_pieces = pieces.count()

    valeur_stock = sum(float(p.quantite_stock) * float(p.prix_unitaire) for p in pieces)

    mouvements = MouvementPieceRechange.objects.all()
    if date_debut and date_fin:
        mouvements = mouvements.filter(date__date__range=(date_debut, date_fin))
    sorties_periode = mouvements.filter(type_mouvement="SORTIE").aggregate(t=Sum("quantite"))["t"] or 0
    stock_moyen = sum(float(p.quantite_stock) for p in pieces) / total_pieces if total_pieces else 0
    rotation_stock = round(float(sorties_periode) / stock_moyen, 2) if stock_moyen else None

    nb_ruptures = pieces.filter(quantite_stock__lte=0).count()
    taux_disponibilite = round((total_pieces - nb_ruptures) / total_pieces * 100, 1) if total_pieces else None

    pieces_critiques = pieces.filter(est_critique=True)
    nb_critiques = pieces_critiques.count()
    nb_critiques_disponibles = pieces_critiques.exclude(quantite_stock__lte=0).count()
    taux_disponibilite_critiques = (
        round(nb_critiques_disponibles / nb_critiques * 100, 1) if nb_critiques else None
    )

    delais_reappro = []
    for piece in pieces:
        entrees = list(
            MouvementPieceRechange.objects.filter(piece=piece, type_mouvement="ENTREE").order_by("date")
        )
        for prev, curr in zip(entrees, entrees[1:]):
            delais_reappro.append((curr.date - prev.date).days)
    delai_moyen_reappro = round(sum(delais_reappro) / len(delais_reappro), 1) if delais_reappro else None

    return {
        "taux_disponibilite_pieces": taux_disponibilite,
        "nombre_ruptures_stock": nb_ruptures,
        "rotation_stocks": rotation_stock,
        "valeur_stock": valeur_stock,
        "delai_moyen_approvisionnement_jours": delai_moyen_reappro,
        "taux_disponibilite_pieces_critiques": taux_disponibilite_critiques,
    }


class PieceRechangeViewSet(viewsets.ModelViewSet):
    queryset = PieceRechange.objects.all()
    serializer_class = PieceRechangeSerializer
    permission_classes = [DAE_ENCADREMENT]


class MouvementPieceRechangeViewSet(viewsets.ModelViewSet):
    queryset = MouvementPieceRechange.objects.select_related("piece").all()
    serializer_class = MouvementPieceRechangeSerializer
    permission_classes = [DAE_ENCADREMENT]


class StockKPIView(APIView):
    permission_classes = [DAE_MEMBRE]

    def get(self, request):
        return Response(compute_stock_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
