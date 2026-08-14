from django.db.models import Sum
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from aero_maintenance.models import OrdreTravail
from core.direction_access import direction_permission

from .models import FactureDAE
from .serializers import FactureDAESerializer

# Les factures elles-mêmes sont réservées au palier "direction" (Admin/
# Directeur uniquement). L'agrégat KPI reste ouvert à tout membre DAE, comme
# les autres endpoints KPI, pour ne pas casser le tableau de bord DAE existant
# (qui interroge toutes les catégories, y compris financiers, en une fois).
DAE_DIRECTION = direction_permission('DAE', feature_key='dae_view_finance')
DAE_MEMBRE = direction_permission('DAE')


def compute_financiers_kpis(date_debut=None, date_fin=None):
    """Calcule les 6 KPI Financiers (categorie 10) de la DAE. Reutilisable
    directement par le tableau de bord DAE."""
    factures = FactureDAE.objects.all()
    if date_debut and date_fin:
        factures = factures.filter(date_emission__range=(date_debut, date_fin))

    ca_prestations = float(factures.filter(statut="PAYEE").aggregate(t=Sum("montant_ttc"))["t"] or 0)

    ordres = OrdreTravail.objects.all()
    if date_debut and date_fin:
        ordres = ordres.filter(date_demande__date__range=(date_debut, date_fin))
    termines = ordres.filter(statut="TERMINE").select_related("piece_utilisee")

    couts_ordres = [float(o.piece_utilisee.prix_unitaire) for o in termines if o.piece_utilisee]
    cout_moyen_intervention = round(sum(couts_ordres) / len(couts_ordres), 2) if couts_ordres else None
    cout_total = sum(couts_ordres)

    cout_par_type = {}
    for type_code, _ in OrdreTravail.TYPE_CHOICES:
        ordres_type = termines.filter(type_intervention=type_code, piece_utilisee__isnull=False)
        cout_par_type[type_code] = round(
            sum(float(o.piece_utilisee.prix_unitaire) for o in ordres_type), 2
        )

    rentabilite = round(ca_prestations - cout_total, 2)

    nb_termines = termines.count()
    taux_facturation = round(factures.count() / nb_termines * 100, 1) if nb_termines else None

    total_factures = factures.count()
    taux_recouvrement = (
        round(factures.filter(statut="PAYEE").count() / total_factures * 100, 1) if total_factures else None
    )

    return {
        "ca_prestations": ca_prestations,
        "cout_moyen_intervention": cout_moyen_intervention,
        "cout_maintenance_par_type_note": (
            "Repartition par type d'intervention (preventive/corrective/urgence) : "
            "aucun cout dedie par equipement (roue/batterie/atelier) n'est trace individuellement."
        ),
        "cout_maintenance_par_type": cout_par_type,
        "rentabilite": rentabilite,
        "taux_facturation": taux_facturation,
        "taux_recouvrement": taux_recouvrement,
    }


class FactureDAEViewSet(viewsets.ModelViewSet):
    queryset = FactureDAE.objects.select_related("client", "ordre_travail").all()
    serializer_class = FactureDAESerializer
    permission_classes = [DAE_DIRECTION]


class FinanciersKPIView(APIView):
    permission_classes = [DAE_MEMBRE]

    def get(self, request):
        return Response(compute_financiers_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
