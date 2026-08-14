from rest_framework import serializers

from .models import Batiment, InterventionTechnique, PanneVehicule, ReservationSalle, Salle, Vehicule


class VehiculeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicule
        fields = ["id", "immatriculation", "marque", "modele", "statut", "kilometrage", "created_at"]
        read_only_fields = ["id", "created_at"]


class PanneVehiculeSerializer(serializers.ModelSerializer):
    vehicule_immatriculation = serializers.CharField(source="vehicule.immatriculation", read_only=True)

    class Meta:
        model = PanneVehicule
        fields = ["id", "vehicule", "vehicule_immatriculation", "date_panne", "date_reparation", "cout", "description"]
        read_only_fields = ["id", "date_panne"]


class BatimentSerializer(serializers.ModelSerializer):
    site_nom = serializers.CharField(source="site.nom", read_only=True, default=None)

    class Meta:
        model = Batiment
        fields = ["id", "nom", "site", "site_nom", "disponible", "etat"]
        read_only_fields = ["id"]


class SalleSerializer(serializers.ModelSerializer):
    batiment_nom = serializers.CharField(source="batiment.nom", read_only=True, default=None)

    class Meta:
        model = Salle
        fields = ["id", "nom", "capacite", "batiment", "batiment_nom"]
        read_only_fields = ["id"]


class ReservationSalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservationSalle
        fields = ["id", "salle", "date_debut", "date_fin", "motif"]
        read_only_fields = ["id"]


class InterventionTechniqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterventionTechnique
        fields = ["id", "batiment", "type_intervention", "date_intervention", "description"]
        read_only_fields = ["id", "date_intervention"]
