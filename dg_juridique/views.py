from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission, scope_dg_service_queryset

from .models import (
    AvisJuridique,
    Contentieux,
    Contrat,
    DossierJuridique,
    ProcedureDisciplinaire,
    TexteReglementaire,
)
from .serializers import (
    AvisJuridiqueSerializer,
    ContentieuxSerializer,
    ContratSerializer,
    DossierJuridiqueSerializer,
    ProcedureDisciplinaireSerializer,
    TexteReglementaireSerializer,
)


def compute_juridique_kpis(date_debut=None, date_fin=None, request=None):
    """Calcule les 12 KPI Juridique. Reutilisable directement par le dashboard DG.
    Si `request` est fourni, restreint au meme perimetre (Service + proprietaire)
    que les listes CRUD de l'utilisateur courant."""
    dossiers = DossierJuridique.objects.all()
    contrats = Contrat.objects.all()
    contentieux = Contentieux.objects.all()
    avis = AvisJuridique.objects.all()
    procedures = ProcedureDisciplinaire.objects.all()
    textes_qs = TexteReglementaire.objects.all()
    if request is not None:
        dossiers = scope_dg_service_queryset(dossiers, request, 'Juridique', owner_field='responsable')
        contrats = scope_dg_service_queryset(contrats, request, 'Juridique', owner_field='dossier__responsable')
        contentieux = scope_dg_service_queryset(contentieux, request, 'Juridique', owner_field='dossier__responsable')
        avis = scope_dg_service_queryset(avis, request, 'Juridique', owner_field='demandeur')
        procedures = scope_dg_service_queryset(procedures, request, 'Juridique')
        textes_qs = scope_dg_service_queryset(textes_qs, request, 'Juridique', owner_field='analyse_par')

    if date_debut and date_fin:
        dossiers = dossiers.filter(date_ouverture__range=(date_debut, date_fin))

    dossiers_clotures = dossiers.filter(statut="CLOTURE", date_cloture__isnull=False)
    delai_moyen = None
    if dossiers_clotures.exists():
        delais = [(d.date_cloture - d.date_ouverture).days for d in dossiers_clotures]
        delai_moyen = round(sum(delais) / len(delais), 1)

    nb_contentieux_total = contentieux.count()
    nb_contentieux_clotures = contentieux.filter(statut="CLOTURE").count()
    nb_contentieux_evites = contentieux.filter(statut="EVITE").count()
    taux_resolution = (
        round((nb_contentieux_clotures + nb_contentieux_evites) / nb_contentieux_total * 100, 1)
        if nb_contentieux_total else None
    )

    nb_contrats_total = contrats.count()
    nb_contrats_en_vigueur = contrats.filter(statut__in=["VALIDE", "SIGNE", "RENOUVELE"]).count()
    taux_conformite_juridique = (
        round(nb_contrats_en_vigueur / nb_contrats_total * 100, 1) if nb_contrats_total else None
    )

    return {
        "nombre_dossiers_traites": dossiers.filter(statut="CLOTURE").count(),
        "nombre_contrats_rediges": nb_contrats_total,
        "nombre_contrats_valides": nb_contrats_en_vigueur,
        "nombre_contrats_renouveles": contrats.filter(statut="RENOUVELE").count(),
        "nombre_contentieux_en_cours": contentieux.filter(statut="EN_COURS").count(),
        "nombre_contentieux_clotures": nb_contentieux_clotures,
        "delai_moyen_traitement_dossiers_jours": delai_moyen,
        "nombre_avis_rendus": avis.filter(date_reponse__isnull=False).count(),
        "nombre_consultations_juridiques": avis.count(),
        "nombre_litiges_evites": nb_contentieux_evites,
        "nombre_procedures_disciplinaires_traitees": procedures.filter(statut="CLOTUREE").count(),
        "taux_resolution_litiges": taux_resolution,
        "taux_conformite_juridique": taux_conformite_juridique,
        "nombre_textes_reglementaires_analyses": textes_qs.count(),
    }


DG_JURIDIQUE_MEMBRE = direction_permission('DG_JURIDIQUE')


class DossierJuridiqueViewSet(viewsets.ModelViewSet):
    queryset = DossierJuridique.objects.all()
    serializer_class = DossierJuridiqueSerializer
    permission_classes = [DG_JURIDIQUE_MEMBRE]

    def get_queryset(self):
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Juridique', owner_field='responsable')


class ContratViewSet(viewsets.ModelViewSet):
    queryset = Contrat.objects.select_related("dossier").all()
    serializer_class = ContratSerializer
    permission_classes = [DG_JURIDIQUE_MEMBRE]

    def get_queryset(self):
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Juridique', owner_field='dossier__responsable')


class ContentieuxViewSet(viewsets.ModelViewSet):
    queryset = Contentieux.objects.select_related("dossier").all()
    serializer_class = ContentieuxSerializer
    permission_classes = [DG_JURIDIQUE_MEMBRE]

    def get_queryset(self):
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Juridique', owner_field='dossier__responsable')


class AvisJuridiqueViewSet(viewsets.ModelViewSet):
    queryset = AvisJuridique.objects.select_related("dossier", "demandeur").all()
    serializer_class = AvisJuridiqueSerializer
    permission_classes = [DG_JURIDIQUE_MEMBRE]

    def get_queryset(self):
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Juridique', owner_field='demandeur')


class ProcedureDisciplinaireViewSet(viewsets.ModelViewSet):
    queryset = ProcedureDisciplinaire.objects.select_related("agent_concerne").all()
    serializer_class = ProcedureDisciplinaireSerializer
    permission_classes = [DG_JURIDIQUE_MEMBRE]

    def get_queryset(self):
        # Pas de champ "responsable du traitement" distinct de l'agent
        # concerné (le sujet de la procédure) : cloisonnement par Service
        # uniquement, pas de restriction par propriétaire.
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Juridique')


class TexteReglementaireViewSet(viewsets.ModelViewSet):
    queryset = TexteReglementaire.objects.select_related("dossier", "analyse_par").all()
    serializer_class = TexteReglementaireSerializer
    permission_classes = [DG_JURIDIQUE_MEMBRE]

    def get_queryset(self):
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Juridique', owner_field='analyse_par')


class JuridiqueKPIView(APIView):
    permission_classes = [DG_JURIDIQUE_MEMBRE]

    def get(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")
        return Response(compute_juridique_kpis(date_debut, date_fin, request=request))


class JuridiqueDashboardDirecteurView(APIView):
    """Vue condensee Directeur : pilotage strategique juridique (resolution, risques, echeances contractuelles)."""

    permission_classes = [DG_JURIDIQUE_MEMBRE]

    def get(self, request):
        kpis = compute_juridique_kpis()
        today = timezone.now().date()
        echeance = today + timedelta(days=60)
        contrats_expirant_bientot = Contrat.objects.filter(
            date_expiration__gte=today, date_expiration__lte=echeance
        ).count()

        return Response({
            "nombre_dossiers_traites": kpis["nombre_dossiers_traites"],
            "taux_resolution_litiges": kpis["taux_resolution_litiges"],
            "taux_conformite_juridique": kpis["taux_conformite_juridique"],
            "nombre_contentieux_en_cours": kpis["nombre_contentieux_en_cours"],
            "contrats_expirant_sous_60_jours": contrats_expirant_bientot,
            "delai_moyen_traitement_dossiers_jours": kpis["delai_moyen_traitement_dossiers_jours"],
            "nombre_procedures_disciplinaires_traitees": kpis["nombre_procedures_disciplinaires_traitees"],
            "nombre_avis_rendus": kpis["nombre_avis_rendus"],
            "nombre_litiges_evites": kpis["nombre_litiges_evites"],
        })


class JuridiqueDashboardChefServiceView(APIView):
    """Vue condensee Chef de service : suivi operationnel (dossiers ouverts, contrats a valider, charge par responsable)."""

    permission_classes = [DG_JURIDIQUE_MEMBRE]

    def get(self, request):
        dossiers_ouverts = DossierJuridique.objects.exclude(statut="CLOTURE")
        contrats_a_valider = Contrat.objects.filter(statut="BROUILLON")
        avis_en_attente = AvisJuridique.objects.filter(date_reponse__isnull=True)

        charge_par_responsable = list(
            dossiers_ouverts.exclude(responsable__isnull=True)
            .values("responsable__username")
            .annotate(nb=Count("id"))
            .order_by("-nb")
        )

        contentieux_en_cours = list(
            Contentieux.objects.filter(statut="EN_COURS").order_by("-date_ouverture")[:10].values(
                "reference", "partie_adverse", "objet", "date_ouverture"
            )
        )

        return Response({
            "nombre_dossiers_ouverts": dossiers_ouverts.count(),
            "nombre_contrats_a_valider": contrats_a_valider.count(),
            "nombre_avis_en_attente": avis_en_attente.count(),
            "charge_dossiers_par_responsable": charge_par_responsable,
            "contentieux_en_cours": contentieux_en_cours,
        })
