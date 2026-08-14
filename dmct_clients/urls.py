from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ClientDMCTViewSet, ClientsKPIView, ReclamationClientDMCTViewSet

router = DefaultRouter()
router.register(r"clients", ClientDMCTViewSet, basename="dmct-client")
router.register(r"reclamations", ReclamationClientDMCTViewSet, basename="dmct-reclamation")

urlpatterns = [
    path("kpis/", ClientsKPIView.as_view(), name="dmct-clients-kpis"),
    path("", include(router.urls)),
]
