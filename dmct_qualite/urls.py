from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ActionCorrectiveDMCTViewSet, AuditDMCTViewSet, NonConformiteDMCTViewSet, QualiteKPIView

router = DefaultRouter()
router.register(r"non-conformites", NonConformiteDMCTViewSet, basename="dmct-non-conformite")
router.register(r"actions-correctives", ActionCorrectiveDMCTViewSet, basename="dmct-action-corrective")
router.register(r"audits", AuditDMCTViewSet, basename="dmct-audit")

urlpatterns = [
    path("kpis/", QualiteKPIView.as_view(), name="dmct-qualite-kpis"),
    path("", include(router.urls)),
]
