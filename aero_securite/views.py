from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission

from .models import ControleReglementaire, EcartReglementaire, FormationSecurite, IncidentTechnique, RapportSecurite
from .serializers import (
    ControleReglementaireSerializer,
    EcartReglementaireSerializer,
    FormationSecuriteSerializer,
    IncidentTechniqueSerializer,
    RapportSecuriteSerializer,
)


def compute_securite_kpis(date_debut=None, date_fin=None):
    """Calcule les 7 KPI Securite aeronautique / conformite ANAC (categorie 5)
    de la DAE. Reutilisable directement par le tableau de bord DAE."""
    incidents = IncidentTechnique.objects.all()
    if date_debut and date_fin:
        incidents = incidents.filter(date_incident__range=(date_debut, date_fin))

    ecarts = EcartReglementaire.objects.all()
    if date_debut and date_fin:
        ecarts = ecarts.filter(date_constat__range=(date_debut, date_fin))

    rapports = RapportSecurite.objects.all()
    if date_debut and date_fin:
        rapports = rapports.filter(date_creation__range=(date_debut, date_fin))

    controles = ControleReglementaire.objects.all()
    if date_debut and date_fin:
        controles = controles.filter(date_controle__range=(date_debut, date_fin))

    formations = FormationSecurite.objects.all()
    if date_debut and date_fin:
        formations = formations.filter(date_formation__range=(date_debut, date_fin))

    total_controles = controles.count()
    nb_reussis = controles.filter(resultat="REUSSI").count()
    taux_conformite_anac = round(nb_reussis / total_controles * 100, 1) if total_controles else None

    return {
        "nombre_incidents_techniques": incidents.count(),
        "nombre_accidents": incidents.filter(est_accident=True).count(),
        "nombre_ecarts_reglementaires": ecarts.count(),
        "nombre_rapports_securite": rapports.count(),
        "taux_conformite_anac": taux_conformite_anac,
        "nombre_controles_reussis": nb_reussis,
        "nombre_formations_realisees": formations.count(),
    }


DAE_ENCADREMENT = direction_permission('DAE', min_tier='encadrement')
DAE_MEMBRE = direction_permission('DAE')


class IncidentTechniqueViewSet(viewsets.ModelViewSet):
    queryset = IncidentTechnique.objects.select_related("ordre_travail").all()
    serializer_class = IncidentTechniqueSerializer
    permission_classes = [DAE_ENCADREMENT]


class EcartReglementaireViewSet(viewsets.ModelViewSet):
    queryset = EcartReglementaire.objects.all()
    serializer_class = EcartReglementaireSerializer
    permission_classes = [DAE_ENCADREMENT]


class RapportSecuriteViewSet(viewsets.ModelViewSet):
    queryset = RapportSecurite.objects.all()
    serializer_class = RapportSecuriteSerializer
    permission_classes = [DAE_ENCADREMENT]


class ControleReglementaireViewSet(viewsets.ModelViewSet):
    queryset = ControleReglementaire.objects.all()
    serializer_class = ControleReglementaireSerializer
    permission_classes = [DAE_ENCADREMENT]


class FormationSecuriteViewSet(viewsets.ModelViewSet):
    queryset = FormationSecurite.objects.all()
    serializer_class = FormationSecuriteSerializer
    permission_classes = [DAE_ENCADREMENT]


class SecuriteKPIView(APIView):
    permission_classes = [DAE_MEMBRE]

    def get(self, request):
        return Response(compute_securite_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
