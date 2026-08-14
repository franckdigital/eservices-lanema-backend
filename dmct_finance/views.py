from collections import Counter

from django.db.models import Avg, Sum
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from dmct_prestations.models import PrestationDMCT
from core.direction_access import direction_permission

from .models import FactureDMCT
from .serializers import FactureDMCTSerializer

# Les factures sont réservées au palier "direction" (Admin/Directeur). L'agrégat
# KPI reste ouvert à tout membre DMCT, comme les autres endpoints KPI, pour ne
# pas casser le tableau de bord DMCT existant.
DMCT_DIRECTION = direction_permission('DMCT', feature_key='dmct_view_finance')
DMCT_MEMBRE = direction_permission('DMCT')


def compute_financiers_kpis(date_debut=None, date_fin=None):
    """Calcule les 7 KPI Financiers (categorie 8) de la DMCT. Reutilisable
    directement par le tableau de bord DMCT."""
    factures = FactureDMCT.objects.all()
    if date_debut and date_fin:
        factures = factures.filter(date_emission__range=(date_debut, date_fin))

    factures_payees = factures.filter(statut="PAYEE")
    ca_prestations = float(factures_payees.aggregate(t=Sum("montant_ttc"))["t"] or 0)

    ca_par_secteur = Counter()
    for f in factures_payees.select_related("client"):
        ca_par_secteur[f.client.secteur_activite] += float(f.montant_ttc)

    prestations = PrestationDMCT.objects.all()
    if date_debut and date_fin:
        prestations = prestations.filter(date_debut__date__range=(date_debut, date_fin))

    cout_moyen_etalonnage = prestations.filter(
        type_prestation="ETALONNAGE", cout_revient__isnull=False
    ).aggregate(m=Avg("cout_revient"))["m"]
    cout_moyen_etalonnage = round(float(cout_moyen_etalonnage), 2) if cout_moyen_etalonnage is not None else None

    cout_moyen_verification = prestations.filter(
        type_prestation="VERIFICATION", cout_revient__isnull=False
    ).aggregate(m=Avg("cout_revient"))["m"]
    cout_moyen_verification = round(float(cout_moyen_verification), 2) if cout_moyen_verification is not None else None

    termines = prestations.filter(statut="TERMINEE")
    nb_termines = termines.count()
    taux_facturation = round(factures.count() / nb_termines * 100, 1) if nb_termines else None

    total_factures = factures.count()
    taux_recouvrement = (
        round(factures_payees.count() / total_factures * 100, 1) if total_factures else None
    )

    en_attente_facturation = termines.filter(factures__isnull=True).count()

    return {
        "chiffre_affaires_prestations": ca_prestations,
        "chiffre_affaires_par_secteur": dict(ca_par_secteur),
        "cout_moyen_etalonnage": cout_moyen_etalonnage,
        "cout_moyen_verification": cout_moyen_verification,
        "taux_facturation": taux_facturation,
        "taux_recouvrement": taux_recouvrement,
        "nombre_prestations_en_attente_facturation": en_attente_facturation,
    }


class FactureDMCTViewSet(viewsets.ModelViewSet):
    queryset = FactureDMCT.objects.select_related("client", "prestation").all()
    serializer_class = FactureDMCTSerializer
    permission_classes = [DMCT_DIRECTION]


class FinanciersKPIView(APIView):
    permission_classes = [DMCT_MEMBRE]

    def get(self, request):
        return Response(compute_financiers_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
