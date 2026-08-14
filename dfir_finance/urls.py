from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FactureDFIRViewSet, FinanciersKPIView

router = DefaultRouter()
router.register(r"factures", FactureDFIRViewSet, basename="dfir-facture")

urlpatterns = [
    path("kpis/", FinanciersKPIView.as_view(), name="dfir-financiers-kpis"),
    path("", include(router.urls)),
]
