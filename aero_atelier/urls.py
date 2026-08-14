from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CertificationTechnicienViewSet,
    EquipementAtelierViewSet,
    EquipementsAtelierKPIView,
    EtalonnageAtelierViewSet,
    MaintenancePreventiveAtelierViewSet,
    PanneEquipementAtelierViewSet,
    PersonnelKPIView,
)

router = DefaultRouter()
router.register(r"equipements", EquipementAtelierViewSet, basename="aero-equipement-atelier")
router.register(r"pannes", PanneEquipementAtelierViewSet, basename="aero-panne-atelier")
router.register(r"maintenances-preventives", MaintenancePreventiveAtelierViewSet, basename="aero-maintenance-atelier")
router.register(r"etalonnages", EtalonnageAtelierViewSet, basename="aero-etalonnage-atelier")
router.register(r"certifications", CertificationTechnicienViewSet, basename="aero-certification")

urlpatterns = [
    path("kpis/equipements/", EquipementsAtelierKPIView.as_view(), name="aero-equipements-atelier-kpis"),
    path("kpis/personnel/", PersonnelKPIView.as_view(), name="aero-personnel-kpis"),
    path("", include(router.urls)),
]
