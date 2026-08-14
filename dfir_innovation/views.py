from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission

from .models import ProjetInnovation
from .serializers import ProjetInnovationSerializer

DFIR_ENCADREMENT = direction_permission('DFIR', min_tier='encadrement')
DFIR_MEMBRE = direction_permission('DFIR')


def compute_innovation_kpis(date_debut=None, date_fin=None):
    """Calcule les 8 KPI Innovation (categorie 4) de la DFIR. Reutilisable
    directement par le tableau de bord DFIR."""
    projets = ProjetInnovation.objects.all()
    if date_debut and date_fin:
        projets = projets.filter(date_lancement__date__range=(date_debut, date_fin))

    acheves = projets.filter(statut="ACHEVE")
    abandonnes = projets.filter(statut="ABANDONNE")
    total_clotures = acheves.count() + abandonnes.count()
    taux_reussite = round(acheves.count() / total_clotures * 100, 1) if total_clotures else None

    acheves_avec_dates = acheves.filter(date_fin_reelle__isnull=False)
    delais = [(p.date_fin_reelle - p.date_lancement.date()).days for p in acheves_avec_dates]
    delai_moyen = round(sum(delais) / len(delais), 1) if delais else None

    return {
        "nombre_projets_lances": projets.count(),
        "nombre_projets_acheves": acheves.count(),
        "taux_reussite_projets": taux_reussite,
        "nombre_nouvelles_methodes": projets.filter(methode_developpee=True).count(),
        "nombre_prototypes_realises": projets.filter(prototype_realise=True).count(),
        "nombre_innovations_mises_en_oeuvre": projets.filter(mis_en_oeuvre=True).count(),
        "nombre_partenariats_innovation": projets.filter(partenariat=True).count(),
        "delai_moyen_realisation_projets_jours": delai_moyen,
    }


class ProjetInnovationViewSet(viewsets.ModelViewSet):
    queryset = ProjetInnovation.objects.all()
    serializer_class = ProjetInnovationSerializer
    permission_classes = [DFIR_ENCADREMENT]


class InnovationKPIView(APIView):
    permission_classes = [DFIR_MEMBRE]

    def get(self, request):
        return Response(compute_innovation_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
