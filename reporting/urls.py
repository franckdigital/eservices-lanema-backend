from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    RapportEssaiViewSet,
    RapportGenerateView,
    RapportListView,
    RapportsEssaisKPIView,
    ReportingDashboardStatsView,
)

router = DefaultRouter()
router.register(r"rapports-essais", RapportEssaiViewSet, basename="rapport-essai")

urlpatterns = [
    path("dashboard/stats/", ReportingDashboardStatsView.as_view(), name="reporting-dashboard-stats"),
    path("generate/<str:type_rapport>/", RapportGenerateView.as_view(), name="reporting-generate"),
    path("rapports/", RapportListView.as_view(), name="reporting-rapports"),
    path("rapports-essais/kpis/", RapportsEssaisKPIView.as_view(), name="dea-rapports-essais-kpis"),
    path("", include(router.urls)),
]
