from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CompteEmailDFIRViewSet, DetecterConfigView, EmailDFIRViewSet

router = DefaultRouter()
router.register(r"comptes", CompteEmailDFIRViewSet, basename="dfir-compte-email")
router.register(r"emails", EmailDFIRViewSet, basename="dfir-email")

urlpatterns = [
    path("detecter-config/", DetecterConfigView.as_view(), name="dfir-email-detecter-config"),
    path("", include(router.urls)),
]
