from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, permissions, serializers as drf_serializers, viewsets
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenViewBase

from core.direction_access import direction_permission

from .models import EntrepriseDFIR, ParticipantDFIR
from .serializers import (
    EntrepriseDFIRSerializer,
    ParticipantAuthProfileSerializer,
    ParticipantDFIRSerializer,
    ParticipantRegisterSerializer,
)

DFIR_ENCADREMENT = direction_permission('DFIR', min_tier='encadrement')


class EntrepriseDFIRViewSet(viewsets.ModelViewSet):
    queryset = EntrepriseDFIR.objects.all()
    serializer_class = EntrepriseDFIRSerializer
    permission_classes = [DFIR_ENCADREMENT]


class ParticipantDFIRViewSet(viewsets.ModelViewSet):
    queryset = ParticipantDFIR.objects.select_related("entreprise").all()
    serializer_class = ParticipantDFIRSerializer
    permission_classes = [DFIR_ENCADREMENT]


# ─────────────────────────────────────────────────────────────────────────
# "Mon espace" — authentification autonome des participants (email + mot de
# passe), totalement independante des comptes e-diligence/labo. Miroir du
# portail client labo (clients/views.py) avec un correctif : le mot de passe
# choisi par le participant est bien celui utilise (pas un mot de passe
# temporaire).
# ─────────────────────────────────────────────────────────────────────────

def get_participant_or_404(user):
    return ParticipantDFIR.objects.select_related("entreprise").get(user=user)


class ParticipantRegisterView(generics.CreateAPIView):
    queryset = ParticipantDFIR.objects.all()
    serializer_class = ParticipantRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        participant = serializer.save()
        return Response(ParticipantAuthProfileSerializer(participant).data, status=201)


class ParticipantEmailTokenObtainPairSerializer(drf_serializers.Serializer):
    email = drf_serializers.EmailField()
    password = drf_serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise AuthenticationFailed("Aucun compte actif ne correspond a ces identifiants", code="no_active_account")

        if not hasattr(user, "participant_dfir_profile"):
            raise AuthenticationFailed("Aucun compte actif ne correspond a ces identifiants", code="no_active_account")

        if not user.is_active:
            raise AuthenticationFailed("Ce compte est inactif", code="inactive_account")

        if not user.check_password(password):
            raise AuthenticationFailed("Email ou mot de passe incorrect", code="invalid_credentials")

        refresh = RefreshToken.for_user(user)
        return {"access": str(refresh.access_token), "refresh": str(refresh), "user": user}


class ParticipantLoginView(TokenViewBase):
    serializer_class = ParticipantEmailTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        participant = get_participant_or_404(validated["user"])
        tokens = {"access": validated["access"], "refresh": validated["refresh"]}
        return Response({"tokens": tokens, "participant": ParticipantAuthProfileSerializer(participant).data})


class ParticipantProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            participant = get_participant_or_404(request.user)
        except ParticipantDFIR.DoesNotExist:
            return Response({"detail": "Aucun espace participant pour ce compte"}, status=403)
        return Response(ParticipantAuthProfileSerializer(participant).data)


class ParticipantChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, "participant_dfir_profile"):
            return Response({"detail": "Aucun espace participant pour ce compte"}, status=403)

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


class ParticipantLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return Response({"detail": "Logged out"})


class ParticipantPasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = str((request.data or {}).get("email", "")).strip().lower()
        response_payload = {
            "detail": "Si un compte existe pour cet email, un lien de reinitialisation a ete envoye."
        }
        if not email:
            return Response(response_payload)

        user = User.objects.filter(
            email__iexact=email, is_active=True, participant_dfir_profile__isnull=False
        ).first()
        if user is None:
            return Response(response_payload)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"{getattr(settings, 'FRONTEND_BASE_URL', '')}/dfir/mot-de-passe-oublie/confirmer?uid={uid}&token={token}"

        send_mail(
            subject="Réinitialisation de votre mot de passe — Mon espace DFIR",
            message=(
                "Vous avez demandé la réinitialisation du mot de passe de votre espace de formation LANEMA (DFIR).\n\n"
                f"Lien de réinitialisation : {reset_link}\n\n"
                "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email."
            ),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[user.email],
            fail_silently=True,
        )
        return Response(response_payload)


class ParticipantPasswordResetConfirmView(APIView):
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
            user = User.objects.get(pk=user_id, participant_dfir_profile__isnull=False)
        except Exception:
            return Response({"detail": "Lien invalide"}, status=400)

        if not default_token_generator.check_token(user, token):
            return Response({"detail": "Lien invalide ou expiré"}, status=400)

        try:
            validate_password(new_password, user=user)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=400)

        user.set_password(new_password)
        user.save(update_fields=["password"])
        return Response({"detail": "Mot de passe mis à jour"})
