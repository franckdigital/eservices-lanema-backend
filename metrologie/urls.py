from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views_circuit import CertificatViewSet, FicheMetrologieViewSet, MesCertificatsViewSet
from .views import (
    EquipementsKPIView,
    EquipementViewSet,
    EtalonnageViewSet,
    MaintenancePreventiveViewSet,
    MetrologieDashboardStatsView,
    PanneEquipementViewSet,
)


router = DefaultRouter()
router.register(r"equipements", EquipementViewSet, basename="equipement")
router.register(r"etalonnages", EtalonnageViewSet, basename="etalonnage")
router.register(r"pannes", PanneEquipementViewSet, basename="panne-equipement")
router.register(r"maintenances-preventives", MaintenancePreventiveViewSet, basename="maintenance-preventive")
router.register(r"fiches-travaux", FicheMetrologieViewSet, basename="fiche-travaux-metrologie")
router.register(r"certificats-etalonnage", CertificatViewSet, basename="certificat-etalonnage")
router.register(r"mes-certificats", MesCertificatsViewSet, basename="mes-certificats")


urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/stats/", MetrologieDashboardStatsView.as_view(), name="metrologie-dashboard-stats"),
    path("equipements/kpis/", EquipementsKPIView.as_view(), name="dea-equipements-kpis"),
]
