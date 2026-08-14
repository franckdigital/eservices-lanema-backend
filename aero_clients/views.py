from django.db.models import Avg
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission

from .models import Aeronef, ClientAeronautique, ReclamationClientDAE
from .serializers import AeronefSerializer, ClientAeronautiqueSerializer, ReclamationClientDAESerializer

# Gestion des clients aéronautiques : réservée à l'encadrement DAE et plus
# (Admin/Directeur/Sous-Directeur/Chef d'atelier) — palier "terrain" exclu.
DAE_ENCADREMENT = direction_permission('DAE', min_tier='encadrement')
DAE_MEMBRE = direction_permission('DAE')


def compute_clients_kpis(date_debut=None, date_fin=None):
    """Calcule les 6 KPI clients de la DAE. Reutilisable directement par le
    tableau de bord DAE."""
    from aero_maintenance.models import OrdreTravail

    aeronefs = Aeronef.objects.all()
    ordres = OrdreTravail.objects.all()
    if date_debut and date_fin:
        ordres = ordres.filter(date_demande__date__range=(date_debut, date_fin))

    ordres_clotures = ordres.filter(statut="TERMINE", date_fin__isnull=False)
    delai_moyen_restitution = None
    if ordres_clotures.exists():
        delais = [
            (o.date_fin - o.date_demande.date()).days for o in ordres_clotures
        ]
        delai_moyen_restitution = round(sum(delais) / len(delais), 1)

    reclamations = ReclamationClientDAE.objects.all()
    if date_debut and date_fin:
        reclamations = reclamations.filter(date_reception__range=(date_debut, date_fin))

    satisfaction_moyenne = reclamations.filter(note_satisfaction__isnull=False).aggregate(
        m=Avg("note_satisfaction")
    )["m"]
    taux_satisfaction = round(float(satisfaction_moyenne) / 5 * 100, 1) if satisfaction_moyenne is not None else None

    reclamations_traitees = reclamations.filter(date_traitement__isnull=False)
    temps_moyen_traitement = None
    if reclamations_traitees.exists():
        delais_r = [(r.date_traitement - r.date_reception).days for r in reclamations_traitees]
        temps_moyen_traitement = round(sum(delais_r) / len(delais_r), 1)

    return {
        "nombre_aeronefs_pris_en_charge": aeronefs.count(),
        "nombre_ordres_travail_clotures": ordres_clotures.count(),
        "delai_moyen_restitution_jours": delai_moyen_restitution,
        "taux_satisfaction_clients": taux_satisfaction,
        "nombre_reclamations": reclamations.count(),
        "temps_moyen_traitement_reclamations_jours": temps_moyen_traitement,
    }


class ClientAeronautiqueViewSet(viewsets.ModelViewSet):
    queryset = ClientAeronautique.objects.all()
    serializer_class = ClientAeronautiqueSerializer
    permission_classes = [DAE_ENCADREMENT]


class AeronefViewSet(viewsets.ModelViewSet):
    queryset = Aeronef.objects.select_related("client").all()
    serializer_class = AeronefSerializer
    permission_classes = [DAE_ENCADREMENT]


class ReclamationClientDAEViewSet(viewsets.ModelViewSet):
    queryset = ReclamationClientDAE.objects.select_related("client").all()
    serializer_class = ReclamationClientDAESerializer
    permission_classes = [DAE_ENCADREMENT]


class ClientsKPIView(APIView):
    permission_classes = [DAE_MEMBRE]

    def get(self, request):
        return Response(compute_clients_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
