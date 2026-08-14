from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ActionCorrectiveDAEViewSet, AuditQualiteDAEViewSet, NonConformiteDAEViewSet, QualiteKPIView

router = DefaultRouter()
router.register(r"non-conformites", NonConformiteDAEViewSet, basename="aero-non-conformite")
router.register(r"actions-correctives", ActionCorrectiveDAEViewSet, basename="aero-action-corrective")
router.register(r"audits", AuditQualiteDAEViewSet, basename="aero-audit")

urlpatterns = [
    path("kpis/", QualiteKPIView.as_view(), name="aero-qualite-kpis"),
    path("", include(router.urls)),
]
