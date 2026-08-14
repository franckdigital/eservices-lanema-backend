from django.db.models import Sum
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CompteBancaire, MouvementBancaire, RapprochementBancaire
from .serializers import (
    CompteBancaireSerializer,
    MouvementBancaireSerializer,
    RapprochementBancaireSerializer,
)


def _solde_compte(compte):
    credits = compte.mouvements.filter(type_mouvement="CREDIT").aggregate(t=Sum("montant"))["t"] or 0
    debits = compte.mouvements.filter(type_mouvement="DEBIT").aggregate(t=Sum("montant"))["t"] or 0
    return float(compte.solde_initial) + float(credits) - float(debits)


def compute_tresorerie_kpis(date_debut=None, date_fin=None):
    """Calcule les 6 KPI Tresorerie de la comptabilite. Reutilisable
    directement par le tableau de bord comptabilite."""
    comptes = CompteBancaire.objects.filter(actif=True)
    solde_par_compte = [
        {"compte": f"{c.nom_banque} ({c.numero_compte})", "solde": _solde_compte(c)} for c in comptes
    ]
    solde_global = sum(s["solde"] for s in solde_par_compte)

    mouvements = MouvementBancaire.objects.all()
    if date_debut and date_fin:
        mouvements = mouvements.filter(date_mouvement__range=(date_debut, date_fin))

    today = timezone.now().date()
    debut_mois = today.replace(day=1)
    mouvements_mois = MouvementBancaire.objects.filter(date_mouvement__gte=debut_mois)
    flux_entrants = mouvements_mois.filter(type_mouvement="CREDIT").aggregate(t=Sum("montant"))["t"] or 0
    flux_sortants = mouvements_mois.filter(type_mouvement="DEBIT").aggregate(t=Sum("montant"))["t"] or 0

    total_mouvements = mouvements.count()
    non_rapproches = mouvements.filter(rapproche=False).count()
    taux_rapprochement = (
        round((total_mouvements - non_rapproches) / total_mouvements * 100, 1) if total_mouvements else None
    )

    return {
        "solde_global": solde_global,
        "solde_par_compte": solde_par_compte,
        "flux_entrants_mois": float(flux_entrants),
        "flux_sortants_mois": float(flux_sortants),
        "nombre_mouvements_non_rapproches": non_rapproches,
        "taux_rapprochement": taux_rapprochement,
    }


class CompteBancaireViewSet(viewsets.ModelViewSet):
    queryset = CompteBancaire.objects.all()
    serializer_class = CompteBancaireSerializer
    permission_classes = [permissions.IsAuthenticated]


class MouvementBancaireViewSet(viewsets.ModelViewSet):
    queryset = MouvementBancaire.objects.select_related("compte").all()
    serializer_class = MouvementBancaireSerializer
    permission_classes = [permissions.IsAuthenticated]


class RapprochementBancaireViewSet(viewsets.ModelViewSet):
    queryset = RapprochementBancaire.objects.select_related("compte").all()
    serializer_class = RapprochementBancaireSerializer
    permission_classes = [permissions.IsAuthenticated]


class TresorerieKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(compute_tresorerie_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
