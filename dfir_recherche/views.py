from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    CollaborationRecherche,
    ProjetRecherche,
    PublicationScientifique,
    RapportRecherche,
    RecommandationRecherche,
)
from core.direction_access import direction_permission

from .serializers import (
    CollaborationRechercheSerializer,
    ProjetRechercheSerializer,
    PublicationScientifiqueSerializer,
    RapportRechercheSerializer,
    RecommandationRechercheSerializer,
)

DFIR_ENCADREMENT = direction_permission('DFIR', min_tier='encadrement')
DFIR_MEMBRE = direction_permission('DFIR')


def compute_recherche_kpis(date_debut=None, date_fin=None):
    """Calcule les 8 KPI Recherche (categorie 5) de la DFIR. Reutilisable
    directement par le tableau de bord DFIR."""
    projets = ProjetRecherche.objects.all()
    if date_debut and date_fin:
        projets = projets.filter(date_debut__date__range=(date_debut, date_fin))

    publications = PublicationScientifique.objects.all()
    if date_debut and date_fin:
        publications = publications.filter(date_publication__range=(date_debut, date_fin))

    rapports = RapportRecherche.objects.all()
    if date_debut and date_fin:
        rapports = rapports.filter(date_creation__range=(date_debut, date_fin))

    recommandations = RecommandationRecherche.objects.all()

    collaborations = CollaborationRecherche.objects.all()
    if date_debut and date_fin:
        collaborations = collaborations.filter(date_debut__range=(date_debut, date_fin))

    total_projets = projets.count()
    taux_realisation = (
        round(projets.filter(statut="ACHEVE").count() / total_projets * 100, 1) if total_projets else None
    )

    return {
        "nombre_projets_recherche": total_projets,
        "nombre_etudes_techniques": projets.filter(type_projet="ETUDE_TECHNIQUE").count(),
        "nombre_etudes_entreprises": projets.filter(type_projet="ETUDE_ENTREPRISE").count(),
        "nombre_publications": publications.count(),
        "nombre_rapports_valides": rapports.filter(valide=True).count(),
        "nombre_recommandations_appliquees": recommandations.filter(appliquee=True).count(),
        "nombre_collaborations": collaborations.count(),
        "taux_realisation_projets_recherche": taux_realisation,
    }


class ProjetRechercheViewSet(viewsets.ModelViewSet):
    queryset = ProjetRecherche.objects.select_related("entreprise").all()
    serializer_class = ProjetRechercheSerializer
    permission_classes = [DFIR_ENCADREMENT]


class PublicationScientifiqueViewSet(viewsets.ModelViewSet):
    queryset = PublicationScientifique.objects.select_related("projet").all()
    serializer_class = PublicationScientifiqueSerializer
    permission_classes = [DFIR_ENCADREMENT]


class RapportRechercheViewSet(viewsets.ModelViewSet):
    queryset = RapportRecherche.objects.select_related("projet").all()
    serializer_class = RapportRechercheSerializer
    permission_classes = [DFIR_ENCADREMENT]


class RecommandationRechercheViewSet(viewsets.ModelViewSet):
    queryset = RecommandationRecherche.objects.select_related("rapport").all()
    serializer_class = RecommandationRechercheSerializer
    permission_classes = [DFIR_ENCADREMENT]


class CollaborationRechercheViewSet(viewsets.ModelViewSet):
    queryset = CollaborationRecherche.objects.all()
    serializer_class = CollaborationRechercheSerializer
    permission_classes = [DFIR_ENCADREMENT]


class RechercheKPIView(APIView):
    permission_classes = [DFIR_MEMBRE]

    def get(self, request):
        return Response(compute_recherche_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
