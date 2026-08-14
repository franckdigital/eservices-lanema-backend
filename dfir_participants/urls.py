from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    EntrepriseDFIRViewSet,
    ParticipantChangePasswordView,
    ParticipantDFIRViewSet,
    ParticipantLoginView,
    ParticipantLogoutView,
    ParticipantPasswordResetConfirmView,
    ParticipantPasswordResetRequestView,
    ParticipantProfileView,
    ParticipantRegisterView,
)

router = DefaultRouter()
router.register(r"entreprises", EntrepriseDFIRViewSet, basename="dfir-entreprise")
router.register(r"participants", ParticipantDFIRViewSet, basename="dfir-participant")

urlpatterns = [
    path("auth/register/", ParticipantRegisterView.as_view(), name="dfir-participant-register"),
    path("auth/login/", ParticipantLoginView.as_view(), name="dfir-participant-login"),
    path("auth/profile/", ParticipantProfileView.as_view(), name="dfir-participant-profile"),
    path("auth/password-change/", ParticipantChangePasswordView.as_view(), name="dfir-participant-password-change"),
    path("auth/logout/", ParticipantLogoutView.as_view(), name="dfir-participant-logout"),
    path("auth/password-reset/", ParticipantPasswordResetRequestView.as_view(), name="dfir-participant-password-reset"),
    path("auth/password-reset/confirm/", ParticipantPasswordResetConfirmView.as_view(), name="dfir-participant-password-reset-confirm"),
    path("", include(router.urls)),
]
