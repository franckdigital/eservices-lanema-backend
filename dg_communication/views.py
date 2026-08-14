from django.db.models import Avg, Count, Q, Sum
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission, scope_dg_service_queryset

from .models import ActionCommunication, Partenariat, Prospect, SatisfactionClient
from .serializers import (
    ActionCommunicationSerializer,
    PartenariatSerializer,
    ProspectSerializer,
    SatisfactionClientSerializer,
)


def compute_communication_kpis(date_debut=None, date_fin=None, request=None):
    """Calcule les 15 KPI Communication/Marketing. Reutilisable telle quelle
    par le tableau de bord DG (appel direct, pas de requete HTTP interne).
    Si `request` est fourni, les KPI sont restreints au meme perimetre
    (Service + proprietaire) que les listes CRUD de l'utilisateur courant —
    un agent Marketing voit ainsi ses propres KPI, pas ceux de tout le
    service."""
    actions = ActionCommunication.objects.all()
    prospects = Prospect.objects.all()
    partenariats_qs = Partenariat.objects.all()
    satisfaction_qs = SatisfactionClient.objects.all()
    if request is not None:
        actions = scope_dg_service_queryset(actions, request, 'Communication', owner_field='responsable')
        prospects = scope_dg_service_queryset(prospects, request, 'Marketing')
        partenariats_qs = scope_dg_service_queryset(partenariats_qs, request, 'Marketing', owner_field='responsable')
        satisfaction_qs = scope_dg_service_queryset(satisfaction_qs, request, 'Marketing')
    if date_debut and date_fin:
        actions = actions.filter(date_debut__range=(date_debut, date_fin))
        prospects = prospects.filter(date_creation__date__range=(date_debut, date_fin))

    realisees = actions.filter(statut="REALISEE")

    nb_campagnes = realisees.filter(type="CAMPAGNE").count()
    nb_communiques = realisees.filter(type="COMMUNIQUE").count()
    nb_evenements = realisees.filter(type="EVENEMENT").count()
    nb_salons = realisees.filter(type="SALON").count()
    nb_supports = realisees.filter(type="SUPPORT").count()

    nb_prospects = prospects.count()
    nb_nouveaux_clients = prospects.filter(statut="CONVERTI").count()
    taux_conversion = round(nb_nouveaux_clients / nb_prospects * 100, 1) if nb_prospects else 0

    ca_marketing = actions.aggregate(total=Sum("chiffre_affaires_genere"))["total"] or 0
    budget_total = actions.aggregate(total=Sum("budget"))["total"] or 0
    cout_acquisition = round(float(budget_total) / nb_nouveaux_clients, 2) if nb_nouveaux_clients else None
    roi = round((float(ca_marketing) - float(budget_total)) / float(budget_total) * 100, 1) if budget_total else None

    nb_devis_recus = prospects.filter(montant_devis__isnull=False).count()

    satisfaction = satisfaction_qs
    taux_satisfaction = satisfaction.aggregate(moyenne=Avg("note"))["moyenne"]
    taux_satisfaction = round(float(taux_satisfaction) / 5 * 100, 1) if taux_satisfaction is not None else None
    nb_satisfaction = satisfaction.count()
    taux_fidelisation = (
        round(satisfaction.filter(fidele=True).count() / nb_satisfaction * 100, 1) if nb_satisfaction else None
    )

    nb_partenariats = partenariats_qs.filter(statut="ACTIF").count()

    return {
        "nombre_campagnes_realisees": nb_campagnes,
        "nombre_communiques_publies": nb_communiques,
        "nombre_evenements_organises": nb_evenements,
        "nombre_participations_salons": nb_salons,
        "nombre_supports_produits": nb_supports,
        "nombre_prospects_generes": nb_prospects,
        "nombre_nouveaux_clients": nb_nouveaux_clients,
        "taux_conversion_prospects": taux_conversion,
        "chiffre_affaires_marketing": float(ca_marketing),
        "cout_acquisition_client": cout_acquisition,
        "roi_campagnes": roi,
        "nombre_devis_recus": nb_devis_recus,
        "taux_satisfaction_clients": taux_satisfaction,
        "taux_fidelisation": taux_fidelisation,
        "nombre_partenariats_conclus": nb_partenariats,
    }


DG_COM_MEMBRE = direction_permission('DG_COM')


class ActionCommunicationViewSet(viewsets.ModelViewSet):
    queryset = ActionCommunication.objects.all()
    serializer_class = ActionCommunicationSerializer
    permission_classes = [DG_COM_MEMBRE]

    def get_queryset(self):
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Communication', owner_field='responsable')


class ProspectViewSet(viewsets.ModelViewSet):
    queryset = Prospect.objects.select_related("action_origine").all()
    serializer_class = ProspectSerializer
    permission_classes = [DG_COM_MEMBRE]

    def get_queryset(self):
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Marketing')


class PartenariatViewSet(viewsets.ModelViewSet):
    queryset = Partenariat.objects.all()
    serializer_class = PartenariatSerializer
    permission_classes = [DG_COM_MEMBRE]

    def get_queryset(self):
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Marketing', owner_field='responsable')


class SatisfactionClientViewSet(viewsets.ModelViewSet):
    queryset = SatisfactionClient.objects.all()
    serializer_class = SatisfactionClientSerializer
    permission_classes = [DG_COM_MEMBRE]

    def get_queryset(self):
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Marketing')


class CommunicationKPIView(APIView):
    permission_classes = [DG_COM_MEMBRE]

    def get(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")
        return Response(compute_communication_kpis(date_debut, date_fin, request=request))


class CommunicationDashboardDirecteurView(APIView):
    """Vue condensee Directeur : pilotage strategique communication/marketing (ROI, conversion, fidelisation)."""

    permission_classes = [DG_COM_MEMBRE]

    def get(self, request):
        kpis = compute_communication_kpis()

        return Response({
            "chiffre_affaires_marketing": kpis["chiffre_affaires_marketing"],
            "roi_campagnes": kpis["roi_campagnes"],
            "taux_conversion_prospects": kpis["taux_conversion_prospects"],
            "taux_satisfaction_clients": kpis["taux_satisfaction_clients"],
            "taux_fidelisation": kpis["taux_fidelisation"],
            "cout_acquisition_client": kpis["cout_acquisition_client"],
            "nombre_partenariats_conclus": kpis["nombre_partenariats_conclus"],
            "nombre_campagnes_realisees": kpis["nombre_campagnes_realisees"],
            "nombre_nouveaux_clients": kpis["nombre_nouveaux_clients"],
        })


class CommunicationDashboardChefServiceView(APIView):
    """Vue condensee Chef de service : suivi operationnel (actions en cours, prospects a qualifier, charge par responsable)."""

    permission_classes = [DG_COM_MEMBRE]

    def get(self, request):
        actions_en_cours = ActionCommunication.objects.filter(statut__in=["PLANIFIEE", "EN_COURS"])
        prospects_a_qualifier = Prospect.objects.filter(statut__in=["NOUVEAU", "QUALIFIE"])
        devis_en_attente = Prospect.objects.filter(statut="DEVIS_ENVOYE")

        charge_par_responsable = list(
            actions_en_cours.exclude(responsable__isnull=True)
            .values("responsable__username")
            .annotate(nb=Count("id"))
            .order_by("-nb")
        )

        prospects_recents = list(
            prospects_a_qualifier.order_by("-date_creation")[:10].values(
                "nom", "organisation", "statut", "source", "date_creation"
            )
        )

        return Response({
            "nombre_actions_en_cours": actions_en_cours.count(),
            "nombre_prospects_a_qualifier": prospects_a_qualifier.count(),
            "nombre_devis_en_attente": devis_en_attente.count(),
            "charge_actions_par_responsable": charge_par_responsable,
            "prospects_recents": prospects_recents,
        })
