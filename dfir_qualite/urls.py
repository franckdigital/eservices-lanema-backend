from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AmeliorationProgrammeViewSet, AuditDFIRViewSet, QualiteKPIView, ReclamationDFIRViewSet

router = DefaultRouter()
router.register(r"reclamations", ReclamationDFIRViewSet, basename="dfir-reclamation")
router.register(r"ameliorations", AmeliorationProgrammeViewSet, basename="dfir-amelioration")
router.register(r"audits", AuditDFIRViewSet, basename="dfir-audit")

urlpatterns = [
    path("kpis/", QualiteKPIView.as_view(), name="dfir-qualite-kpis"),
    path("", include(router.urls)),
]
