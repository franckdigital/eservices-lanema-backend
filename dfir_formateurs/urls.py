from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FormateurDFIRViewSet, FormateursKPIView

router = DefaultRouter()
router.register(r"formateurs", FormateurDFIRViewSet, basename="dfir-formateur")

urlpatterns = [
    path("kpis/", FormateursKPIView.as_view(), name="dfir-formateurs-kpis"),
    path("", include(router.urls)),
]
