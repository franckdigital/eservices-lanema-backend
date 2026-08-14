from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FactureDMCTViewSet, FinanciersKPIView

router = DefaultRouter()
router.register(r"factures", FactureDMCTViewSet, basename="dmct-facture")

urlpatterns = [
    path("kpis/", FinanciersKPIView.as_view(), name="dmct-financiers-kpis"),
    path("", include(router.urls)),
]
