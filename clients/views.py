from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Avg, Q
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.conf import settings
from rest_framework import generics, permissions, serializers, viewsets
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenViewBase

from .models import ClientProfile, LaboRolePermission, ReclamationClient
from .permissions_catalog import PERMISSION_CATALOG, PERMISSION_CODES
from .serializers import ClientProfileSerializer, ReclamationClientSerializer, RegisterSerializer


def get_or_create_profile(user, **defaults):
    profile, _ = ClientProfile.objects.get_or_create(user=user, defaults={"role": "CLIENT", **defaults})
    return profile


class RegisterView(generics.CreateAPIView):
    queryset = ClientProfile.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class EmailTokenObtainPairSerializer(serializers.Serializer):
    """Serializer JWT simple base sur email + mot de passe."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed(
                "Aucun compte actif ne correspond a ces identifiants",
                code="no_active_account",
            )

        if not user.is_active:
            raise AuthenticationFailed(
                "Ce compte est inactif",
                code="inactive_account",
            )

        if not user.check_password(password):
            raise AuthenticationFailed(
                "Email ou mot de passe incorrect",
                code="invalid_credentials",
            )

        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": user,
        }


class EmailTokenObtainPairView(TokenViewBase):
    serializer_class = EmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):  # type: ignore[override]
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data
        tokens = {"access": validated["access"], "refresh": validated["refresh"]}
        profile = get_or_create_profile(validated["user"])
        user_data = ClientProfileSerializer(profile).data

        return Response({"tokens": tokens, "user": user_data})


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = get_or_create_profile(request.user)
        serializer = ClientProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        profile = get_or_create_profile(request.user)
        serializer = ClientProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PushTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = str((request.data or {}).get("expo_push_token", "")).strip()
        if not token:
            return Response({"detail": "expo_push_token requis"}, status=400)

        profile = get_or_create_profile(request.user)
        profile.expo_push_token = token
        profile.save(update_fields=["expo_push_token"])
        return Response({"detail": "Token enregistre"})


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data or {}
        current_password = str(data.get("current_password", ""))
        new_password = str(data.get("new_password", ""))

        if not current_password or not new_password:
            return Response({"detail": "Parametres manquants"}, status=400)

        user = request.user
        if not user.check_password(current_password):
            return Response({"detail": "Mot de passe actuel incorrect"}, status=400)

        try:
            validate_password(new_password, user=user)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=400)

        user.set_password(new_password)
        user.save(update_fields=["password"])

        return Response({"detail": "Mot de passe mis a jour"})


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Avec JWT cote frontend, le logout est gere en supprimant le token
        return Response({"detail": "Logged out"})


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = (request.data or {}).get("email", "")
        email = str(email).strip().lower()

        # Reponse toujours identique pour eviter de divulguer l'existence d'un compte
        response_payload = {
            "detail": "Si un compte existe pour cet email, un lien de reinitialisation a ete envoye."
        }

        if not email:
            return Response(response_payload)

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user is None:
            return Response(response_payload)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"{getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:5173')}/reset-password?uid={uid}&token={token}"

        subject = "Reinitialisation de votre mot de passe"
        message = (
            "Vous avez demande la reinitialisation de votre mot de passe.\n\n"
            f"Lien de reinitialisation : {reset_link}\n\n"
            "Si vous n'etes pas a l'origine de cette demande, ignorez cet email."
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass

        return Response(response_payload)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data or {}
        uid = str(data.get("uid", "")).strip()
        token = str(data.get("token", "")).strip()
        new_password = str(data.get("new_password", ""))

        if not uid or not token or not new_password:
            return Response({"detail": "Parametres manquants"}, status=400)

        try:
            user_id = urlsafe_base64_decode(uid).decode("utf-8")
            user = User.objects.get(pk=user_id)
        except Exception:
            return Response({"detail": "Lien invalide"}, status=400)

        if not default_token_generator.check_token(user, token):
            return Response({"detail": "Lien invalide ou expire"}, status=400)

        try:
            validate_password(new_password, user=user)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=400)

        user.set_password(new_password)
        user.save(update_fields=["password"])

        return Response({"detail": "Mot de passe mis a jour"})


class ClientAdminViewSet(viewsets.ModelViewSet):
    """CRUD admin sur les clients et fournisseurs."""

    serializer_class = ClientProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        role = self.request.query_params.get('role', None)
        qs = ClientProfile.objects.select_related("user").all()
        if role:
            qs = qs.filter(role=role)
        else:
            # Par defaut, retourner clients et fournisseurs.
            # Pour les admins/gestionnaires, retourner tous les profils.
            requester_profile = getattr(self.request.user, "client_profile", None)
            requester_role = getattr(requester_profile, "role", None)
            if requester_role in ["ADMIN", "GESTIONNAIRE"] or getattr(self.request.user, "is_staff", False):
                pass
            else:
                qs = qs.filter(role__in=["CLIENT", "FOURNISSEUR"])
        return qs.order_by("raison_sociale", "user__email")


class ClientsDashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = ClientProfile.objects.filter(role="CLIENT")
        data = {
            "total_clients": qs.count(),
            "actifs": qs.filter(user__is_active=True).count(),
            "premium": qs.filter(type_subscription="PREMIUM").count(),
            "enterprise": qs.filter(type_subscription="ENTERPRISE").count(),
        }
        return Response(data)


class UserPermissionsView(APIView):
    """Permissions du portail staff labo (/app) accordees a l'utilisateur
    courant, d'apres son role (ClientProfile.role) et la matrice
    LaboRolePermission editable depuis Administration > Permissions.

    Le role ADMIN a toujours l'integralite du catalogue, pour eviter tout
    risque de verrouillage accidentel."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = getattr(getattr(request.user, "client_profile", None), "role", None)

        if role == "ADMIN":
            codes = PERMISSION_CODES
        elif role:
            codes = list(
                LaboRolePermission.objects.filter(role=role, is_granted=True)
                .values_list("permission_code", flat=True)
            )
        else:
            codes = []

        permissions_list = [
            {"permission_code": code, "is_granted": True}
            for code in codes
        ]
        return Response(permissions_list)


class IsLaboAdmin(permissions.BasePermission):
    """Autorise uniquement les comptes labo de role ADMIN (Administration)."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = getattr(getattr(request.user, "client_profile", None), "role", None)
        return role == "ADMIN"


class RolePermissionCatalogView(APIView):
    """Catalogue statique des permissions disponibles (code, libelle, module),
    pour l'ecran Administration > Permissions."""

    permission_classes = [IsLaboAdmin]

    def get(self, request):
        data = [
            {"code": code, "label": label, "module": module}
            for code, label, module in PERMISSION_CATALOG
        ]
        return Response(data)


class RolePermissionListView(APIView):
    """Liste des octrois de permission par role (matrice complete), pour
    l'ecran Administration > Permissions."""

    permission_classes = [IsLaboAdmin]

    def get(self, request):
        rows = LaboRolePermission.objects.all()
        data = [
            {"id": r.id, "role": r.role, "permission_code": r.permission_code, "is_granted": r.is_granted}
            for r in rows
        ]
        return Response(data)


class ToggleRolePermissionView(APIView):
    """Bascule l'octroi d'une permission pour un role. Le role ADMIN est
    protege : il conserve toujours l'integralite des droits."""

    permission_classes = [IsLaboAdmin]

    def post(self, request):
        role = request.data.get("role")
        code = request.data.get("permission_code")

        if role == "ADMIN":
            return Response(
                {"detail": "Les droits du role ADMIN ne peuvent pas etre modifies."},
                status=400,
            )
        if role not in dict(ClientProfile.ROLE_CHOICES) or code not in PERMISSION_CODES:
            return Response({"detail": "role ou permission_code invalide"}, status=400)

        grant, created = LaboRolePermission.objects.get_or_create(
            role=role, permission_code=code, defaults={"is_granted": True}
        )
        if not created:
            grant.is_granted = not grant.is_granted
            grant.save(update_fields=["is_granted"])

        return Response({"role": grant.role, "permission_code": grant.permission_code, "is_granted": grant.is_granted})


def compute_clients_kpis(date_debut=None, date_fin=None):
    """Calcule les 7 KPI clients du laboratoire."""
    from demandes.models import DemandeDevis
    from facturation.models import DemandeAnalyse

    clients_qs = ClientProfile.objects.filter(role="CLIENT")
    nb_clients = clients_qs.count()

    nouveaux_clients_qs = User.objects.filter(client_profile__role="CLIENT")
    if date_debut and date_fin:
        nouveaux_clients_qs = nouveaux_clients_qs.filter(date_joined__date__range=(date_debut, date_fin))
    nb_nouveaux_clients = nouveaux_clients_qs.count()

    demandes = DemandeDevis.objects.all()
    if date_debut and date_fin:
        demandes = demandes.filter(created_at__date__range=(date_debut, date_fin))
    nb_dossiers_traites = demandes.filter(statut__in=["ACCEPTEE", "REFUSEE"]).count()

    analyses_terminees = DemandeAnalyse.objects.filter(
        date_fin_analyse__isnull=False, date_depot_echantillons__isnull=False
    )
    delai_moyen_traitement = None
    if analyses_terminees.exists():
        delais = [
            (a.date_fin_analyse - a.date_depot_echantillons).days for a in analyses_terminees
        ]
        delai_moyen_traitement = round(sum(delais) / len(delais), 1)

    reclamations = ReclamationClient.objects.all()
    if date_debut and date_fin:
        reclamations = reclamations.filter(date_reception__range=(date_debut, date_fin))

    satisfaction_moyenne = reclamations.filter(note_satisfaction__isnull=False).aggregate(
        m=Avg("note_satisfaction")
    )
    taux_satisfaction = None
    if satisfaction_moyenne["m"] is not None:
        taux_satisfaction = round(float(satisfaction_moyenne["m"]) / 5 * 100, 1)

    reclamations_traitees = reclamations.filter(date_traitement__isnull=False)
    temps_moyen_traitement_reclamations = None
    if reclamations_traitees.exists():
        delais_reclamations = [
            (r.date_traitement - r.date_reception).days for r in reclamations_traitees
        ]
        temps_moyen_traitement_reclamations = round(
            sum(delais_reclamations) / len(delais_reclamations), 1
        )

    return {
        "nombre_clients": nb_clients,
        "nombre_nouveaux_clients": nb_nouveaux_clients,
        "nombre_dossiers_traites": nb_dossiers_traites,
        "delai_moyen_traitement_demande_jours": delai_moyen_traitement,
        "taux_satisfaction_client": taux_satisfaction,
        "nombre_reclamations": reclamations.count(),
        "temps_moyen_traitement_reclamations_jours": temps_moyen_traitement_reclamations,
    }


class ReclamationClientViewSet(viewsets.ModelViewSet):
    queryset = ReclamationClient.objects.select_related("client").all()
    serializer_class = ReclamationClientSerializer
    permission_classes = [permissions.IsAuthenticated]


class ClientsKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(compute_clients_kpis(
            request.query_params.get("date_debut"), request.query_params.get("date_fin")
        ))


class EdiligenceAccountsView(APIView):
    """Liste des comptes e-diligence (core.UserProfile) sans profil labo,
    pour l'écran Administration > Liaison de comptes (fusion). Un compte lié
    partage un seul identifiant/mot de passe entre les deux portails."""

    permission_classes = [IsLaboAdmin]

    def get(self, request):
        from core.models import UserProfile as EdiligenceProfile

        search = (request.query_params.get("search") or "").strip()

        qs = User.objects.filter(profile__isnull=False, client_profile__isnull=True)
        if search:
            qs = qs.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )
        qs = qs.select_related("profile").order_by("username")[:30]

        role_labels = dict(EdiligenceProfile.ROLE_CHOICES)
        data = [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "ediligence_role": u.profile.role,
                "ediligence_role_display": role_labels.get(u.profile.role, u.profile.role),
            }
            for u in qs
        ]
        return Response(data)


class LinkEdiligenceAccountView(APIView):
    """Rattache un profil labo (ClientProfile) à un compte e-diligence
    EXISTANT (même User, même identifiant/mot de passe) plutôt que de créer
    un nouveau compte séparé : c'est la fusion de comptes."""

    permission_classes = [IsLaboAdmin]

    def post(self, request):
        user_id = request.data.get("user_id")
        role = request.data.get("role")

        if not user_id or role not in dict(ClientProfile.ROLE_CHOICES):
            return Response({"detail": "user_id et role valides sont requis"}, status=400)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "Compte introuvable"}, status=404)

        if not hasattr(user, "profile"):
            return Response(
                {"detail": "Ce compte n'a pas de profil e-diligence à fusionner"}, status=400
            )
        if hasattr(user, "client_profile"):
            return Response({"detail": "Ce compte a déjà un profil labo"}, status=400)

        profile = ClientProfile.objects.create(
            user=user,
            role=role,
            raison_sociale=request.data.get("raison_sociale", ""),
            organisation=request.data.get("organisation", ""),
            telephone=request.data.get("telephone", ""),
        )
        serializer = ClientProfileSerializer(profile)
        return Response(serializer.data, status=201)
