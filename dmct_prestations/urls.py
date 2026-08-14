from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PrestationDMCTViewSet, PrestationsKPIView

router = DefaultRouter()
router.register(r"prestations", PrestationDMCTViewSet, basename="dmct-prestation")

urlpatterns = [
    path("kpis/", PrestationsKPIView.as_view(), name="dmct-prestations-kpis"),
    path("", include(router.urls)),
]
