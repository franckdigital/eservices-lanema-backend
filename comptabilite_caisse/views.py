from django.db.models import Sum
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Caisse, MouvementCaisse
from .serializers import CaisseSerializer, MouvementCaisseSerializer


def _solde_caisse(caisse):
    entrees = caisse.mouvements.filter(type_mouvement="ENTREE").aggregate(t=Sum("montant"))["t"] or 0
    sorties = caisse.mouvements.filter(type_mouvement="SORTIE").aggregate(t=Sum("montant"))["t"] or 0
    return float(caisse.solde_initial) + float(entrees) - float(sorties)


def compute_caisse_kpis(date_debut=None, date_fin=None):
    """Calcule les 5 KPI Caisse de la comptabilite. Reutilisable directement
    par le tableau de bord comptabilite."""
    caisses = Caisse.objects.filter(actif=True)
    solde_par_caisse = [{"caisse": c.nom, "solde": _solde_caisse(c)} for c in caisses]
    solde_total = sum(s["solde"] for s in solde_par_caisse)

    today = timezone.now().date()
    mouvements_jour = MouvementCaisse.objects.filter(date_mouvement__date=today)

    debut_mois = today.replace(day=1)
    mouvements_mois = MouvementCaisse.objects.filter(date_mouvement__date__gte=debut_mois)
    entrees_mois = mouvements_mois.filter(type_mouvement="ENTREE").aggregate(t=Sum("montant"))["t"] or 0
    sorties_mois = mouvements_mois.filter(type_mouvement="SORTIE").aggregate(t=Sum("montant"))["t"] or 0

    return {
        "solde_total_caisses": solde_total,
        "solde_par_caisse": solde_par_caisse,
        "nombre_mouvements_jour": mouvements_jour.count(),
        "entrees_mois": float(entrees_mois),
        "sorties_mois": float(sorties_mois),
        "nombre_caisses_actives": caisses.count(),
    }


class CaisseViewSet(viewsets.ModelViewSet):
    queryset = Caisse.objects.select_related("responsable").all()
    serializer_class = CaisseSerializer
    permission_classes = [permissions.IsAuthenticated]


class MouvementCaisseViewSet(viewsets.ModelViewSet):
    queryset = MouvementCaisse.objects.select_related("caisse").all()
    serializer_class = MouvementCaisseSerializer
    permission_classes = [permissions.IsAuthenticated]


class CaisseKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(compute_caisse_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
