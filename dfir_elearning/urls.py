from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CertificatFormationViewSet,
    CertificatPDFView,
    CertificatVerifyView,
    ClasseVirtuelleViewSet,
    LeconViewSet,
    MonEspaceView,
    ProgressionUpdateView,
)

router = DefaultRouter()
router.register(r"lecons", LeconViewSet, basename="dfir-lecon")
router.register(r"classes-virtuelles", ClasseVirtuelleViewSet, basename="dfir-classe-virtuelle")
router.register(r"certificats", CertificatFormationViewSet, basename="dfir-certificat")

urlpatterns = [
    path("mon-espace/", MonEspaceView.as_view(), name="dfir-mon-espace"),
    path("lecons/<int:lecon_id>/progression/", ProgressionUpdateView.as_view(), name="dfir-progression"),
    path("certificats/<int:pk>/pdf/", CertificatPDFView.as_view(), name="dfir-certificat-pdf"),
    path("verifier/<uuid:code>/", CertificatVerifyView.as_view(), name="dfir-certificat-verify"),
    path("", include(router.urls)),
]
