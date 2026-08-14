from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ActionQualiteViewSet,
    AuditViewSet,
    EchantillonsKPIView,
    EchantillonViewSet,
    EssaisKPIView,
    EssaiViewSet,
    NonConformiteViewSet,
    QualiteDashboardStatsView,
    QualiteIsoKPIView,
    RecommandationAuditViewSet,
    TechniciensKPIView,
)


router = DefaultRouter()
router.register(r"non-conformites", NonConformiteViewSet, basename="non-conformite")
router.register(r"audits", AuditViewSet, basename="audit")
router.register(r"echantillons", EchantillonViewSet, basename="echantillon")
router.register(r"essais", EssaiViewSet, basename="essai")
router.register(r"actions-qualite", ActionQualiteViewSet, basename="action-qualite-labo")
router.register(r"recommandations-audit", RecommandationAuditViewSet, basename="recommandation-audit")


urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/stats/", QualiteDashboardStatsView.as_view(), name="qualite-dashboard-stats"),
    path("echantillons/kpis/", EchantillonsKPIView.as_view(), name="dea-echantillons-kpis"),
    path("essais/kpis/", EssaisKPIView.as_view(), name="dea-essais-kpis"),
    path("techniciens/kpis/", TechniciensKPIView.as_view(), name="dea-techniciens-kpis"),
    path("qualite-iso/kpis/", QualiteIsoKPIView.as_view(), name="dea-qualite-iso-kpis"),
]
