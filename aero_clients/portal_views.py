"""Portail client DAE — cf. cahier des charges section 3.7 : un client
(compagnie aérienne, forces armées...) peut déposer une demande, suivre son
dossier, consulter l'état de l'intervention, télécharger rapports/certificats,
consulter ses factures, donner une note, déposer une réclamation — sans
compte staff. Auth JWT dédiée (email + mot de passe), distincte de
core.UserProfile (staff) et de clients.ClientProfile (portail labo)."""
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenViewBase

from aero_finance.models import FactureDAE
from aero_finance.pdf_utils import generate_facture_dae_pdf
from aero_maintenance.models import CertificatDAE, OrdreTravail
from aero_maintenance.pdf_utils import generate_certificat_ot_pdf
from core.pdf_utils import create_pdf_response

from .models import Aeronef, ClientAeronautique, DemandeDAE, ReclamationClientDAE, SatisfactionDAE
from .portal_serializers import (
    ClientPortalAeronefSerializer,
    ClientPortalDemandeSerializer,
    ClientPortalFactureSerializer,
    ClientPortalOrdreTravailSerializer,
    ClientPortalProfileSerializer,
    ClientPortalReclamationSerializer,
    ClientPortalRegisterSerializer,
)

User = get_user_model()


def get_client_aeronautique(user):
    """Retourne le ClientAeronautique lié au compte portail connecté, ou None
    si ce compte n'est pas un compte client DAE (protège les vues portail
    contre un JWT staff/labo valide sur le meme domaine)."""
    return getattr(user, "client_aeronautique", None)


class IsClientPortalUser(permissions.BasePermission):
    """Authentifié ET rattaché à un ClientAeronautique (cf. get_client_aeronautique)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and get_client_aeronautique(request.user))


class ClientPortalRegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ClientPortalRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        email = data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            return Response({"error": "Un compte existe déjà avec cet email."}, status=status.HTTP_400_BAD_REQUEST)
        if ClientAeronautique.objects.filter(nom=data["nom"]).exists():
            return Response(
                {"error": "Un client aéronautique porte déjà ce nom. Contactez la DAE pour rattacher votre compte."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_password(data["password"])
        except DjangoValidationError as exc:
            return Response({"error": " ".join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=email, email=email, password=data["password"])
        client = ClientAeronautique.objects.create(
            nom=data["nom"], type_client=data.get("type_client", "AUTRE"), adresse=data.get("adresse", ""),
            telephone=data.get("telephone", ""), email=email, numero_identification=data.get("numero_identification", ""),
            contact=data.get("contact", ""), compte_utilisateur=user,
        )

        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        return Response({
            "tokens": {"access": str(refresh.access_token), "refresh": str(refresh)},
            "client": ClientPortalProfileSerializer(client).data,
        }, status=status.HTTP_201_CREATED)


class ClientPortalLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            user = User.objects.get(email__iexact=attrs["email"])
        except User.DoesNotExist:
            raise AuthenticationFailed("Aucun compte actif ne correspond à ces identifiants.", code="no_active_account")
        if not user.check_password(attrs["password"]):
            raise AuthenticationFailed("Aucun compte actif ne correspond à ces identifiants.", code="no_active_account")
        if not user.is_active:
            raise AuthenticationFailed("Ce compte est inactif.", code="inactive_account")
        client = get_client_aeronautique(user)
        if not client:
            raise AuthenticationFailed("Ce compte n'est pas rattaché à un espace client DAE.", code="not_a_client")

        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        attrs["access"] = str(refresh.access_token)
        attrs["refresh"] = str(refresh)
        attrs["client"] = client
        return attrs


class ClientPortalLoginView(TokenViewBase):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    serializer_class = ClientPortalLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        return Response({
            "tokens": {"access": validated["access"], "refresh": validated["refresh"]},
            "client": ClientPortalProfileSerializer(validated["client"]).data,
        })


class ClientPortalProfileView(APIView):
    permission_classes = [IsClientPortalUser]

    def get(self, request):
        return Response(ClientPortalProfileSerializer(get_client_aeronautique(request.user)).data)

    def patch(self, request):
        client = get_client_aeronautique(request.user)
        serializer = ClientPortalProfileSerializer(client, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ClientPortalDashboardView(APIView):
    """Vue d'ensemble du dossier client — cf. cahier des charges section 3.7 :
    suivi de dossier et état de l'intervention en un coup d'œil."""

    permission_classes = [IsClientPortalUser]

    def get(self, request):
        client = get_client_aeronautique(request.user)
        aeronefs = Aeronef.objects.filter(client=client)
        ordres = OrdreTravail.objects.filter(aeronef__client=client)
        demandes = DemandeDAE.objects.filter(client=client)
        factures = FactureDAE.objects.filter(client=client)
        reclamations = ReclamationClientDAE.objects.filter(client=client)
        satisfactions_en_attente = SatisfactionDAE.objects.filter(
            ordre_travail__aeronef__client=client, date_envoi__isnull=False, date_evaluation__isnull=True,
        ).count()

        return Response({
            "nombre_aeronefs": aeronefs.count(),
            "nombre_demandes_en_cours": demandes.exclude(statut__in=["ACCEPTEE", "REFUSEE"]).count(),
            "nombre_ordres_en_cours": ordres.exclude(statut__in=["CLOTURE", "ANNULE"]).count(),
            "nombre_factures_impayees": factures.filter(statut="IMPAYEE").count(),
            "nombre_reclamations_ouvertes": reclamations.exclude(statut="CLOTUREE").count(),
            "nombre_satisfactions_en_attente": satisfactions_en_attente,
        })


class ClientPortalAeronefViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ClientPortalAeronefSerializer
    permission_classes = [IsClientPortalUser]

    def get_queryset(self):
        return Aeronef.objects.filter(client=get_client_aeronautique(self.request.user))


class ClientPortalDemandeViewSet(viewsets.ModelViewSet):
    """Cf. cahier des charges section 3.7 : "déposer une demande" +
    "suivre son dossier". Le statut n'est jamais modifiable par le client
    (piloté par l'agent administratif via /dae/clients)."""

    serializer_class = ClientPortalDemandeSerializer
    permission_classes = [IsClientPortalUser]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return DemandeDAE.objects.filter(client=get_client_aeronautique(self.request.user)).select_related("aeronef", "ordre_travail")

    def perform_create(self, serializer):
        client = get_client_aeronautique(self.request.user)
        last_id = DemandeDAE.objects.count() + 1
        reference = f"DEM-DAE-{timezone.now().year}-{last_id:05d}"
        aeronef = serializer.validated_data.get("aeronef")
        if aeronef and aeronef.client_id != client.id:
            raise serializers.ValidationError({"aeronef": "Cet aéronef n'appartient pas à votre organisation."})
        serializer.save(client=client, reference=reference)


class ClientPortalOrdreTravailView(viewsets.ReadOnlyModelViewSet):
    """Cf. cahier des charges section 3.7 : "consulter l'état de
    l'intervention" + "télécharger les rapports/certificats"."""

    serializer_class = ClientPortalOrdreTravailSerializer
    permission_classes = [IsClientPortalUser]

    def get_queryset(self):
        return OrdreTravail.objects.filter(
            aeronef__client=get_client_aeronautique(self.request.user)
        ).select_related("aeronef", "certificat")

    @action(detail=True, methods=["get"], url_path="telecharger-certificat")
    def telecharger_certificat(self, request, pk=None):
        ordre_travail = self.get_object()
        if ordre_travail.statut not in ("TERMINE", "VALIDE", "CLOTURE"):
            return Response(
                {"error": "Le certificat n'est disponible qu'après le contrôle qualité."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        certificat, _ = CertificatDAE.objects.get_or_create(ordre_travail=ordre_travail)
        buffer = generate_certificat_ot_pdf(ordre_travail, numero_certificat=certificat.numero)
        return create_pdf_response(buffer, f"{certificat.numero}.pdf")


class ClientPortalFactureViewSet(viewsets.ReadOnlyModelViewSet):
    """Cf. cahier des charges section 3.7 : "consulter les factures"."""

    serializer_class = ClientPortalFactureSerializer
    permission_classes = [IsClientPortalUser]

    def get_queryset(self):
        return FactureDAE.objects.filter(client=get_client_aeronautique(self.request.user)).select_related("ordre_travail")

    @action(detail=True, methods=["get"], url_path="telecharger-pdf")
    def telecharger_pdf(self, request, pk=None):
        facture = self.get_object()
        buffer = generate_facture_dae_pdf(facture)
        return create_pdf_response(buffer, f"facture_{facture.reference}.pdf")


class ClientPortalReclamationViewSet(viewsets.ModelViewSet):
    """Cf. cahier des charges section 3.7 : "déposer une réclamation". Le
    client ne peut ni changer le statut ni écrire la réponse (pilotés par
    l'agent affecté via /dae/clients — cf. section 22)."""

    serializer_class = ClientPortalReclamationSerializer
    permission_classes = [IsClientPortalUser]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return ReclamationClientDAE.objects.filter(
            client=get_client_aeronautique(self.request.user)
        ).select_related("ordre_travail")

    def perform_create(self, serializer):
        client = get_client_aeronautique(self.request.user)
        ordre_travail = serializer.validated_data.get("ordre_travail")
        if ordre_travail and ordre_travail.aeronef and ordre_travail.aeronef.client_id != client.id:
            raise serializers.ValidationError({"ordre_travail": "Cet ordre de travail n'appartient pas à votre organisation."})
        serializer.save(client=client)

    def perform_update(self, serializer):
        # Seule "note_satisfaction" est modifiable par le client apres cloture
        # (cf. cahier des charges section 3.7 : "donner une note").
        instance = self.get_object()
        if instance.statut != "CLOTUREE":
            raise serializers.ValidationError({"error": "La note ne peut être donnée qu'après clôture de la réclamation."})
        serializer.save()


class ClientPortalSatisfactionView(APIView):
    """Fiches de satisfaction en attente de notation pour ce client (cf.
    cahier des charges section 21) — meme flux de soumission que le lien
    public (SatisfactionDAEPublicView), accessible ici sans ressaisir le
    token puisque le client est deja authentifie."""

    permission_classes = [IsClientPortalUser]

    def get(self, request):
        from .serializers import SatisfactionDAESerializer

        client = get_client_aeronautique(request.user)
        satisfactions = SatisfactionDAE.objects.filter(
            ordre_travail__aeronef__client=client, date_envoi__isnull=False, date_evaluation__isnull=True,
        ).select_related("ordre_travail")
        return Response(SatisfactionDAESerializer(satisfactions, many=True).data)

    def post(self, request, pk):
        client = get_client_aeronautique(request.user)
        try:
            satisfaction = SatisfactionDAE.objects.get(pk=pk, ordre_travail__aeronef__client=client)
        except SatisfactionDAE.DoesNotExist:
            return Response({"detail": "Fiche introuvable."}, status=status.HTTP_404_NOT_FOUND)
        if satisfaction.date_evaluation is not None:
            return Response({"detail": "Cette évaluation a déjà été soumise."}, status=status.HTTP_400_BAD_REQUEST)

        criteres = ["note_qualite", "note_delai", "note_accueil", "note_communication", "note_prestation_technique"]
        notes = {}
        for critere in criteres:
            valeur = request.data.get(critere)
            try:
                valeur = int(valeur)
            except (TypeError, ValueError):
                return Response({"detail": "Merci de renseigner les 5 notes (sur 5)."}, status=status.HTTP_400_BAD_REQUEST)
            if not (1 <= valeur <= 5):
                return Response({"detail": "Les notes doivent être comprises entre 1 et 5."}, status=status.HTTP_400_BAD_REQUEST)
            notes[critere] = valeur

        for critere, valeur in notes.items():
            setattr(satisfaction, critere, valeur)
        satisfaction.commentaire = request.data.get("commentaire", "")
        satisfaction.date_evaluation = timezone.now()
        satisfaction.save()
        return Response({"detail": "Merci pour votre évaluation !"})
