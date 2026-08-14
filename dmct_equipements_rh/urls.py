from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CertificationAgentDMCTViewSet,
    EquipementReferenceViewSet,
    EquipementsReferenceKPIView,
    EtalonnageReferenceViewSet,
    FormationDMCTViewSet,
    MaintenancePreventiveReferenceViewSet,
    PanneEquipementReferenceViewSet,
    RHKPIView,
)

router = DefaultRouter()
router.register(r"equipements", EquipementReferenceViewSet, basename="dmct-equipement-reference")
router.register(r"pannes", PanneEquipementReferenceViewSet, basename="dmct-panne-reference")
router.register(r"maintenances-preventives", MaintenancePreventiveReferenceViewSet, basename="dmct-maintenance-reference")
router.register(r"etalonnages", EtalonnageReferenceViewSet, basename="dmct-etalonnage-reference")
router.register(r"certifications", CertificationAgentDMCTViewSet, basename="dmct-certification")
router.register(r"formations", FormationDMCTViewSet, basename="dmct-formation")

urlpatterns = [
    path("kpis/equipements/", EquipementsReferenceKPIView.as_view(), name="dmct-equipements-reference-kpis"),
    path("kpis/rh/", RHKPIView.as_view(), name="dmct-rh-kpis"),
    path("", include(router.urls)),
]
