from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission

from .models import ContreVisiteDMCT, InspectionDMCT
from .serializers import ContreVisiteDMCTSerializer, InspectionDMCTSerializer

DMCT_ENCADREMENT = direction_permission('DMCT', min_tier='encadrement')
DMCT_MEMBRE = direction_permission('DMCT')


def compute_inspections_kpis(date_debut=None, date_fin=None):
    """Calcule les 7 KPI Inspections & controles techniques (categorie 6) de
    la DMCT. Reutilisable directement par le tableau de bord DMCT."""
    inspections = InspectionDMCT.objects.all()
    if date_debut and date_fin:
        inspections = inspections.filter(date_inspection__range=(date_debut, date_fin))

    contre_visites = ContreVisiteDMCT.objects.all()
    if date_debut and date_fin:
        contre_visites = contre_visites.filter(date_contre_visite__range=(date_debut, date_fin))

    evaluees = inspections.filter(conforme__isnull=False)
    taux_conformite = (
        round(evaluees.filter(conforme=True).count() / evaluees.count() * 100, 1) if evaluees.count() else None
    )

    cloturees = inspections.filter(date_cloture__isnull=False)
    delais_cloture = [(i.date_cloture - i.date_inspection).days for i in cloturees]
    delai_moyen_cloture = round(sum(delais_cloture) / len(delais_cloture), 1) if delais_cloture else None

    return {
        "nombre_inspections_realisees": inspections.filter(categorie="INSPECTION").count(),
        "nombre_controles_techniques_effectues": inspections.filter(categorie="CONTROLE_TECHNIQUE").count(),
        "nombre_controles_inopines": inspections.filter(type_controle="INOPINE").count(),
        "taux_conformite_etablissements": taux_conformite,
        "nombre_sanctions_observations": inspections.filter(sanction_emise=True).count(),
        "nombre_contre_visites": contre_visites.count(),
        "delai_moyen_cloture_inspection_jours": delai_moyen_cloture,
    }


class InspectionDMCTViewSet(viewsets.ModelViewSet):
    queryset = InspectionDMCT.objects.select_related("etablissement").all()
    serializer_class = InspectionDMCTSerializer
    permission_classes = [DMCT_ENCADREMENT]


class ContreVisiteDMCTViewSet(viewsets.ModelViewSet):
    queryset = ContreVisiteDMCT.objects.select_related("inspection").all()
    serializer_class = ContreVisiteDMCTSerializer
    permission_classes = [DMCT_ENCADREMENT]


class InspectionsKPIView(APIView):
    permission_classes = [DMCT_MEMBRE]

    def get(self, request):
        return Response(compute_inspections_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
