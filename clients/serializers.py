from django.contrib.auth.models import User
from rest_framework import serializers

from .models import ClientProfile, ReclamationClient


class ClientProfileSerializer(serializers.ModelSerializer):
    """Expose un ClientProfile avec les champs du User sous-jacent aplatis,
    pour rester compatible avec le contrat API de l'ancien clients.User."""

    id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", required=False)
    email = serializers.EmailField(source="user.email", required=False)
    first_name = serializers.CharField(source="user.first_name", required=False, allow_blank=True)
    last_name = serializers.CharField(source="user.last_name", required=False, allow_blank=True)
    is_active = serializers.BooleanField(source="user.is_active", required=False)
    nom = serializers.CharField(source="raison_sociale", required=False, allow_blank=True)

    class Meta:
        model = ClientProfile
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "type_subscription",
            "organisation",
            "raison_sociale",
            "nom",
            "adresse",
            "telephone",
            "siret",
            "contact_nom",
            "is_active",
            "signature_image",
            "cachet_image",
        ]

    def create(self, validated_data):
        user_data = validated_data.pop("user", {})
        email = user_data.get("email", "")
        raison_sociale = validated_data.get("raison_sociale", "")

        username = user_data.get("username")
        if not username:
            base = email.split("@")[0] if email else (raison_sociale.lower().replace(" ", "_") or "user")
            candidate = base
            index = 1
            while User.objects.filter(username=candidate).exists():
                candidate = f"{base}{index}"
                index += 1
            username = candidate

        user = User(
            username=username,
            email=email,
            first_name=user_data.get("first_name", ""),
            last_name=user_data.get("last_name", ""),
            is_active=user_data.get("is_active", True),
        )
        # Mot de passe temporaire (les fournisseurs ne se connectent pas forcement)
        user.set_password(f"fournisseur_{username}_temp")
        user.save()

        return ClientProfile.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        if user_data:
            for attr, value in user_data.items():
                setattr(instance.user, attr, value)
            instance.user.save()
        return super().update(instance, validated_data)


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", required=False, allow_blank=True)
    email = serializers.EmailField(source="user.email", required=False, allow_blank=True)
    first_name = serializers.CharField(source="user.first_name", required=False, allow_blank=True)
    last_name = serializers.CharField(source="user.last_name", required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = ClientProfile
        fields = [
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "role",
            "type_subscription",
            "organisation",
            "raison_sociale",
            "adresse",
            "telephone",
            "siret",
            "contact_nom",
        ]
        extra_kwargs = {
            "role": {"required": False},
            "type_subscription": {"required": False},
            "organisation": {"required": False},
            "raison_sociale": {"required": False},
            "adresse": {"required": False},
            "telephone": {"required": False},
            "siret": {"required": False},
            "contact_nom": {"required": False},
        }

    def create(self, validated_data):
        password = validated_data.pop("password")
        user_data = validated_data.pop("user", {})

        # Genere un username si non fourni (le frontend n'envoie que l'email)
        username = user_data.get("username")
        email = user_data.get("email", "")
        if not username:
            base_username = email.split("@")[0] if email else "user"
            candidate = base_username
            index = 1
            while User.objects.filter(username=candidate).exists():
                candidate = f"{base_username}{index}"
                index += 1
            username = candidate

        # Role par defaut pour les inscriptions publiques
        if not validated_data.get("role"):
            validated_data["role"] = "CLIENT"

        user = User(
            username=username,
            email=email,
            first_name=user_data.get("first_name", ""),
            last_name=user_data.get("last_name", ""),
        )
        user.set_password(password)
        user.save()

        return ClientProfile.objects.create(user=user, **validated_data)


class ReclamationClientSerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source="client.username", read_only=True)

    class Meta:
        model = ReclamationClient
        fields = [
            "id", "client", "client_nom", "description", "date_reception",
            "date_traitement", "statut", "note_satisfaction",
        ]
        read_only_fields = ["id", "date_reception"]
