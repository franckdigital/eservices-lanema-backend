from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BienViewSet,
    InventairePatrimoineViewSet,
    MaintenanceBienViewSet,
    MouvementBienViewSet,
    PatrimoineDashboardChefServiceView,
    PatrimoineDashboardDirecteurView,
    PatrimoineKPIView,
)

router = DefaultRouter()
router.register(r"biens", BienViewSet, basename="bien")
router.register(r"mouvements", MouvementBienViewSet, basename="mouvement-bien")
router.register(r"maintenances", MaintenanceBienViewSet, basename="maintenance-bien")
router.register(r"inventaires", InventairePatrimoineViewSet, basename="inventaire-patrimoine")

urlpatterns = [
    path("kpis/", PatrimoineKPIView.as_view(), name="dg-patrimoine-kpis"),
    path("dashboard/directeur/", PatrimoineDashboardDirecteurView.as_view(), name="dg-patrimoine-dashboard-directeur"),
    path("dashboard/chef-service/", PatrimoineDashboardChefServiceView.as_view(), name="dg-patrimoine-dashboard-chef-service"),
    path("", include(router.urls)),
]
