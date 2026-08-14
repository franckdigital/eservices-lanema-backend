from django.db.models import Count, F

from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Equipement, Etalonnage, MaintenancePreventive, PanneEquipement
from .serializers import (
    EquipementSerializer,
    EtalonnageSerializer,
    MaintenancePreventiveSerializer,
    PanneEquipementSerializer,
)


class EquipementViewSet(viewsets.ModelViewSet):
    queryset = Equipement.objects.all().order_by("code")
    serializer_class = EquipementSerializer
    permission_classes = [permissions.IsAuthenticated]


class EtalonnageViewSet(viewsets.ModelViewSet):
    queryset = Etalonnage.objects.select_related("equipement").all().order_by("-date_etalonnage")
    serializer_class = EtalonnageSerializer
    permission_classes = [permissions.IsAuthenticated]


class MetrologieDashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        equipements = Equipement.objects.all()
        data = {
            "total_equipements": equipements.count(),
            "operationnel": equipements.filter(statut="OPERATIONNEL").count(),
            "etalonnage_requis": equipements.filter(statut="ETALONNAGE_REQUIS").count(),
            "maintenance": equipements.filter(statut="MAINTENANCE").count(),
            "hors_service": equipements.filter(statut="HORS_SERVICE").count(),
            "etalonnages_par_equipement": list(
                Etalonnage.objects.values("equipement__code").annotate(total=Count("id"))
            ),
        }
        return Response(data)


def compute_equipements_kpis(date_debut=None, date_fin=None):
    """Calcule les 9 KPI des equipements de laboratoire."""
    equipements = Equipement.objects.all()
    total = equipements.count()
    nb_hors_service = equipements.filter(statut="HORS_SERVICE").count()
    nb_maintenance = equipements.filter(statut="MAINTENANCE").count()
    taux_disponibilite = (
        round((total - nb_hors_service - nb_maintenance) / total * 100, 1) if total else None
    )

    pannes = PanneEquipement.objects.all()
    if date_debut and date_fin:
        pannes = pannes.filter(date_panne__range=(date_debut, date_fin))

    pannes_reparees = pannes.filter(date_reparation__isnull=False)
    temps_arret_total = sum((p.date_reparation - p.date_panne).days for p in pannes_reparees)
    temps_moyen_reparation = (
        round(temps_arret_total / pannes_reparees.count(), 1) if pannes_reparees.count() else None
    )

    maintenances = MaintenancePreventive.objects.all()
    if date_debut and date_fin:
        maintenances = maintenances.filter(date_prevue__range=(date_debut, date_fin))
    maintenances_realisees = maintenances.filter(statut="REALISEE")
    nb_dans_calendrier = maintenances_realisees.filter(date_realisee__lte=F("date_prevue")).count()
    respect_calendrier = (
        round(nb_dans_calendrier / maintenances_realisees.count() * 100, 1)
        if maintenances_realisees.count() else None
    )

    return {
        "taux_disponibilite_equipements": taux_disponibilite,
        "taux_utilisation_equipements": None,
        "taux_utilisation_note": (
            "Non mesurable avec les donnees actuelles : aucun journal d'utilisation "
            "des equipements par essai n'est trace."
        ),
        "temps_arret_equipements_jours": temps_arret_total,
        "nombre_pannes": pannes.count(),
        "temps_moyen_reparation_jours": temps_moyen_reparation,
        "nombre_maintenances_preventives": maintenances.count(),
        "nombre_maintenances_reussies": maintenances.filter(reussie=True).count(),
        "respect_calendrier_maintenance": respect_calendrier,
        "nombre_equipements_hors_service": nb_hors_service,
    }


class PanneEquipementViewSet(viewsets.ModelViewSet):
    queryset = PanneEquipement.objects.select_related("equipement").all()
    serializer_class = PanneEquipementSerializer
    permission_classes = [permissions.IsAuthenticated]


class MaintenancePreventiveViewSet(viewsets.ModelViewSet):
    queryset = MaintenancePreventive.objects.select_related("equipement").all()
    serializer_class = MaintenancePreventiveSerializer
    permission_classes = [permissions.IsAuthenticated]


class EquipementsKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(compute_equipements_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))
