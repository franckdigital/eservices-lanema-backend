from django.contrib.auth.models import User
from rest_framework import serializers

from .models import EntrepriseDFIR, ParticipantDFIR


class EntrepriseDFIRSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntrepriseDFIR
        fields = ["id", "nom", "secteur_activite", "contact", "actif", "created_at"]
        read_only_fields = ["id", "created_at"]


class ParticipantDFIRSerializer(serializers.ModelSerializer):
    entreprise_nom = serializers.CharField(source="entreprise.nom", read_only=True, default=None)
    a_un_compte = serializers.SerializerMethodField()

    class Meta:
        model = ParticipantDFIR
        fields = ["id", "nom", "prenom", "entreprise", "entreprise_nom", "email", "created_at", "a_un_compte"]
        read_only_fields = ["id", "created_at", "a_un_compte"]

    def get_a_un_compte(self, obj):
        return obj.user_id is not None


# ── Authentification "mon espace" (compte participant, email + mot de passe) ──

class ParticipantAuthProfileSerializer(serializers.ModelSerializer):
    """Profil renvoye apres connexion/inscription : identite du participant +
    quelques infos du compte Django sous-jacent."""

    email = serializers.EmailField(source="user.email", read_only=True)
    is_active = serializers.BooleanField(source="user.is_active", read_only=True)
    entreprise_nom = serializers.CharField(source="entreprise.nom", read_only=True, default=None)

    class Meta:
        model = ParticipantDFIR
        fields = ["id", "nom", "prenom", "email", "entreprise", "entreprise_nom", "is_active"]
        read_only_fields = fields


class ParticipantRegisterSerializer(serializers.Serializer):
    """Inscription libre-service : cree (ou recupere) le ParticipantDFIR
    correspondant a l'email, cree le compte Django, et associe les deux.
    Si un ParticipantDFIR existe deja pour cet email (saisi par le staff lors
    d'une inscription a une session) mais sans compte, on le rattache plutot
    que d'en creer un doublon."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    nom = serializers.CharField(max_length=255)
    prenom = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Un compte existe deja pour cet email.")
        return value

    def create(self, validated_data):
        email = validated_data["email"]
        nom = validated_data["nom"]
        prenom = validated_data.get("prenom", "")

        base_username = f"dfir_{email.split('@')[0]}"
        username = base_username
        index = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{index}"
            index += 1

        user = User(username=username, email=email, first_name=prenom, last_name=nom)
        user.set_password(validated_data["password"])
        user.save()

        participant = ParticipantDFIR.objects.filter(email__iexact=email, user__isnull=True).first()
        if participant:
            participant.user = user
            participant.nom = nom
            participant.prenom = prenom or participant.prenom
            participant.save(update_fields=["user", "nom", "prenom"])
        else:
            participant = ParticipantDFIR.objects.create(user=user, email=email, nom=nom, prenom=prenom)

        return participant
