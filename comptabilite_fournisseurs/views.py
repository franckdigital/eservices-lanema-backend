from django.db.models import Sum
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FactureFournisseur, FournisseurComptable, PaiementFournisseur
from .serializers import (
    FactureFournisseurSerializer,
    FournisseurComptableSerializer,
    PaiementFournisseurSerializer,
)


def compute_fournisseurs_kpis(date_debut=None, date_fin=None):
    """Calcule les 6 KPI Fournisseurs de la comptabilite. Reutilisable
    directement par le tableau de bord comptabilite."""
    factures = FactureFournisseur.objects.all()
    if date_debut and date_fin:
        factures = factures.filter(date_reception__range=(date_debut, date_fin))

    factures_payees = factures.filter(statut="PAYEE")
    montant_du = factures.exclude(statut="PAYEE").aggregate(t=Sum("montant_ttc"))["t"] or 0

    paiements = PaiementFournisseur.objects.filter(facture_fournisseur__in=factures)
    delais = []
    for paiement in paiements.select_related("facture_fournisseur"):
        delais.append((paiement.date_paiement - paiement.facture_fournisseur.date_reception).days)
    delai_moyen_paiement = round(sum(delais) / len(delais), 1) if delais else None

    factures_avec_echeance = factures_payees.filter(date_echeance__isnull=False)
    nb_dans_les_delais = 0
    for facture in factures_avec_echeance.prefetch_related("paiements"):
        dernier_paiement = facture.paiements.order_by("-date_paiement").first()
        if dernier_paiement and dernier_paiement.date_paiement <= facture.date_echeance:
            nb_dans_les_delais += 1
    taux_respect_echeances = (
        round(nb_dans_les_delais / factures_avec_echeance.count() * 100, 1)
        if factures_avec_echeance.count() else None
    )

    return {
        "nombre_fournisseurs_actifs": FournisseurComptable.objects.filter(actif=True).count(),
        "nombre_factures_recues": factures.count(),
        "nombre_factures_payees": factures_payees.count(),
        "montant_total_du": float(montant_du),
        "delai_moyen_paiement_jours": delai_moyen_paiement,
        "taux_respect_echeances": taux_respect_echeances,
    }


class FournisseurComptableViewSet(viewsets.ModelViewSet):
    queryset = FournisseurComptable.objects.all()
    serializer_class = FournisseurComptableSerializer
    permission_classes = [permissions.IsAuthenticated]


class FactureFournisseurViewSet(viewsets.ModelViewSet):
    queryset = FactureFournisseur.objects.select_related("fournisseur").all()
    serializer_class = FactureFournisseurSerializer
    permission_classes = [permissions.IsAuthenticated]


class PaiementFournisseurViewSet(viewsets.ModelViewSet):
    queryset = PaiementFournisseur.objects.select_related("facture_fournisseur").all()
    serializer_class = PaiementFournisseurSerializer
    permission_classes = [permissions.IsAuthenticated]


class FournisseursKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(compute_fournisseurs_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
