import json
import secrets
import string
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Count
from django.utils import timezone

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    CreneauDisponibilite,
    DemandeDevis,
    EchantillonPrevu,
    InterventionPrelevement,
    SousTraitantPartenaire,
)
from .serializers import CreneauDisponibiliteSerializer, DemandeDevisSerializer, SousTraitantPartenaireSerializer
from clients.models import ClientProfile
from clients.permissions_catalog import user_has_permission
from facturation.models import BonCommande, Facture, Proforma


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


def prix_unitaire_demande(type_analyse: str, categorie: str, priorite: str) -> Decimal:
    """Prix unitaire par echantillon/parametre, utilise pour figer la colonne
    P.U. de chaque ligne EchantillonPrevu (cf. formulaire EN 002-PG002,
    tableau "Paramètres ou Grandeurs")."""
    base = PRICING_BASE_TYPE.get(type_analyse, Decimal("0"))
    supplement = PRICING_SUPPLEMENTS.get(type_analyse, {}).get(categorie, Decimal("0"))
    coeff = PRIORITE_COEFFICIENTS.get(priorite or "NORMALE", Decimal("1.0"))
    return (base + supplement) * coeff


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


def delai_actuel():
    """Creneau de disponibilite applicable aujourd'hui (ou, a defaut, le
    prochain a venir), annonce sur le formulaire public de devis — parametre
    depuis l'espace du service reception (CreneauDisponibiliteViewSet)."""
    today = timezone.now().date()
    creneau = CreneauDisponibilite.objects.filter(
        actif=True, date_debut__lte=today, date_fin__gte=today
    ).order_by("date_debut").first()
    if creneau is None:
        creneau = CreneauDisponibilite.objects.filter(
            actif=True, date_debut__gte=today
        ).order_by("date_debut").first()
    return creneau


def creer_devis_et_proforma(
    client, type_analyse, categorie, objet, description, priorite, echantillons,
    accord_sous_traitance=False, sous_traitants_ids=None, sous_traitants_libres="",
    retour_materiel_gere_labo=None, lieu_realisation="LABORATOIRE",
    observations_particulieres="", declaration_conformite_souhaitee=None,
):
    """Cree une DemandeDevis + sa Proforma associee (montant calcule et fige).
    Factorise entre DemandeDevisViewSet.perform_create (client authentifie) et
    PublicDevisCreateView (formulaire public, compte cree a la volee)."""
    last_id = DemandeDevis.objects.count() + 1
    numero = f"DEV-{last_id:05d}"
    while DemandeDevis.objects.filter(numero=numero).exists():
        last_id += 1
        numero = f"DEV-{last_id:05d}"

    creneau = delai_actuel()
    demande = DemandeDevis.objects.create(
        client=client, numero=numero, type_analyse=type_analyse,
        categorie=categorie, objet=objet, description=description,
        delai_realisation_jours=creneau.delai_jours_ouvres if creneau else None,
        accord_sous_traitance=bool(accord_sous_traitance),
        sous_traitants_souhaits_libres=sous_traitants_libres or "",
        retour_materiel_gere_labo=retour_materiel_gere_labo,
        lieu_realisation=lieu_realisation or "LABORATOIRE",
        observations_particulieres=observations_particulieres or "",
        declaration_conformite_souhaitee=declaration_conformite_souhaitee,
    )
    if sous_traitants_ids:
        demande.sous_traitants_choisis.set(
            SousTraitantPartenaire.objects.filter(id__in=sous_traitants_ids)
        )
    pu = prix_unitaire_demande(type_analyse, categorie, priorite)
    EchantillonPrevu.objects.bulk_create([
        EchantillonPrevu(
            demande=demande, nom=(e.get("nom") or "").strip() or "Échantillon", quantite=e.get("quantite") or 1,
            prix_unitaire=pu,
        )
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
        if isinstance(echantillons, str):
            try:
                echantillons = json.loads(echantillons)
            except (TypeError, ValueError):
                echantillons = []
        if not type_analyse or not objet:
            return Response({"detail": "Type d'analyse et objet requis."}, status=status.HTTP_400_BAD_REQUEST)

        first_name = str(data.get("first_name", "")).strip()
        last_name = str(data.get("last_name", "")).strip()
        raison_sociale = str(data.get("raison_sociale", "")).strip()
        telephone = str(data.get("telephone", "")).strip()
        domaine_activite = str(data.get("domaine_activite", "")).strip()
        situation_geographique = str(data.get("situation_geographique", "")).strip()
        adresse = str(data.get("adresse", "")).strip()

        accord_sous_traitance = str(data.get("accord_sous_traitance", "")).lower() in ("true", "1", "on")
        sous_traitants_libres = str(data.get("sous_traitants_libres", "")).strip()
        sous_traitants_raw = data.get("sous_traitants_choisis")
        if isinstance(sous_traitants_raw, str):
            try:
                sous_traitants_raw = json.loads(sous_traitants_raw)
            except (TypeError, ValueError):
                sous_traitants_raw = []
        sous_traitants_ids = [i for i in (sous_traitants_raw or []) if i not in (None, "")]

        lieu_realisation = str(data.get("lieu_realisation", "LABORATOIRE")).strip() or "LABORATOIRE"
        observations_particulieres = str(data.get("observations_particulieres", "")).strip()

        def _parse_bool_optionnel(key):
            raw = data.get(key)
            if raw in (None, ""):
                return None
            return str(raw).lower() in ("true", "1", "on", "oui")

        retour_materiel_gere_labo = _parse_bool_optionnel("retour_materiel_gere_labo")
        declaration_conformite_souhaitee = _parse_bool_optionnel("declaration_conformite_souhaitee")

        signature = request.FILES.get("signature_client_image")

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
                adresse=adresse,
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
            if adresse and not profile.adresse:
                profile.adresse = adresse
                updated_fields.append("adresse")
            if updated_fields:
                profile.save(update_fields=updated_fields)

        demande, proforma = creer_devis_et_proforma(
            client=user, type_analyse=type_analyse, categorie=categorie, objet=objet,
            description=description, priorite=priorite, echantillons=echantillons,
            retour_materiel_gere_labo=retour_materiel_gere_labo, lieu_realisation=lieu_realisation,
            observations_particulieres=observations_particulieres,
            declaration_conformite_souhaitee=declaration_conformite_souhaitee,
            accord_sous_traitance=accord_sous_traitance, sous_traitants_ids=sous_traitants_ids,
            sous_traitants_libres=sous_traitants_libres,
        )

        bon_pour_accord = False
        if signature is not None:
            bon_pour_accord = True
            proforma.statut = "ACCEPTEE"
            proforma.save(update_fields=["statut"])
            demande.statut = "ACCEPTEE"
            demande.save(update_fields=["statut"])

            suffixe = proforma.numero.split("-")[-1]
            bc_numero = f"BC-{suffixe}"
            if BonCommande.objects.filter(numero=bc_numero).exists():
                bc_numero = f"BC-{BonCommande.objects.count() + 1:05d}"
            bon_commande = BonCommande.objects.create(
                numero=bc_numero, client=user, proforma=proforma,
                montant_ht=proforma.montant_ht, montant_ttc=proforma.montant_ttc, devise=proforma.devise,
                statut="SIGNE_CLIENT", signature_client_image=signature, date_signature_client=timezone.now().date(),
            )
            fac_numero = f"FAC-{suffixe}"
            if Facture.objects.filter(numero=fac_numero).exists():
                fac_numero = f"FAC-{Facture.objects.count() + 1:05d}"
            date_emission = timezone.now().date()
            facture = Facture.objects.create(
                numero=fac_numero, client=user, proforma=proforma, bon_commande=bon_commande,
                montant_ht=proforma.montant_ht, montant_ttc=proforma.montant_ttc, devise=proforma.devise,
                statut="EN_ATTENTE", date_emission=date_emission, date_echeance=date_emission + timedelta(days=30),
                visible_client=True,
            )
            # Import local pour eviter une dependance circulaire au chargement du module.
            from facturation.views import _creer_demande_analyse_si_absente
            _creer_demande_analyse_si_absente(facture)

        espace_url = f"{getattr(settings, 'FRONTEND_BASE_URL', 'https://e-services.lanema-ci.com')}/devis/connexion"
        delai_txt = f"{demande.delai_realisation_jours} jours ouvres" if demande.delai_realisation_jours else "24h ouvrees"
        if compte_cree:
            subject = "Votre compte client LANEMA et votre demande de devis"
            message = (
                f"Bonjour {first_name or ''},\n\n"
                f"Votre demande de devis {demande.numero} a bien ete enregistree aupres du laboratoire LANEMA"
                f"{' et signee (bon pour accord)' if bon_pour_accord else ''}.\n"
                f"Elle sera traitee sous {delai_txt}.\n\n"
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
                f"Votre demande de devis {demande.numero} a bien ete enregistree aupres du laboratoire LANEMA"
                f"{' et signee (bon pour accord)' if bon_pour_accord else ''}.\n"
                f"Elle sera traitee sous {delai_txt}.\n\n"
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
            "delai_realisation_jours": demande.delai_realisation_jours,
            "bon_pour_accord": bon_pour_accord,
        }, status=status.HTTP_201_CREATED)


class DelaiActuelView(APIView):
    """Delai de realisation actuellement annonce (cf. CreneauDisponibilite) —
    consulte publiquement par le formulaire de demande de devis."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        creneau = delai_actuel()
        if creneau is None:
            return Response({"delai_jours_ouvres": None, "label": None})
        return Response(CreneauDisponibiliteSerializer(creneau).data)


class CreneauDisponibiliteViewSet(viewsets.ModelViewSet):
    """Parametrage des plages de disponibilite (service reception) — cf.
    cahier des charges EN 002-PG002, champ "Delais de realisation" du devis."""

    queryset = CreneauDisponibilite.objects.all()
    serializer_class = CreneauDisponibiliteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _check_labo_staff(self):
        if not user_has_permission(self.request.user, "echantillons.manage"):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seul le personnel du laboratoire peut gerer les delais.")

    def perform_create(self, serializer):
        self._check_labo_staff()
        serializer.save()

    def perform_update(self, serializer):
        self._check_labo_staff()
        serializer.save()

    def perform_destroy(self, instance):
        self._check_labo_staff()
        instance.delete()


class SousTraitantPartenaireViewSet(viewsets.ModelViewSet):
    """Catalogue des sous-traitants (partenaires officiels LANEMA + sous-traitants
    souhaites par des clients, formalises par le service reception) — la liste
    des partenaires actifs est consultable publiquement depuis le formulaire
    de devis (choix du client), la gestion est reservee au personnel labo."""

    queryset = SousTraitantPartenaire.objects.all()
    serializer_class = SousTraitantPartenaireSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list" and not (self.request.user and self.request.user.is_authenticated):
            # Formulaire public : uniquement les partenaires officiels actifs.
            queryset = queryset.filter(actif=True, type_sous_traitant="PARTENAIRE")
        type_filter = self.request.query_params.get("type")
        if type_filter:
            queryset = queryset.filter(type_sous_traitant=type_filter)
        return queryset

    def _check_labo_staff(self):
        if not user_has_permission(self.request.user, "echantillons.manage"):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seul le personnel du laboratoire peut gerer les sous-traitants.")

    def perform_create(self, serializer):
        self._check_labo_staff()
        serializer.save()

    def perform_update(self, serializer):
        self._check_labo_staff()
        serializer.save()

    def perform_destroy(self, instance):
        self._check_labo_staff()
        instance.delete()


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

    @action(detail=True, methods=["post"], url_path="interventions_prelevement")
    def definir_interventions_prelevement(self, request, pk=None):
        """Renseigne (service reception) le tableau "2 - Prélèvement ou
        récupération de l'appareil de mesure" du devis officiel : duree,
        kilometrage, nombre et prix unitaire pour chacune des 5 designations
        fixes. Le frontend envoie la liste complete a chaque enregistrement
        (upsert par designation)."""

        if not user_has_permission(request.user, "echantillons.manage"):
            return Response({"detail": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)

        demande = self.get_object()
        lignes = request.data if isinstance(request.data, list) else request.data.get("lignes", [])
        designations_valides = dict(InterventionPrelevement.DESIGNATION_CHOICES)

        for ligne in lignes:
            designation = ligne.get("designation")
            if designation not in designations_valides:
                continue
            InterventionPrelevement.objects.update_or_create(
                demande=demande, designation=designation,
                defaults={
                    "duree_heures": ligne.get("duree_heures") or None,
                    "km": ligne.get("km") or None,
                    "nombre": ligne.get("nombre") or 0,
                    "prix_unitaire": ligne.get("prix_unitaire") or 0,
                },
            )

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
