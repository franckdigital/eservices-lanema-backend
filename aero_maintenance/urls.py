from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BatterieAeronefViewSet,
    BatteriesKPIView,
    InspectionRoueViewSet,
    MaintenanceKPIView,
    OrdreTravailViewSet,
    RoueAeronefViewSet,
    RouesKPIView,
)

router = DefaultRouter()
router.register(r"ordres-travail", OrdreTravailViewSet, basename="aero-ordre-travail")
router.register(r"roues", RoueAeronefViewSet, basename="aero-roue")
router.register(r"inspections-roues", InspectionRoueViewSet, basename="aero-inspection-roue")
router.register(r"batteries", BatterieAeronefViewSet, basename="aero-batterie")

urlpatterns = [
    path("kpis/", MaintenanceKPIView.as_view(), name="aero-maintenance-kpis"),
    path("kpis/roues/", RouesKPIView.as_view(), name="aero-roues-kpis"),
    path("kpis/batteries/", BatteriesKPIView.as_view(), name="aero-batteries-kpis"),
    path("", include(router.urls)),
]
