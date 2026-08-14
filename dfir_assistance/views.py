from django.db.models import Avg
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission

from .models import MissionAssistance
from .serializers import MissionAssistanceSerializer

DFIR_ENCADREMENT = direction_permission('DFIR', min_tier='encadrement')
DFIR_MEMBRE = direction_permission('DFIR')


def compute_assistance_kpis(date_debut=None, date_fin=None):
    """Calcule les 6 KPI Assistance technique (categorie 6) de la DFIR.
    Reutilisable directement par le tableau de bord DFIR."""
    missions = MissionAssistance.objects.all()
    if date_debut and date_fin:
        missions = missions.filter(date_demande__date__range=(date_debut, date_fin))

    satisfaction_moyenne = missions.filter(satisfaction__isnull=False).aggregate(m=Avg("satisfaction"))["m"]
    taux_satisfaction = round(float(satisfaction_moyenne) / 5 * 100, 1) if satisfaction_moyenne is not None else None

    terminees = missions.filter(statut="TERMINEE", date_fin__isnull=False)
    delais = [(m.date_fin - m.date_demande).days for m in terminees]
    temps_moyen = round(sum(delais) / len(delais), 1) if delais else None

    return {
        "nombre_missions": missions.count(),
        "nombre_entreprises_accompagnees": missions.values("entreprise").distinct().count(),
        "nombre_diagnostics_realises": missions.filter(diagnostic_realise=True).count(),
        "nombre_plans_amelioration": missions.filter(plan_amelioration_elabore=True).count(),
        "taux_satisfaction_entreprises": taux_satisfaction,
        "temps_moyen_traitement_jours": temps_moyen,
    }


class MissionAssistanceViewSet(viewsets.ModelViewSet):
    queryset = MissionAssistance.objects.select_related("entreprise").all()
    serializer_class = MissionAssistanceSerializer
    permission_classes = [DFIR_ENCADREMENT]


class AssistanceKPIView(APIView):
    permission_classes = [DFIR_MEMBRE]

    def get(self, request):
        return Response(compute_assistance_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
