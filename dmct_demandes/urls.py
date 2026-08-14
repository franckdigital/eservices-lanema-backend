from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DemandeDMCTViewSet, DemandesKPIView

router = DefaultRouter()
router.register(r"demandes", DemandeDMCTViewSet, basename="dmct-demande")

urlpatterns = [
    path("kpis/", DemandesKPIView.as_view(), name="dmct-demandes-kpis"),
    path("", include(router.urls)),
]
