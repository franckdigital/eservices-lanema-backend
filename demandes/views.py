from decimal import Decimal

from django.db.models import Count

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DemandeDevis
from .serializers import DemandeDevisSerializer
from facturation.models import Proforma


TVA_RATE = Decimal("0.1925")  # 19,25 %


PRICING_BASE_TYPE = {
    "MICROBIOLOGIE_PARASITOLOGIE": Decimal("60000"),
    "CHIMIE_ALIMENTAIRE_INDUSTRIELLE": Decimal("55000"),
    "EAUX_CONSOMMATION": Decimal("45000"),
    "SOLS_ENGRAIS": Decimal("50000"),
    "METROLOGIE": Decimal("80000"),
    "ETALONNAGE_INSTRUMENTS": Decimal("70000"),
    "ETALONNAGE_VERRERIE": Decimal("35000"),
}


PRICING_SUPPLEMENTS = {
    "MICROBIOLOGIE_PARASITOLOGIE": {
        "Analyses microbiologiques des eaux": Decimal("0"),
        "Analyses microbiologiques des aliments": Decimal("10000"),
        "Recherche de parasites": Decimal("15000"),
        "Contrle de strilit": Decimal("20000"),
        "Autres analyses microbiologiques": Decimal("5000"),
    },
    "CHIMIE_ALIMENTAIRE_INDUSTRIELLE": {
        "Analyses physico-chimiques des eaux": Decimal("0"),
        "Analyses chimiques des aliments": Decimal("10000"),
        "Analyses de produits industriels": Decimal("15000"),
        "Contrle qualit produits": Decimal("10000"),
        "Autres analyses chimiques": Decimal("5000"),
    },
    "EAUX_CONSOMMATION": {
        "Eau potable du robinet": Decimal("0"),
        "Eau de puits": Decimal("5000"),
        "Eau de forage": Decimal("5000"),
        "Eau minrale": Decimal("10000"),
        "Eau de source": Decimal("5000"),
    },
    "SOLS_ENGRAIS": {
        "Analyse de sol agricole": Decimal("5000"),
        "Analyse de compost": Decimal("5000"),
        "Analyse d'engrais": Decimal("10000"),
        "Analyse de substrats": Decimal("10000"),
        "Autres analyses de sols": Decimal("5000"),
    },
    "METROLOGIE": {
        "talonnage de masse": Decimal("0"),
        "talonnage de pression": Decimal("0"),
        "talonnage de temprature": Decimal("0"),
        "talonnage lectrique": Decimal("10000"),
        "Autres talonnages": Decimal("15000"),
    },
    "ETALONNAGE_INSTRUMENTS": {
        "Instruments de mesure de pression": Decimal("0"),
        "Instruments de mesure de masse": Decimal("0"),
        "Cls dynamomtriques": Decimal("10000"),
        "Instruments de temprature": Decimal("0"),
        "Appareils lectriques": Decimal("10000"),
    },
    "ETALONNAGE_VERRERIE": {
        "Pipettes": Decimal("0"),
        "Burettes": Decimal("0"),
        "Fioles jauges": Decimal("5000"),
        "prouvettes gradues": Decimal("0"),
        "Autres verreries": Decimal("5000"),
    },
}


PRIORITE_COEFFICIENTS = {
    "NORMALE": Decimal("1.0"),
    "HAUTE": Decimal("1.2"),
    "URGENTE": Decimal("1.5"),
}


def calculer_montant_demande(type_analyse: str, categorie: str, priorite: str, echantillons) -> tuple[Decimal, Decimal]:
    """Calcule montant HT et TTC pour une demande de devis.

    - type_analyse: code du type (MICROBIOLOGIE_PARASITOLOGIE, ...)
    - categorie: libell de la catgorie
    - priorite: NORMALE / HAUTE / URGENTE
    - echantillons: liste de dicts avec au moins 'quantite'
    """

    base = PRICING_BASE_TYPE.get(type_analyse, Decimal("0"))
    supplements_par_type = PRICING_SUPPLEMENTS.get(type_analyse, {})
    supplement = supplements_par_type.get(categorie, Decimal("0"))
    coeff = PRIORITE_COEFFICIENTS.get(priorite or "NORMALE", Decimal("1.0"))

    # Prix unitaire par chantillon
    prix_unitaire = (base + supplement) * coeff

    # Nombre total "units" d'chantillons
    total_unites = Decimal("0")
    try:
        for e in echantillons or []:
            qte = e.get("quantite", 1) or 1
            total_unites += Decimal(str(qte))
    except Exception:
        total_unites = Decimal("1")

    montant_ht = (prix_unitaire * total_unites).quantize(Decimal("1"))
    montant_tva = (montant_ht * TVA_RATE).quantize(Decimal("1"))
    montant_ttc = montant_ht + montant_tva
    return montant_ht, montant_ttc


class DemandeDevisViewSet(viewsets.ModelViewSet):
    queryset = DemandeDevis.objects.select_related("client").all()
    serializer_class = DemandeDevisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Si aucun client explicite, utiliser l'utilisateur courant
        client = serializer.validated_data.get("client") or self.request.user
        # Génération simple d'un numéro de devis (peut être améliorée plus tard)
        if not serializer.validated_data.get("numero"):
            last_id = DemandeDevis.objects.count() + 1
            numero = f"DEV-{last_id:05d}"
        else:
            numero = serializer.validated_data["numero"]
        demande = serializer.save(client=client, numero=numero)

        # Calculer les montants de la proforma à partir de la demande
        type_analyse = serializer.validated_data.get("type_analyse", "")
        categorie = serializer.validated_data.get("categorie", "")
        priorite = serializer.initial_data.get("priorite", "NORMALE")
        echantillons = serializer.initial_data.get("echantillons", [])

        montant_ht, montant_ttc = calculer_montant_demande(
            type_analyse=type_analyse,
            categorie=categorie,
            priorite=priorite,
            echantillons=echantillons,
        )

        # Générer automatiquement une proforma (devis côté facturation)
        last_proforma_id = Proforma.objects.count() + 1
        proforma_numero = f"PROF-{last_proforma_id:05d}"
        Proforma.objects.create(
            numero=proforma_numero,
            client=client,
            montant_ht=montant_ht,
            montant_ttc=montant_ttc,
            devise="FCFA",
            statut="BROUILLON",
            demande_devis=demande,
        )

    @action(detail=False, methods=["get"], url_path="mes_demandes")
    def mes_demandes(self, request):
        qs = self.get_queryset().filter(client=request.user)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="accepter")
    def accepter(self, request, pk=None):
        demande = self.get_object()
        demande.statut = "ACCEPTEE"
        demande.save(update_fields=["statut"])
        serializer = self.get_serializer(demande)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="refuser")
    def refuser(self, request, pk=None):
        demande = self.get_object()
        demande.statut = "REFUSEE"
        demande.save(update_fields=["statut"])
        serializer = self.get_serializer(demande)
        return Response(serializer.data)


class DemandesDashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = DemandeDevis.objects.all()
        # Pour l'espace client, renvoyer uniquement les stats du client connecté.
        # Les rôles staff (admin/technicien/etc.) conservent une vue globale.
        client_profile = getattr(request.user, "client_profile", None)
        if not getattr(request.user, "is_staff", False) or getattr(client_profile, "role", None) == "CLIENT":
            qs = qs.filter(client=request.user)
        data = {
            "total_demandes": qs.count(),
            "en_attente": qs.filter(statut="EN_ATTENTE").count(),
            "en_cours": qs.filter(statut="EN_COURS").count(),
            "acceptees": qs.filter(statut="ACCEPTEE").count(),
        }
        resp = Response(data)
        resp["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp["Pragma"] = "no-cache"
        return resp


class TypesAnalyseView(APIView):
    """Retourne la liste des types d'analyse disponibles"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        types = [
            {"id": "MICROBIOLOGIE_PARASITOLOGIE", "nom": "Microbiologie / Parasitologie"},
            {"id": "CHIMIE_ALIMENTAIRE_INDUSTRIELLE", "nom": "Chimie alimentaire et industrielle"},
            {"id": "EAUX_CONSOMMATION", "nom": "Eaux de consommation"},
            {"id": "SOLS_ENGRAIS", "nom": "Sols et engrais"},
            {"id": "METROLOGIE", "nom": "Métrologie"},
            {"id": "ETALONNAGE_INSTRUMENTS", "nom": "Étalonnage d'instruments"},
            {"id": "ETALONNAGE_VERRERIE", "nom": "Étalonnage de verrerie"},
        ]
        return Response(types)


class DemandesSimpleView(APIView):
    """Retourne une liste simplifiée des demandes d'analyse pour les sélecteurs"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        demandes = DemandeDevis.objects.filter(
            statut__in=["EN_ATTENTE", "EN_COURS", "ACCEPTEE"]
        ).values("id", "numero", "type_analyse", "client__email")
        result = [
            {
                "id": d["id"],
                "numero": d["numero"],
                "type_analyse": d["type_analyse"],
                "client_email": d["client__email"],
                "label": f"{d['numero']} - {d['type_analyse']}"
            }
            for d in demandes
        ]
        return Response(result)
