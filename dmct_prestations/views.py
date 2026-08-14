from collections import Counter

from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission, scope_queryset_to_owner, user_tier

from .models import PrestationDMCT
from .serializers import PrestationDMCTSerializer

# Page "Prestations" : seule page opérationnelle accessible au palier
# "terrain" (métrologue) — mais un métrologue ne voit/modifie que ses propres
# prestations (scope_queryset_to_owner ci-dessous).
DMCT_MEMBRE = direction_permission('DMCT')


def compute_prestations_kpis(date_debut=None, date_fin=None):
    """Calcule les 8 KPI Prestations (categorie 3) de la DMCT. Reutilisable
    directement par le tableau de bord DMCT."""
    prestations = PrestationDMCT.objects.all()
    if date_debut and date_fin:
        prestations = prestations.filter(date_debut__date__range=(date_debut, date_fin))

    termines = prestations.filter(statut="TERMINEE").select_related(
        "demande__client", "instrument__client"
    )

    secteurs = Counter()
    for p in termines:
        client = None
        if p.demande and p.demande.client:
            client = p.demande.client
        elif p.instrument and p.instrument.client:
            client = p.instrument.client
        if client:
            secteurs[client.secteur_activite] += 1

    avec_duree = termines.filter(date_debut__isnull=False, date_fin__isnull=False)
    durees = [(p.date_fin - p.date_debut).total_seconds() / 3600 for p in avec_duree]
    temps_moyen = round(sum(durees) / len(durees), 1) if durees else None

    avec_certificat = termines.filter(date_livraison_certificat__isnull=False, date_fin__isnull=False)
    delais_certificat = [(p.date_livraison_certificat - p.date_fin.date()).days for p in avec_certificat]
    delai_moyen_certificat = round(sum(delais_certificat) / len(delais_certificat), 1) if delais_certificat else None

    avec_sla = termines.filter(date_fin_prevue__isnull=False)
    nb_dans_delais = sum(1 for p in avec_sla if p.date_fin <= p.date_fin_prevue)
    taux_sla = round(nb_dans_delais / avec_sla.count() * 100, 1) if avec_sla.count() else None

    return {
        "nombre_total_prestations": termines.count(),
        "prestations_par_secteur": dict(secteurs),
        "nombre_prestations_sur_site": termines.filter(lieu="SUR_SITE").count(),
        "nombre_prestations_laboratoire": termines.filter(lieu="LABORATOIRE").count(),
        "temps_moyen_prestation_heures": temps_moyen,
        "delai_moyen_livraison_certificats_jours": delai_moyen_certificat,
        "taux_respect_delais_sla": taux_sla,
        "nombre_prestations_urgentes": termines.filter(urgent=True).count(),
    }


class PrestationDMCTViewSet(viewsets.ModelViewSet):
    queryset = PrestationDMCT.objects.select_related("demande", "instrument", "agent").all()
    serializer_class = PrestationDMCTSerializer
    permission_classes = [DMCT_MEMBRE]

    def get_queryset(self):
        return scope_queryset_to_owner(super().get_queryset(), self.request, "agent")

    def perform_create(self, serializer):
        if user_tier(self.request.user) == 'terrain' and not serializer.validated_data.get('agent'):
            serializer.save(agent=self.request.user)
        else:
            serializer.save()


class PrestationsKPIView(APIView):
    permission_classes = [DMCT_MEMBRE]

    def get(self, request):
        return Response(compute_prestations_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
