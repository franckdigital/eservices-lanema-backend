from rest_framework import serializers

from .models import Bien, InventairePatrimoine, MaintenanceBien, MouvementBien


class BienSerializer(serializers.ModelSerializer):
    responsable_nom = serializers.CharField(source="responsable.username", read_only=True, default=None)

    class Meta:
        model = Bien
        fields = [
            "id", "code", "designation", "categorie", "date_acquisition", "valeur_acquisition",
            "valeur_actuelle", "duree_amortissement_ans", "statut", "localisation", "responsable",
            "responsable_nom", "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class MouvementBienSerializer(serializers.ModelSerializer):
    bien_code = serializers.CharField(source="bien.code", read_only=True)
    effectue_par_nom = serializers.CharField(source="effectue_par.username", read_only=True, default=None)

    class Meta:
        model = MouvementBien
        fields = ["id", "bien", "bien_code", "type_mouvement", "motif", "date_mouvement", "effectue_par", "effectue_par_nom"]
        read_only_fields = ["id", "date_mouvement"]


class MaintenanceBienSerializer(serializers.ModelSerializer):
    bien_code = serializers.CharField(source="bien.code", read_only=True)

    class Meta:
        model = MaintenanceBien
        fields = ["id", "bien", "bien_code", "type_maintenance", "date_maintenance", "date_fin", "cout", "description"]
        read_only_fields = ["id"]


class InventairePatrimoineSerializer(serializers.ModelSerializer):
    responsable_nom = serializers.CharField(source="responsable.username", read_only=True, default=None)

    class Meta:
        model = InventairePatrimoine
        fields = [
            "id", "date_inventaire", "responsable", "responsable_nom", "nombre_biens_verifies",
            "ecarts_constates", "observations", "created_at",
        ]
        read_only_fields = ["id", "created_at"]
