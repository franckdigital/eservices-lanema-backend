"""
Cree (ou reinitialise) le compte de demonstration du responsable du service
reception, un client de demonstration et trois devis d'exemple a differents
stades (a completer / envoye / sous-traitance demandee), afin de visualiser le
tableau de bord « Service Réception » et la fiche de devis.

Idempotent : relancer la commande remet les comptes a leur etat de demonstration
sans dupliquer les devis.
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from clients.models import ClientProfile, LaboRolePermission
from clients.permissions_catalog import DEFAULT_ROLE_PERMISSIONS
from demandes.models import CreneauDisponibilite, DemandeDevis, SousTraitantPartenaire
from demandes.views import creer_devis_et_proforma

COMPTABLE_EMAIL = "facturation@demo.com"
COMPTABLE_PASSWORD = "Facture@2026"
RECEPTION_EMAIL = "reception@demo.com"
RECEPTION_PASSWORD = "Reception@2026"
CLIENT_EMAIL = "client.devis@demo.com"
CLIENT_PASSWORD = "Client@2026"
TECH_EMAIL = "technicien.labo@demo.com"
TECH_PASSWORD = "Labo@2026"


class Command(BaseCommand):
    help = "Cree le compte demo du responsable du service reception + des devis d'exemple"

    def _compte(self, email, password, first_name, last_name, role, **profil):
        user, _ = User.objects.get_or_create(
            email=email, defaults={"username": email.split("@")[0], "first_name": first_name, "last_name": last_name},
        )
        user.first_name, user.last_name = first_name, last_name
        user.is_active = True
        user.set_password(password)
        user.save()
        ClientProfile.objects.update_or_create(user=user, defaults={"role": role, **profil})
        return user

    def _impaye_demo(self, client):
        """Devis approuve et facture emise, mais reglement non encore valide : les travaux sont bloques."""
        import io

        from django.core.files.base import ContentFile
        from PIL import Image

        from facturation.views import _accepter_proforma, _signer_bon_commande

        buf = io.BytesIO()
        Image.new("RGB", (160, 60), "white").save(buf, "PNG")
        _, proforma = creer_devis_et_proforma(
            client=client, type_analyse="EAUX_CONSOMMATION", categorie="Eau de boisson", objet="Eaux de puits — suivi trimestriel (règlement en attente)",
            description="Dossier de démonstration : en attente de règlement", priorite="NORMALE", echantillons=[{"nom": "Eau de puits P1", "quantite": 2}],
        )
        proforma.statut, proforma.lu_approuve, proforma.lu_approuve_le, proforma.lu_approuve_par = "ENVOYEE", True, timezone.now(), client
        proforma.save()
        _signer_bon_commande(_accepter_proforma(proforma), ContentFile(buf.getvalue(), name="signature.png"))

    def _regler(self, proforma, mode="CHEQUE", reference="CHQ-0001"):
        """Le service facturation valide le reglement : les travaux sont autorises."""
        from facturation.models import Facture
        from facturation.travaux import autoriser_travaux

        facture = Facture.objects.get(proforma=proforma)
        facture.mode_paiement, facture.reference_paiement, facture.visible_client = mode, reference, True
        if mode == "BON_COMMANDE":
            facture.statut = "ENGAGEE"
        else:
            facture.statut, facture.paiement_valide, facture.date_paiement = "PAYEE", True, timezone.now().date()
        facture.save()
        autoriser_travaux(facture, self.comptable)

    def handle(self, *args, **options):
        # Permissions du role RECEPTION (deja semees par migration ; garde-fou)
        for code in DEFAULT_ROLE_PERMISSIONS["RECEPTION"]:
            LaboRolePermission.objects.get_or_create(role="RECEPTION", permission_code=code, defaults={"is_granted": True})

        reception = self._compte(
            RECEPTION_EMAIL, RECEPTION_PASSWORD, "Responsable", "Service Réception", "RECEPTION",
            organisation="LANEMA — Service de réception des objets",
            telephone="01 43 11 01 01",
        )
        client = self._compte(
            CLIENT_EMAIL, CLIENT_PASSWORD, "Koffi", "Yao", "CLIENT",
            organisation="SOCIÉTÉ DÉMO AGRO-INDUSTRIE",
            raison_sociale="SOCIÉTÉ DÉMO AGRO-INDUSTRIE SARL",
            adresse="Zone industrielle de Yopougon, lot 24",
            telephone="07 07 12 34 56",
            contact_nom="M. Koffi Yao",
            code_client="CL-DEMO-001",
            domaine_activite="Agro-alimentaire",
            situation_geographique="Abidjan — Yopougon",
        )

        technicien = self._compte(
            TECH_EMAIL, TECH_PASSWORD, "Aïcha", "Koné", "TECHNICIEN", organisation="LANEMA — Direction des Essais et Analyses",
        )

        comptable = self._compte(
            COMPTABLE_EMAIL, COMPTABLE_PASSWORD, "Marie", "Service Facturation", "COMPTABLE", organisation="LANEMA — Service facturation et caisse",
        )
        for code in DEFAULT_ROLE_PERMISSIONS["COMPTABLE"]:
            LaboRolePermission.objects.get_or_create(role="COMPTABLE", permission_code=code, defaults={"is_granted": True})
        self.comptable = comptable

        # Compte DMCT (e-diligence) pour l'espace « Fiches d'exécution & certificats »
        from django.core.management import call_command

        call_command("seed_direction_demo_accounts", stdout=self.stdout)

        today = timezone.now().date()
        if not CreneauDisponibilite.objects.filter(actif=True, date_debut__lte=today, date_fin__gte=today).exists():
            CreneauDisponibilite.objects.create(
                date_debut=today - timedelta(days=30), date_fin=today + timedelta(days=330),
                delai_jours_ouvres=10, label="Délai standard",
            )

        st_metro, _ = SousTraitantPartenaire.objects.get_or_create(
            nom="Partenaire Démo — Métrologie électrique",
            defaults={"specialite": "Étalonnage électrique", "contact": "metro@partenaire-demo.ci"},
        )
        st_sols, _ = SousTraitantPartenaire.objects.get_or_create(
            nom="Partenaire Démo — Analyses de sols",
            defaults={"specialite": "Pédologie", "contact": "sols@partenaire-demo.ci"},
        )

        if DemandeDevis.objects.filter(client=client).exists():
            self.stdout.write("Devis de démonstration déjà présents : conservés.")
        else:
            # 1) Devis simple, a completer par le service reception
            creer_devis_et_proforma(
                client=client, type_analyse="EAUX_CONSOMMATION", categorie="Eau de forage",
                objet="Contrôle de la qualité de l'eau du forage de l'usine", description="Analyse complète avant mise en service",
                priorite="NORMALE", echantillons=[{"nom": "Eau de forage — point 1", "quantite": 2}, {"nom": "Eau de forage — point 2", "quantite": 1}],
                lieu_realisation="LABORATOIRE", observations_particulieres="Prélèvement effectué par le client",
            )
            # 2) Devis avec sous-traitance choisie par le client
            creer_devis_et_proforma(
                client=client, type_analyse="METROLOGIE", categorie="Balances et masses",
                objet="Étalonnage des balances de la ligne de production", description="Deux balances industrielles",
                priorite="HAUTE", echantillons=[{"nom": "Balance industrielle 300 kg", "quantite": 1}, {"nom": "Balance de précision 6 kg", "quantite": 1}],
                accord_sous_traitance=True, sous_traitants_ids=[st_metro.id, st_sols.id],
                sous_traitants_libres="Laboratoire X (déjà agréé par notre groupe)",
                retour_materiel_gere_labo=True, lieu_realisation="SITE_CLIENT",
                observations_particulieres="Intervention sur site souhaitée, hors week-end", declaration_conformite_souhaitee=True,
            )
            # 3) Devis deja envoye au client (en attente de « Lu et approuve »)
            _, p3 = creer_devis_et_proforma(
                client=client, type_analyse="CHIMIE_ALIMENTAIRE_INDUSTRIELLE", categorie="Analyses chimiques des aliments",
                objet="Valeurs nutritionnelles de jus de fruits", description="Lot de 3 références",
                priorite="NORMALE", echantillons=[{"nom": "Jus d'ananas 1 L", "quantite": 3}],
            )
            p3.statut = "ENVOYEE"
            p3.canal_envoi = "EMAIL"
            p3.envoye_le = timezone.now() - timedelta(hours=3)
            p3.save(update_fields=["statut", "canal_envoi", "envoye_le"])
            self.stdout.write(self.style.SUCCESS("3 devis de démonstration créés."))
            self._circuit_demo(client, reception, technicien)
            self._metrologie_demo(client, reception)
            self._impaye_demo(client)

        self.stdout.write(self.style.MIGRATE_HEADING("\nAccès de démonstration :"))
        self.stdout.write(f"  Responsable service réception : {RECEPTION_EMAIL} / {RECEPTION_PASSWORD}")
        self.stdout.write(f"  Service facturation / caisse : {COMPTABLE_EMAIL} / {COMPTABLE_PASSWORD}")
        self.stdout.write(f"  Client (pour la fiche + « Lu et approuvé ») : {CLIENT_EMAIL} / {CLIENT_PASSWORD}")

    # ── Circuit réception <-> laboratoire : 3 dossiers à des stades différents ──
    def _circuit_demo(self, client, reception, technicien):
        from django.core.files.base import ContentFile

        from facturation.views import _accepter_proforma, _signer_bon_commande
        from laboratoires.models import Laboratoire
        from qualite import circuit
        from qualite.models import Echantillon

        import io

        from PIL import Image

        buf = io.BytesIO()
        Image.new("RGB", (160, 60), "white").save(buf, "PNG")
        png = buf.getvalue()
        labos = {l.code: l for l in Laboratoire.objects.filter(code__in=["LMP", "LAI", "LEE", "LPI"])}
        today = timezone.now().date()

        modes = iter([("CHEQUE", "CHQ-4471"), ("BON_COMMANDE", "BC-2026-118"), ("COMPTANT", "RECU-CAISSE-09")] * 3)

        def dossier(objet, type_analyse, categorie, echs):
            _, proforma = creer_devis_et_proforma(
                client=client, type_analyse=type_analyse, categorie=categorie, objet=objet, description="Dossier de démonstration du circuit réception / laboratoire",
                priorite="NORMALE", echantillons=[{"nom": n, "quantite": 1} for n, _ in echs],
            )
            proforma.statut, proforma.lu_approuve, proforma.lu_approuve_le, proforma.lu_approuve_par = "ENVOYEE", True, timezone.now(), client
            proforma.save()
            bon = _accepter_proforma(proforma)
            _signer_bon_commande(bon, ContentFile(png, name="signature.png"))
            self._regler(proforma, *next(modes))
            from facturation.models import DemandeAnalyse
            da = DemandeAnalyse.objects.get(proforma=proforma)
            samples = [
                Echantillon.objects.create(designation=n, quantite=q, demande=da, date_reception=today, type_echantillon=type_analyse, description="")
                for n, q in echs
            ]
            da.statut, da.date_depot_echantillons = "ECHANTILLONS_RECUS", today
            da.save(update_fields=["statut", "date_depot_echantillons"])
            return da, samples

        def payload(da, samples, lab_codes, parametres):
            return {
                "demande": da.id, "nature_objet": "EAUX", "delai_realisation": "10 jours ouvrés", "observations": "Dossier de démonstration",
                "echantillons": [
                    {"id": e.id, "description": f"{e.designation} — flacon stérile", "quantite": e.quantite, "date_prelevement": today.isoformat(),
                     "etat": ["LIQUIDE"], "parametres": parametres, "laboratoires": [labos[c].id for c in lab_codes],
                     "lieu_prelevement": "Site du client (Yopougon)", "prelevement_par": "M. Koffi Yao", "numero_lot": "LOT-DEMO"}
                    for e in samples
                ],
            }

        # 1) Échantillons réceptionnés, fiche d'exécution à établir par la réception
        dossier("Contrôle de l'eau de la cantine", "EAUX_CONSOMMATION", "Eau potable du robinet",
                [("Eau cantine — robinet 1", "2 flacons"), ("Eau cantine — robinet 2", "2 flacons"), ("Eau cantine — réservoir", "1 flacon")])

        # 2) Fiche transmise au laboratoire, en attente de réception par le labo
        da, ech = dossier("Analyse microbiologique de lait", "MICROBIOLOGIE_PARASITOLOGIE", "Analyses microbiologiques des aliments",
                          [("Lait pasteurisé — lot A", "3 pots"), ("Lait pasteurisé — lot B", "3 pots")])
        fiche = circuit.creer_fiche(da, payload(da, ech, ["LMP"], "Flore aérobie mésophile, Salmonella, Coliformes"), reception)
        circuit.transmettre_au_laboratoire(fiche, reception)

        # 3) Résultats transmis par le laboratoire : la réception peut éditer le rapport d'essai
        da, ech = dossier("Qualité de l'eau de forage", "EAUX_CONSOMMATION", "Eau de forage",
                          [("Eau de forage — F1", "2 flacons"), ("Eau de forage — F2", "1 flacon")])
        fiche = circuit.creer_fiche(da, payload(da, ech, ["LMP", "LEE"], "Coliformes totaux, E. coli, pH"), reception)
        circuit.transmettre_au_laboratoire(fiche, reception)
        circuit.receptionner_labo(fiche, labos["LMP"].id, "CONFORME", "", technicien)
        circuit.receptionner_labo(fiche, labos["LEE"].id, "SOUS_RESERVE", "Flacon F2 : quantité limite", technicien)
        circuit.saisir_resultats(fiche, labos["LMP"].id, [
            {"echantillon": ech[0].id, "parametre": "Coliformes totaux", "methode": "NF EN ISO 9308-1", "unite": "UFC/100 mL", "resultat": "<1", "specification": "0 UFC/100 mL", "conforme": True, "accredite": True},
            {"echantillon": ech[0].id, "parametre": "Escherichia coli", "methode": "NF EN ISO 9308-1", "unite": "UFC/100 mL", "resultat": "8", "specification": "0 UFC/100 mL", "conforme": False, "accredite": True},
            {"echantillon": ech[1].id, "parametre": "Coliformes totaux", "methode": "NF EN ISO 9308-1", "unite": "UFC/100 mL", "resultat": "<1", "specification": "0 UFC/100 mL", "conforme": True, "accredite": True},
        ], technicien)
        circuit.saisir_resultats(fiche, labos["LEE"].id, [
            {"echantillon": ech[0].id, "parametre": "pH", "methode": "NF T 90-008", "unite": "-", "resultat": "7,2", "specification": "6,5 - 8,5", "conforme": True},
            {"echantillon": ech[1].id, "parametre": "pH", "methode": "NF T 90-008", "unite": "-", "resultat": "6,9", "specification": "6,5 - 8,5", "conforme": True},
        ], technicien)
        circuit.transmettre_resultats(fiche, labos["LMP"].id, technicien)
        circuit.transmettre_resultats(fiche, labos["LEE"].id, technicien)
        self.stdout.write(self.style.SUCCESS("3 dossiers du circuit réception / laboratoire créés."))

    # ── Circuit métrologie : réception -> DMCT -> certificat ───────────────────
    def _metrologie_demo(self, client, reception):
        from django.contrib.auth.models import User
        from django.core.files.base import ContentFile

        from facturation.views import _accepter_proforma, _signer_bon_commande
        from metrologie import circuit_metro
        from qualite.models import FicheEntreeEquipement

        import io

        from PIL import Image

        buf = io.BytesIO()
        Image.new("RGB", (160, 60), "white").save(buf, "PNG")
        png = buf.getvalue()
        dmct_user = User.objects.get(username="dmct.demo")
        today = timezone.now().date()

        modes = iter([("CHEQUE", "CHQ-5120"), ("BON_COMMANDE", "BC-2026-131"), ("COMPTANT", "RECU-CAISSE-12")] * 3)

        def dossier(objet, instruments, equipements, lieu="LABORATOIRE"):
            _, proforma = creer_devis_et_proforma(
                client=client, type_analyse="METROLOGIE", categorie="Balances et masses", objet=objet, description="Dossier de démonstration — circuit métrologie",
                priorite="NORMALE", echantillons=instruments, lieu_realisation=lieu,
            )
            proforma.statut, proforma.lu_approuve, proforma.lu_approuve_le, proforma.lu_approuve_par = "ENVOYEE", True, timezone.now(), client
            proforma.save()
            _signer_bon_commande(_accepter_proforma(proforma), ContentFile(png, name="signature.png"))
            self._regler(proforma, *next(modes))
            devis = proforma.demande_devis
            fes = [
                FicheEntreeEquipement.objects.create(domaine="METROLOGIE", demande_devis=devis, designation=d, marque=m, modele=mo, numero_serie=sn,
                                                     date_reception=today, etat_reception="bon état", recu_par=reception)
                for d, m, mo, sn in equipements
            ]
            return devis, fes

        def fiche(devis, fes, grandeur):
            eqs = [{"fiche_entree": fe.id, "nature": "Étalonnage", "grandeur": grandeur, "unite": "kg" if grandeur == "MASSE" else "°C"} for fe in fes]
            return circuit_metro.creer_ftm(devis, {"lieu_realisation": "LABORATOIRE", "operations_preliminaires": ["EXIGENCES_CLIENTS", "DOCUMENTS_NORMATIFS"],
                                                   "nombre_mesures_references": ["DOC_LANEMA"], "definition_points": "5 points répartis sur l'étendue",
                                                   "erreurs_max_references": ["DOC_LANEMA"], "jugement_references": ["DOCS_NORMATIFS"], "equipements": eqs}, reception)

        instr_masse = [{"nom": "Balance électronique", "quantite": 2, "details": {"famille": "MASSE", "type": "BALANCE", "prestation": "ETALONNAGE", "marque": "Mettler", "portee_max": "300 kg", "echelon": "0,01 kg"}}]
        # 1) Équipements réceptionnés, fiche de métrologie à établir par la réception
        dossier("Étalonnage des balances du magasin", instr_masse, [("Balance électronique 150 kg", "Ohaus", "Defender", "OH-100"), ("Balance électronique 150 kg", "Ohaus", "Defender", "OH-101")])
        # 2) Fiche transmise à la DMCT, à réceptionner
        devis, fes = dossier("Étalonnage de thermomètres de la chambre froide",
                             [{"nom": "Thermomètre", "quantite": 2, "details": {"famille": "TEMPERATURE", "type": "THERMOMETRE", "prestation": "ETALONNAGE", "plage_mesure": "-40 à 100 °C", "resolution": "0,1 °C"}}],
                             [("Thermomètre numérique", "Testo", "T-110", "TS-501"), ("Thermomètre numérique", "Testo", "T-110", "TS-502")])
        circuit_metro.transmettre_ftm(fiche(devis, fes, "TEMPERATURE"), reception)
        # 3) Travaux terminés : la DMCT prépare les certificats
        devis, fes = dossier("Vérification de la balance de production", instr_masse, [("Balance électronique 300 kg", "Mettler", "XS-300", "MT-900")])
        f = fiche(devis, fes, "MASSE")
        circuit_metro.transmettre_ftm(f, reception)
        circuit_metro.receptionner_dmct(f, dmct_user)
        circuit_metro.demarrer_travaux(f, {"lieu_realisation": "LABORATOIRE"}, dmct_user)
        circuit_metro.terminer_travaux(f, {"decisions": [{"id": e.id, "decision": "CONFORME"} for e in f.equipements.all()]}, dmct_user)
        self.stdout.write(self.style.SUCCESS("3 dossiers du circuit métrologie (réception -> DMCT -> certificat) créés."))
