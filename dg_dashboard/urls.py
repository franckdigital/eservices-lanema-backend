from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DashboardDGView, ObjectifStrategiqueViewSet

router = DefaultRouter()
router.register(r"objectifs-strategiques", ObjectifStrategiqueViewSet, basename="objectif-strategique")

urlpatterns = [
    path("dashboard/", DashboardDGView.as_view(), name="dg-dashboard"),
    path("", include(router.urls)),
]
