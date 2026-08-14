from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LaboratoireViewSet

router = DefaultRouter()
router.register(r"", LaboratoireViewSet, basename="laboratoire")

urlpatterns = [
    path("", include(router.urls)),
]
