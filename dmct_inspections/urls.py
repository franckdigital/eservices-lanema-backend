from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ContreVisiteDMCTViewSet, InspectionDMCTViewSet, InspectionsKPIView

router = DefaultRouter()
router.register(r"inspections", InspectionDMCTViewSet, basename="dmct-inspection")
router.register(r"contre-visites", ContreVisiteDMCTViewSet, basename="dmct-contre-visite")

urlpatterns = [
    path("kpis/", InspectionsKPIView.as_view(), name="dmct-inspections-kpis"),
    path("", include(router.urls)),
]
