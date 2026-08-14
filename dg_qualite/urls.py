from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ActionQualiteViewSet,
    AuditQualiteViewSet,
    IndicateurQualiteViewSet,
    NonConformiteQualiteViewSet,
    QualiteDashboardChefServiceView,
    QualiteDashboardDirecteurView,
    QualiteKPIView,
    ReclamationClientViewSet,
    RevueDirectionViewSet,
)

router = DefaultRouter()
router.register(r"non-conformites", NonConformiteQualiteViewSet, basename="non-conformite-qualite")
router.register(r"actions", ActionQualiteViewSet, basename="action-qualite")
router.register(r"audits", AuditQualiteViewSet, basename="audit-qualite")
router.register(r"reclamations", ReclamationClientViewSet, basename="reclamation-client")
router.register(r"revues-direction", RevueDirectionViewSet, basename="revue-direction")
router.register(r"indicateurs", IndicateurQualiteViewSet, basename="indicateur-qualite")

urlpatterns = [
    path("kpis/", QualiteKPIView.as_view(), name="dg-qualite-kpis"),
    path("dashboard/directeur/", QualiteDashboardDirecteurView.as_view(), name="dg-qualite-dashboard-directeur"),
    path("dashboard/chef-service/", QualiteDashboardChefServiceView.as_view(), name="dg-qualite-dashboard-chef-service"),
    path("", include(router.urls)),
]
