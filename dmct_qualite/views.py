from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from dmct_prestations.models import PrestationDMCT
from core.direction_access import direction_permission

from .models import ActionCorrectiveDMCT, AuditDMCT, NonConformiteDMCT
from .serializers import ActionCorrectiveDMCTSerializer, AuditDMCTSerializer, NonConformiteDMCTSerializer

DMCT_ENCADREMENT = direction_permission('DMCT', min_tier='encadrement')
DMCT_MEMBRE = direction_permission('DMCT')


def compute_qualite_kpis(date_debut=None, date_fin=None):
    """Calcule les 7 KPI Qualite (categorie 4) de la DMCT. Reutilisable
    directement par le tableau de bord DMCT."""
    non_conformites = NonConformiteDMCT.objects.all()
    if date_debut and date_fin:
        non_conformites = non_conformites.filter(date_creation__range=(date_debut, date_fin))

    actions = ActionCorrectiveDMCT.objects.all()
    if date_debut and date_fin:
        actions = actions.filter(date_prevue__range=(date_debut, date_fin))

    audits = AuditDMCT.objects.all()
    if date_debut and date_fin:
        audits = audits.filter(date_audit__range=(date_debut, date_fin))

    total_actions = actions.count()
    taux_cloture_actions = (
        round(actions.filter(statut="REALISEE").count() / total_actions * 100, 1) if total_actions else None
    )

    total_audits = audits.count()
    taux_conformite_procedures = (
        round(audits.filter(resultat="CONFORME").count() / total_audits * 100, 1) if total_audits else None
    )

    audits_iso = audits.filter(type_audit__icontains="17025")
    total_audits_iso = audits_iso.count()
    taux_conformite_iso = (
        round(audits_iso.filter(resultat="CONFORME").count() / total_audits_iso * 100, 1)
        if total_audits_iso else None
    )

    prestations_terminees = PrestationDMCT.objects.filter(statut="TERMINEE")
    if date_debut and date_fin:
        prestations_terminees = prestations_terminees.filter(date_fin__date__range=(date_debut, date_fin))
    total_prestations = prestations_terminees.count()
    prestations_sans_nc = prestations_terminees.exclude(non_conformites__isnull=False).distinct().count()
    taux_fiabilite_resultats = (
        round(prestations_sans_nc / total_prestations * 100, 1) if total_prestations else None
    )

    return {
        "nombre_non_conformites": non_conformites.count(),
        "nombre_actions_correctives": total_actions,
        "taux_cloture_actions_correctives": taux_cloture_actions,
        "nombre_audits_internes": total_audits,
        "taux_conformite_procedures": taux_conformite_procedures,
        "taux_conformite_iso_17025": taux_conformite_iso,
        "taux_fiabilite_resultats": taux_fiabilite_resultats,
    }


class NonConformiteDMCTViewSet(viewsets.ModelViewSet):
    queryset = NonConformiteDMCT.objects.select_related("prestation", "responsable").all()
    serializer_class = NonConformiteDMCTSerializer
    permission_classes = [DMCT_ENCADREMENT]


class ActionCorrectiveDMCTViewSet(viewsets.ModelViewSet):
    queryset = ActionCorrectiveDMCT.objects.select_related("non_conformite", "responsable").all()
    serializer_class = ActionCorrectiveDMCTSerializer
    permission_classes = [DMCT_ENCADREMENT]


class AuditDMCTViewSet(viewsets.ModelViewSet):
    queryset = AuditDMCT.objects.all()
    serializer_class = AuditDMCTSerializer
    permission_classes = [DMCT_ENCADREMENT]


class QualiteKPIView(APIView):
    permission_classes = [DMCT_MEMBRE]

    def get(self, request):
        return Response(compute_qualite_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
