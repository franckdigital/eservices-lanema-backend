from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    EvaluationSatisfactionView,
    FormationsKPIView,
    FormationViewSet,
    InscriptionParticipantViewSet,
    ParticipantsKPIView,
    RessourcesPedagogiquesKPIView,
    SessionFormationViewSet,
    SupportPedagogiqueViewSet,
)

router = DefaultRouter()
router.register(r"formations", FormationViewSet, basename="dfir-formation")
router.register(r"sessions", SessionFormationViewSet, basename="dfir-session")
router.register(r"inscriptions", InscriptionParticipantViewSet, basename="dfir-inscription")
router.register(r"supports", SupportPedagogiqueViewSet, basename="dfir-support")

urlpatterns = [
    path("kpis/", FormationsKPIView.as_view(), name="dfir-formations-kpis"),
    path("kpis/participants/", ParticipantsKPIView.as_view(), name="dfir-participants-kpis"),
    path("kpis/ressources-pedagogiques/", RessourcesPedagogiquesKPIView.as_view(), name="dfir-ressources-pedagogiques-kpis"),
    path("satisfaction/<uuid:token>/", EvaluationSatisfactionView.as_view(), name="dfir-satisfaction"),
    path("", include(router.urls)),
]
