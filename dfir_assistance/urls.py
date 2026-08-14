from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AssistanceKPIView, MissionAssistanceViewSet

router = DefaultRouter()
router.register(r"missions", MissionAssistanceViewSet, basename="dfir-mission-assistance")

urlpatterns = [
    path("kpis/", AssistanceKPIView.as_view(), name="dfir-assistance-kpis"),
    path("", include(router.urls)),
]
