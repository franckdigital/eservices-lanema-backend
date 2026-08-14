from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission

from .models import DemandeDMCT
from .serializers import DemandeDMCTSerializer

# Enregistrement des demandes clients : encadrement DMCT et plus (accueil/
# planification), pas le palier "terrain" (leur page est Prestations).
DMCT_ENCADREMENT = direction_permission('DMCT', min_tier='encadrement')
DMCT_MEMBRE = direction_permission('DMCT')


def compute_demandes_kpis(date_debut=None, date_fin=None):
    """Calcule les 6 KPI de reception des demandes de la DMCT. Reutilisable
    directement par le tableau de bord DMCT."""
    demandes = DemandeDMCT.objects.all()
    if date_debut and date_fin:
        demandes = demandes.filter(date_demande__date__range=(date_debut, date_fin))

    prises_en_charge = demandes.filter(date_prise_charge__isnull=False)
    delais = [(d.date_prise_charge - d.date_demande).total_seconds() / 3600 for d in prises_en_charge]
    temps_moyen_prise_en_charge = round(sum(delais) / len(delais), 1) if delais else None

    demandes_avec_limite = demandes.filter(date_limite_prise_charge__isnull=False, date_prise_charge__isnull=False)
    nb_dans_les_delais = sum(
        1 for d in demandes_avec_limite if d.date_prise_charge <= d.date_limite_prise_charge
    )
    taux_prise_en_charge_delais = (
        round(nb_dans_les_delais / demandes_avec_limite.count() * 100, 1) if demandes_avec_limite.count() else None
    )

    return {
        "nombre_demandes_verification": demandes.filter(type_demande="VERIFICATION").count(),
        "nombre_demandes_etalonnage": demandes.filter(type_demande="ETALONNAGE").count(),
        "nombre_demandes_enregistrees": demandes.filter(date_enregistrement__isnull=False).count(),
        "nombre_demandes_en_attente": demandes.filter(statut="EN_ATTENTE").count(),
        "temps_moyen_prise_en_charge_heures": temps_moyen_prise_en_charge,
        "taux_prise_en_charge_delais": taux_prise_en_charge_delais,
    }


class DemandeDMCTViewSet(viewsets.ModelViewSet):
    queryset = DemandeDMCT.objects.select_related("client").all()
    serializer_class = DemandeDMCTSerializer
    permission_classes = [DMCT_ENCADREMENT]


class DemandesKPIView(APIView):
    permission_classes = [DMCT_MEMBRE]

    def get(self, request):
        return Response(compute_demandes_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
