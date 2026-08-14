from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CertificatDMCTViewSet, InstrumentMesureViewSet, InstrumentsKPIView

router = DefaultRouter()
router.register(r"instruments", InstrumentMesureViewSet, basename="dmct-instrument")
router.register(r"certificats", CertificatDMCTViewSet, basename="dmct-certificat")

urlpatterns = [
    path("kpis/", InstrumentsKPIView.as_view(), name="dmct-instruments-kpis"),
    path("", include(router.urls)),
]
