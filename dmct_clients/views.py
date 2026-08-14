from django.db.models import Avg, Count
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission

from .models import ClientDMCT, ReclamationClientDMCT
from .serializers import ClientDMCTSerializer, ReclamationClientDMCTSerializer

DMCT_ENCADREMENT = direction_permission('DMCT', min_tier='encadrement')
DMCT_MEMBRE = direction_permission('DMCT')


def compute_clients_kpis(date_debut=None, date_fin=None):
    """Calcule les 6 KPI clients de la DMCT. Reutilisable directement par le
    tableau de bord DMCT."""
    from dmct_prestations.models import PrestationDMCT

    prestations = PrestationDMCT.objects.all()
    if date_debut and date_fin:
        prestations = prestations.filter(date_debut__date__range=(date_debut, date_fin))

    clients_servis_ids = prestations.exclude(demande__isnull=True).values_list(
        "demande__client_id", flat=True
    ).distinct()
    nombre_clients_servis = len(set(clients_servis_ids))

    nouveaux_clients = ClientDMCT.objects.all()
    if date_debut and date_fin:
        nouveaux_clients = nouveaux_clients.filter(created_at__date__range=(date_debut, date_fin))

    reclamations = ReclamationClientDMCT.objects.all()
    if date_debut and date_fin:
        reclamations = reclamations.filter(date_reception__range=(date_debut, date_fin))

    satisfaction_moyenne = reclamations.filter(note_satisfaction__isnull=False).aggregate(
        m=Avg("note_satisfaction")
    )["m"]
    taux_satisfaction = round(float(satisfaction_moyenne) / 5 * 100, 1) if satisfaction_moyenne is not None else None

    reclamations_traitees = reclamations.filter(date_traitement__isnull=False)
    temps_moyen_traitement = None
    if reclamations_traitees.exists():
        delais = [(r.date_traitement - r.date_reception).days for r in reclamations_traitees]
        temps_moyen_traitement = round(sum(delais) / len(delais), 1)

    counts_par_client = (
        prestations.exclude(demande__isnull=True)
        .values("demande__client_id")
        .annotate(nb=Count("id"))
    )
    nb_clients_fideles = sum(1 for c in counts_par_client if c["nb"] > 1)
    taux_fidelisation = (
        round(nb_clients_fideles / nombre_clients_servis * 100, 1) if nombre_clients_servis else None
    )

    return {
        "nombre_clients_servis": nombre_clients_servis,
        "nombre_nouveaux_clients": nouveaux_clients.count(),
        "taux_satisfaction_clients": taux_satisfaction,
        "nombre_reclamations": reclamations.count(),
        "temps_moyen_traitement_reclamations_jours": temps_moyen_traitement,
        "taux_fidelisation_clients": taux_fidelisation,
    }


class ClientDMCTViewSet(viewsets.ModelViewSet):
    queryset = ClientDMCT.objects.all()
    serializer_class = ClientDMCTSerializer
    permission_classes = [DMCT_ENCADREMENT]


class ReclamationClientDMCTViewSet(viewsets.ModelViewSet):
    queryset = ReclamationClientDMCT.objects.select_related("client").all()
    serializer_class = ReclamationClientDMCTSerializer
    permission_classes = [DMCT_ENCADREMENT]


class ClientsKPIView(APIView):
    permission_classes = [DMCT_MEMBRE]

    def get(self, request):
        return Response(compute_clients_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
