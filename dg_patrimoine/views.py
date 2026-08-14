from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.direction_access import direction_permission, scope_dg_service_queryset

from .models import Bien, InventairePatrimoine, MaintenanceBien, MouvementBien
from .serializers import (
    BienSerializer,
    InventairePatrimoineSerializer,
    MaintenanceBienSerializer,
    MouvementBienSerializer,
)


def compute_patrimoine_kpis(date_debut=None, date_fin=None, request=None):
    """Calcule les 13 KPI Patrimoine. Reutilisable directement par le dashboard DG.
    Si `request` est fourni, restreint au meme perimetre (Service + proprietaire)
    que les listes CRUD de l'utilisateur courant."""
    biens = Bien.objects.all()
    mouvements_qs = MouvementBien.objects.all()
    maintenances_qs = MaintenanceBien.objects.all()
    inventaires_qs = InventairePatrimoine.objects.all()
    if request is not None:
        biens = scope_dg_service_queryset(biens, request, 'Patrimoine', owner_field='responsable')
        mouvements_qs = scope_dg_service_queryset(mouvements_qs, request, 'Patrimoine', owner_field='effectue_par')
        maintenances_qs = scope_dg_service_queryset(maintenances_qs, request, 'Patrimoine', owner_field='bien__responsable')
        inventaires_qs = scope_dg_service_queryset(inventaires_qs, request, 'Patrimoine', owner_field='responsable')

    total_biens = biens.count()

    nouveaux_biens_qs = biens
    if date_debut and date_fin:
        nouveaux_biens_qs = biens.filter(date_acquisition__range=(date_debut, date_fin))
    nb_nouveaux_biens = nouveaux_biens_qs.count()

    valeur_totale = biens.aggregate(total=Sum("valeur_actuelle"))["total"]
    if valeur_totale is None:
        valeur_totale = biens.aggregate(total=Sum("valeur_acquisition"))["total"] or 0

    mouvements = mouvements_qs
    nb_sorties = mouvements.filter(type_mouvement="SORTIE").count()
    nb_mouvements = mouvements.count()

    nb_reformes = biens.filter(statut="REFORME").count()
    nb_perdus = biens.filter(statut="PERDU").count()
    nb_en_maintenance = biens.filter(statut="EN_MAINTENANCE").count()
    nb_indisponibles = biens.filter(statut__in=["EN_MAINTENANCE", "REFORME", "PERDU", "SORTI"]).count()
    taux_disponibilite = round((total_biens - nb_indisponibles) / total_biens * 100, 1) if total_biens else None

    biens_amortissables = biens.exclude(valeur_actuelle__isnull=True).filter(valeur_acquisition__gt=0)
    taux_amortissement = None
    if biens_amortissables.exists():
        ratios = [
            float(b.valeur_acquisition - b.valeur_actuelle) / float(b.valeur_acquisition)
            for b in biens_amortissables
        ]
        taux_amortissement = round(sum(ratios) / len(ratios) * 100, 1)

    maintenances = maintenances_qs
    annee = timezone.now().year
    cout_annuel_maintenance = (
        maintenances.filter(date_maintenance__year=annee).aggregate(total=Sum("cout"))["total"] or 0
    )

    taux_renouvellement = round(nb_nouveaux_biens / total_biens * 100, 1) if total_biens else None

    inventaires = inventaires_qs
    nb_inventaires = inventaires.count()

    totaux_inventaires = inventaires.aggregate(
        verifies=Sum("nombre_biens_verifies"), ecarts=Sum("ecarts_constates")
    )
    total_verifies = totaux_inventaires["verifies"] or 0
    total_ecarts = totaux_inventaires["ecarts"] or 0
    taux_conformite_inventaires = (
        round((total_verifies - total_ecarts) / total_verifies * 100, 1) if total_verifies else None
    )

    dernier_inventaire = inventaires.order_by("-date_inventaire").first()
    taux_couverture_inventaire = (
        round(dernier_inventaire.nombre_biens_verifies / total_biens * 100, 1)
        if dernier_inventaire and total_biens else None
    )

    return {
        "nombre_total_biens": total_biens,
        "valeur_totale_patrimoine": float(valeur_totale),
        "nombre_nouveaux_biens": nb_nouveaux_biens,
        "nombre_sorties_biens": nb_sorties,
        "nombre_mouvements_biens": nb_mouvements,
        "nombre_biens_reformes": nb_reformes,
        "nombre_biens_perdus": nb_perdus,
        "nombre_biens_en_maintenance": nb_en_maintenance,
        "taux_disponibilite_equipements": taux_disponibilite,
        "taux_amortissement": taux_amortissement,
        "cout_annuel_maintenance": float(cout_annuel_maintenance),
        "taux_renouvellement_equipements": taux_renouvellement,
        "nombre_inventaires_realises": nb_inventaires,
        "taux_conformite_inventaires": taux_conformite_inventaires,
        "taux_couverture_inventaire": taux_couverture_inventaire,
    }


DG_PATRIMOINE_MEMBRE = direction_permission('DG_PATRIMOINE')


class BienViewSet(viewsets.ModelViewSet):
    queryset = Bien.objects.all()
    serializer_class = BienSerializer
    permission_classes = [DG_PATRIMOINE_MEMBRE]

    def get_queryset(self):
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Patrimoine', owner_field='responsable')


class MouvementBienViewSet(viewsets.ModelViewSet):
    queryset = MouvementBien.objects.select_related("bien").all()
    serializer_class = MouvementBienSerializer
    permission_classes = [DG_PATRIMOINE_MEMBRE]

    def get_queryset(self):
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Patrimoine', owner_field='effectue_par')


class MaintenanceBienViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceBien.objects.select_related("bien").all()
    serializer_class = MaintenanceBienSerializer
    permission_classes = [DG_PATRIMOINE_MEMBRE]

    def get_queryset(self):
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Patrimoine', owner_field='bien__responsable')


class InventairePatrimoineViewSet(viewsets.ModelViewSet):
    queryset = InventairePatrimoine.objects.all()
    serializer_class = InventairePatrimoineSerializer
    permission_classes = [DG_PATRIMOINE_MEMBRE]

    def get_queryset(self):
        return scope_dg_service_queryset(super().get_queryset(), self.request, 'Patrimoine', owner_field='responsable')


class PatrimoineKPIView(APIView):
    permission_classes = [DG_PATRIMOINE_MEMBRE]

    def get(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")
        return Response(compute_patrimoine_kpis(date_debut, date_fin, request=request))


class PatrimoineDashboardDirecteurView(APIView):
    """Vue condensee Directeur : pilotage strategique du patrimoine (valeur, disponibilite, risques)."""

    permission_classes = [DG_PATRIMOINE_MEMBRE]

    def get(self, request):
        kpis = compute_patrimoine_kpis()
        biens_a_risque = Bien.objects.filter(statut__in=["PERDU", "REFORME"]).count()
        dernier_inventaire = InventairePatrimoine.objects.order_by("-date_inventaire").first()

        return Response({
            "valeur_totale_patrimoine": kpis["valeur_totale_patrimoine"],
            "taux_disponibilite_equipements": kpis["taux_disponibilite_equipements"],
            "taux_amortissement": kpis["taux_amortissement"],
            "cout_annuel_maintenance": kpis["cout_annuel_maintenance"],
            "taux_renouvellement_equipements": kpis["taux_renouvellement_equipements"],
            "taux_conformite_inventaires": kpis["taux_conformite_inventaires"],
            "nombre_biens_reformes": kpis["nombre_biens_reformes"],
            "nombre_biens_perdus": kpis["nombre_biens_perdus"],
            "biens_a_risque": biens_a_risque,
            "dernier_inventaire_date": dernier_inventaire.date_inventaire if dernier_inventaire else None,
            "dernier_inventaire_ecarts": dernier_inventaire.ecarts_constates if dernier_inventaire else None,
        })


class PatrimoineDashboardChefServiceView(APIView):
    """Vue condensee Chef de service : suivi operationnel (maintenances en cours, charge par responsable)."""

    permission_classes = [DG_PATRIMOINE_MEMBRE]

    def get(self, request):
        biens_en_maintenance = Bien.objects.filter(statut="EN_MAINTENANCE")
        maintenances_en_cours = MaintenanceBien.objects.filter(date_fin__isnull=True)

        charge_par_responsable = list(
            Bien.objects.exclude(responsable__isnull=True)
            .values("responsable__username")
            .annotate(nb=Count("id"))
            .order_by("-nb")
        )

        mouvements_recents = list(
            MouvementBien.objects.select_related("bien").order_by("-date_mouvement")[:10].values(
                "bien__code", "type_mouvement", "motif", "date_mouvement"
            )
        )

        return Response({
            "nombre_biens_en_maintenance": biens_en_maintenance.count(),
            "maintenances_en_cours": maintenances_en_cours.count(),
            "charge_biens_par_responsable": charge_par_responsable,
            "mouvements_recents": mouvements_recents,
        })
