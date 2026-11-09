import secrets
import string
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Count

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DemandeDevis, EchantillonPrevu
from .serializers import DemandeDevisSerializer
from clients.models import ClientProfile
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


def creer_devis_et_proforma(client, type_analyse, categorie, objet, description, priorite, echantillons):
    """Cree une DemandeDevis + sa Proforma associee (montant calcule et fige).
    Factorise entre DemandeDevisViewSet.perform_create (client authentifie) et
    PublicDevisCreateView (formulaire public, compte cree a la volee)."""
    last_id = DemandeDevis.objects.count() + 1
    numero = f"DEV-{last_id:05d}"
    while DemandeDevis.objects.filter(numero=numero).exists():
        last_id += 1
        numero = f"DEV-{last_id:05d}"

    demande = DemandeDevis.objects.create(
        client=client, numero=numero, type_analyse=type_analyse,
        categorie=categorie, objet=objet, description=description,
    )
    EchantillonPrevu.objects.bulk_create([
        EchantillonPrevu(demande=demande, nom=(e.get("nom") or "").strip() or "Échantillon", quantite=e.get("quantite") or 1)
        for e in (echantillons or [])
    ])

    montant_ht, montant_ttc = calculer_montant_demande(
        type_analyse=type_analyse, categorie=categorie, priorite=priorite, echantillons=echantillons,
    )

    suffixe = numero.split("-")[-1]
    proforma_numero = f"PROF-{suffixe}"
    if Proforma.objects.filter(numero=proforma_numero).exists():
        last_proforma_id = Proforma.objects.count() + 1
        proforma_numero = f"PROF-{last_proforma_id:05d}"
    proforma = Proforma.objects.create(
        numero=proforma_numero, client=client, montant_ht=montant_ht, montant_ttc=montant_ttc,
        devise="FCFA", statut="BROUILLON", demande_devis=demande,
    )
    return demande, proforma


def _generer_mot_de_passe():
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(10))


def _generer_username(email, first_name="", raison_sociale=""):
    base = email.split("@")[0] if email else (raison_sociale.lower().replace(" ", "_") or "client")
    candidate = base
    index = 1
    while User.objects.filter(username=candidate).exists():
        candidate = f"{base}{index}"
        index += 1
    return candidate


class PublicDevisCreateView(APIView):
    """Formulaire public (sans authentification) de demande de devis — cf.
    refonte du parcours client : le client remplit directement le formulaire
    (essais/analyses ou metrologie), son compte client est cree automatiquement
    et ses identifiants lui sont envoyes par email."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        data = request.data or {}
        email = str(data.get("email", "")).strip().lower()
        if not email:
            return Response({"detail": "L'adresse email est requise."}, status=status.HTTP_400_BAD_REQUEST)

        type_analyse = str(data.get("type_analyse", "")).strip()
        categorie = str(data.get("categorie", "")).strip()
        objet = str(data.get("objet", "")).strip()
        description = str(data.get("description", "")).strip()
        priorite = str(data.get("priorite", "NORMALE")).strip()
        echantillons = data.get("echantillons") or []
        if not type_analyse or not objet:
            return Response({"detail": "Type d'analyse et objet requis."}, status=status.HTTP_400_BAD_REQUEST)

        first_name = str(data.get("first_name", "")).strip()
        last_name = str(data.get("last_name", "")).strip()
        raison_sociale = str(data.get("raison_sociale", "")).strip()
        telephone = str(data.get("telephone", "")).strip()
        domaine_activite = str(data.get("domaine_activite", "")).strip()
        situation_geographique = str(data.get("situation_geographique", "")).strip()

        user = User.objects.filter(email__iexact=email).first()
        compte_cree = False
        mot_de_passe = None

        if user is None:
            compte_cree = True
            mot_de_passe = _generer_mot_de_passe()
            username = _generer_username(email, first_name, raison_sociale)
            user = User(username=username, email=email, first_name=first_name, last_name=last_name)
            user.set_password(mot_de_passe)
            user.save()
            ClientProfile.objects.create(
                user=user, role="CLIENT", raison_sociale=raison_sociale,
                telephone=telephone, contact_nom=f"{first_name} {last_name}".strip(),
                domaine_activite=domaine_activite, situation_geographique=situation_geographique,
            )
        else:
            # Compte deja existant (demande precedente) : on complete le profil
            # s'il manque des informations, sans toucher au mot de passe.
            profile, _ = ClientProfile.objects.get_or_create(user=user, defaults={"role": "CLIENT"})
            updated_fields = []
            if domaine_activite and not profile.domaine_activite:
                profile.domaine_activite = domaine_activite
                updated_fields.append("domaine_activite")
            if situation_geographique and not profile.situation_geographique:
                profile.situation_geographique = situation_geographique
                updated_fields.append("situation_geographique")
            if raison_sociale and not profile.raison_sociale:
                profile.raison_sociale = raison_sociale
                updated_fields.append("raison_sociale")
            if telephone and not profile.telephone:
                profile.telephone = telephone
                updated_fields.append("telephone")
            if updated_fields:
                profile.save(update_fields=updated_fields)

        demande, proforma = creer_devis_et_proforma(
            client=user, type_analyse=type_analyse, categorie=categorie, objet=objet,
            description=description, priorite=priorite, echantillons=echantillons,
        )

        espace_url = f"{getattr(settings, 'FRONTEND_BASE_URL', 'https://e-services.lanema-ci.com')}/devis/connexion"
        if compte_cree:
            subject = "Votre compte client LANEMA et votre demande de devis"
            message = (
                f"Bonjour {first_name or ''},\n\n"
                f"Votre demande de devis {demande.numero} a bien ete enregistree aupres du laboratoire LANEMA.\n\n"
                "Un espace client a ete cree automatiquement pour vous permettre de suivre votre dossier :\n"
                f"  - Identifiant (email) : {email}\n"
                f"  - Mot de passe : {mot_de_passe}\n\n"
                f"Connectez-vous ici : {espace_url}\n\n"
                "Nous vous recommandons de changer ce mot de passe depuis votre profil des votre premiere connexion.\n\n"
                "L'equipe LANEMA"
            )
        else:
            subject = "Nouvelle demande de devis enregistree"
            message = (
                f"Bonjour {first_name or ''},\n\n"
                f"Votre demande de devis {demande.numero} a bien ete enregistree aupres du laboratoire LANEMA.\n\n"
                f"Suivez son avancement depuis votre espace client : {espace_url}\n\n"
                "L'equipe LANEMA"
            )
        try:
            send_mail(
                subject=subject, message=message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[email], fail_silently=True,
            )
        except Exception:
            pass

        return Response({
            "numero": demande.numero,
            "montant_ht": str(proforma.montant_ht),
            "montant_ttc": str(proforma.montant_ttc),
            "email": email,
            "telephone": telephone,
            "compte_cree": compte_cree,
            "mot_de_passe": mot_de_passe,
            "code_client": getattr(getattr(user, "client_profile", None), "code_client", None),
            "espace_url": espace_url,
        }, status=status.HTTP_201_CREATED)


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
        EchantillonPrevu.objects.bulk_create([
            EchantillonPrevu(demande=demande, nom=(e.get("nom") or "").strip() or "Échantillon", quantite=e.get("quantite") or 1)
            for e in (echantillons or [])
        ])

        montant_ht, montant_ttc = calculer_montant_demande(
            type_analyse=type_analyse,
            categorie=categorie,
            priorite=priorite,
            echantillons=echantillons,
        )

        # Générer automatiquement une proforma (devis côté facturation) en
        # reprenant le meme suffixe numerique que la demande de devis
        # (DEV-00013 -> PROF-00013), pour eviter la confusion entre les
        # numeros des differents documents d'un meme dossier.
        suffixe = numero.split("-")[-1]
        proforma_numero = f"PROF-{suffixe}"
        if Proforma.objects.filter(numero=proforma_numero).exists():
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
