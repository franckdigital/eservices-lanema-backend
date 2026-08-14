from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import InnovationKPIView, ProjetInnovationViewSet

router = DefaultRouter()
router.register(r"projets", ProjetInnovationViewSet, basename="dfir-projet-innovation")

urlpatterns = [
    path("kpis/", InnovationKPIView.as_view(), name="dfir-innovation-kpis"),
    path("", include(router.urls)),
]
