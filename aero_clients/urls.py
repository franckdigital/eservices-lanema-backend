from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AeronefViewSet, ClientAeronautiqueViewSet, ClientsKPIView, ReclamationClientDAEViewSet

router = DefaultRouter()
router.register(r"clients", ClientAeronautiqueViewSet, basename="aero-client")
router.register(r"aeronefs", AeronefViewSet, basename="aero-aeronef")
router.register(r"reclamations", ReclamationClientDAEViewSet, basename="aero-reclamation")

urlpatterns = [
    path("kpis/", ClientsKPIView.as_view(), name="aero-clients-kpis"),
    path("", include(router.urls)),
]
