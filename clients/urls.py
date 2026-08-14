from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ChangePasswordView,
    ClientAdminViewSet,
    ClientsDashboardStatsView,
    ClientsKPIView,
    EdiligenceAccountsView,
    EmailTokenObtainPairView,
    LinkEdiligenceAccountView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileView,
    PushTokenView,
    ReclamationClientViewSet,
    RegisterView,
    RolePermissionCatalogView,
    RolePermissionListView,
    ToggleRolePermissionView,
    UserPermissionsView,
)


router = DefaultRouter()
router.register(r"clients", ClientAdminViewSet, basename="clients-admin")
router.register(r"reclamations", ReclamationClientViewSet, basename="reclamation-client-labo")


urlpatterns = [
    # Auth
    path("auth/login/", EmailTokenObtainPairView.as_view(), name="clients-login"),
    path("auth/register/", RegisterView.as_view(), name="clients-register"),
    path("auth/profile/", ProfileView.as_view(), name="clients-profile"),
    path("auth/profile/update/", ProfileView.as_view(), name="clients-profile-update"),
    path("auth/password-change/", ChangePasswordView.as_view(), name="clients-password-change"),
    path("auth/push-token/", PushTokenView.as_view(), name="clients-push-token"),
    path("auth/logout/", LogoutView.as_view(), name="clients-logout"),
    path("auth/password-reset/", PasswordResetRequestView.as_view(), name="clients-password-reset"),
    path(
        "auth/password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="clients-password-reset-confirm",
    ),

    # Admin clients CRUD
    path("", include(router.urls)),

    # Dashboard clients stats
    path("dashboard/stats/", ClientsDashboardStatsView.as_view(), name="clients-dashboard-stats"),

    # User permissions
    path("user/permissions/", UserPermissionsView.as_view(), name="user-permissions"),
    path("admin/permissions/", RolePermissionCatalogView.as_view(), name="labo-permissions-catalog"),
    path("admin/role-permissions/", RolePermissionListView.as_view(), name="labo-role-permissions"),
    path("admin/toggle-role-permission/", ToggleRolePermissionView.as_view(), name="labo-toggle-role-permission"),

    # Fusion de comptes : lier un profil labo à un compte e-diligence existant
    path("admin/ediligence-accounts/", EdiligenceAccountsView.as_view(), name="labo-ediligence-accounts"),
    path("admin/link-ediligence-account/", LinkEdiligenceAccountView.as_view(), name="labo-link-ediligence-account"),

    # KPI decisionnels DEA - clients
    path("clients-kpis/kpis/", ClientsKPIView.as_view(), name="dea-clients-kpis"),
]
