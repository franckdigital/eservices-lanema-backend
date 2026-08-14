from django.db.models import Avg
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission

from .models import AmeliorationProgramme, AuditDFIR, ReclamationDFIR
from .serializers import AmeliorationProgrammeSerializer, AuditDFIRSerializer, ReclamationDFIRSerializer

DFIR_ENCADREMENT = direction_permission('DFIR', min_tier='encadrement')
DFIR_MEMBRE = direction_permission('DFIR')


def compute_qualite_kpis(date_debut=None, date_fin=None):
    """Calcule les 6 KPI Qualite (categorie 7) de la DFIR. Reutilisable
    directement par le tableau de bord DFIR."""
    from dfir_formations.models import SessionFormation

    sessions = SessionFormation.objects.all()
    if date_debut and date_fin:
        sessions = sessions.filter(date_debut__date__range=(date_debut, date_fin))

    satisfaction_moyenne = sessions.filter(evaluation_session__isnull=False).aggregate(
        m=Avg("evaluation_session")
    )["m"]
    taux_satisfaction_global = (
        round(float(satisfaction_moyenne) / 5 * 100, 1) if satisfaction_moyenne is not None else None
    )

    reclamations = ReclamationDFIR.objects.all()
    if date_debut and date_fin:
        reclamations = reclamations.filter(date_reception__range=(date_debut, date_fin))
    total_reclamations = reclamations.count()
    taux_traitement = (
        round(reclamations.filter(statut="TRAITEE").count() / total_reclamations * 100, 1)
        if total_reclamations else None
    )

    ameliorations = AmeliorationProgramme.objects.all()
    if date_debut and date_fin:
        ameliorations = ameliorations.filter(date_mise_en_oeuvre__date__range=(date_debut, date_fin))

    sessions_avec_dates = sessions.filter(
        statut="TERMINEE", date_fin_reelle__isnull=False, date_fin_prevue__isnull=False
    )
    nb_dans_les_delais = sum(
        1 for s in sessions_avec_dates if s.date_fin_reelle <= s.date_fin_prevue
    )
    respect_calendrier = (
        round(nb_dans_les_delais / sessions_avec_dates.count() * 100, 1) if sessions_avec_dates.count() else None
    )

    audits = AuditDFIR.objects.all()
    if date_debut and date_fin:
        audits = audits.filter(date_audit__range=(date_debut, date_fin))
    total_audits = audits.count()
    taux_conformite_referentiels = (
        round(audits.filter(resultat="CONFORME").count() / total_audits * 100, 1) if total_audits else None
    )

    return {
        "taux_satisfaction_global_formations": taux_satisfaction_global,
        "nombre_reclamations": total_reclamations,
        "taux_traitement_reclamations": taux_traitement,
        "nombre_ameliorations_programmes": ameliorations.count(),
        "respect_calendrier_formations": respect_calendrier,
        "taux_conformite_referentiels_qualite": taux_conformite_referentiels,
    }


class ReclamationDFIRViewSet(viewsets.ModelViewSet):
    queryset = ReclamationDFIR.objects.select_related("entreprise", "participant").all()
    serializer_class = ReclamationDFIRSerializer
    permission_classes = [DFIR_ENCADREMENT]


class AmeliorationProgrammeViewSet(viewsets.ModelViewSet):
    queryset = AmeliorationProgramme.objects.select_related("formation").all()
    serializer_class = AmeliorationProgrammeSerializer
    permission_classes = [DFIR_ENCADREMENT]


class AuditDFIRViewSet(viewsets.ModelViewSet):
    queryset = AuditDFIR.objects.all()
    serializer_class = AuditDFIRSerializer
    permission_classes = [DFIR_ENCADREMENT]


class QualiteKPIView(APIView):
    permission_classes = [DFIR_MEMBRE]

    def get(self, request):
        return Response(compute_qualite_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
