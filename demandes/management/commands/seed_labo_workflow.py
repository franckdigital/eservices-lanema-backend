"""
Seed du personnel DEA (staff labo) et de 5 clients repartis sur les
differentes etapes du workflow reel devis -> proforma -> bon de commande ->
paiement -> echantillon -> analyse -> resultats, pour tester chaque ecran du
portail /app (client-labo) avec des donnees realistes et coherentes avec les
transitions imposees par facturation/views.py et demandes/views.py.

Usage : python manage.py seed_labo_workflow
"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from clients.models import ClientProfile
from demandes.models import DemandeDevis
from facturation.models import BonCommande, DemandeAnalyse, Facture, Proforma
from laboratoires.models import Laboratoire
from qualite.models import Echantillon, Essai

TVA_RATE = Decimal("0.1925")
STAFF_PASSWORD = "Lanema2026!"
CLIENT_PASSWORD = "Client2026!"


def _montant(base_ht: Decimal) -> tuple[Decimal, Decimal]:
    ttc = (base_ht * (1 + TVA_RATE)).quantize(Decimal("1"))
    return base_ht, ttc


class Command(BaseCommand):
    help = "Seed le personnel DEA et 5 clients a differentes etapes du workflow devis -> analyse"

    def handle(self, *args, **options):
        today = timezone.now().date()

        self.stdout.write(self.style.MIGRATE_HEADING("=== Personnel DEA (staff labo) ==="))
        responsable = self._make_staff(
            username="responsable.labo", email="responsable.labo@lanema-ci.com",
            first_name="Aya", last_name="Koffi", role="ADMIN",
        )
        self._make_staff(
            username="gestionnaire.labo", email="gestionnaire.labo@lanema-ci.com",
            first_name="Bakary", last_name="Traore", role="GESTIONNAIRE",
        )
        self._make_staff(
            username="comptable.labo", email="comptable.labo@lanema-ci.com",
            first_name="Chantal", last_name="Nguessan", role="COMPTABLE",
        )
        technicien = self._make_staff(
            username="technicien.labo", email="technicien.labo@lanema-ci.com",
            first_name="David", last_name="Ouattara", role="TECHNICIEN",
        )

        labo, _ = Laboratoire.objects.get_or_create(
            code="DEAL",
            defaults={
                "nom": "Direction des Essais et Analyses de Laboratoire",
                "responsable": responsable,
                "capacite_journaliere": 20,
            },
        )

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Clients ==="))
        c1 = self._make_client("client1.entreprise", "contact@agrosarl.ci", "AGRO SARL", "Jean", "Kouassi")
        c2 = self._make_client("client2.entreprise", "qualite@ivoireeau.ci", "Ivoire Eau Distribution", "Fatou", "Diabate")
        c3 = self._make_client("client3.entreprise", "labo@nutrifoods.ci", "NutriFoods CI", "Marc", "Yao")
        c4 = self._make_client("client4.entreprise", "achats@batico.ci", "BATICO Industries", "Aicha", "Sanogo")
        c5 = self._make_client("client5.entreprise", "contact@pharmaplus.ci", "PharmaPlus CI", "Yves", "Brou")

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Scenarios ==="))
        self._scenario_complet(
            c1, responsable, technicien, labo, today, index=1,
            type_analyse="EAUX_CONSOMMATION", categorie="Eau potable du robinet",
            objet="Controle qualite eau potable - reseau de distribution",
            montant_base=Decimal("45000"),
        )
        self._scenario_complet(
            c2, responsable, technicien, labo, today, index=2,
            type_analyse="MICROBIOLOGIE_PARASITOLOGIE", categorie="Analyses microbiologiques des aliments",
            objet="Controle microbiologique de routine - unite de production",
            montant_base=Decimal("70000"),
        )
        self._scenario_analyse_en_cours(
            c3, responsable, technicien, labo, today, index=3,
            type_analyse="CHIMIE_ALIMENTAIRE_INDUSTRIELLE", categorie="Analyses chimiques des aliments",
            objet="Analyse chimique d'un nouveau produit avant commercialisation",
            montant_base=Decimal("65000"),
        )
        self._scenario_attente_paiement(
            c4, responsable, today, index=4,
            type_analyse="SOLS_ENGRAIS", categorie="Analyse de sol agricole",
            objet="Analyse de sol avant lancement d'un chantier",
            montant_base=Decimal("55000"),
        )
        self._scenario_premiere_phase(
            c5, today, index=5,
            type_analyse="METROLOGIE", categorie="Etalonnage de masse",
            objet="Etalonnage annuel des instruments de pesage",
            montant_base=Decimal("80000"),
        )

        self._print_recap()

    # ─── Comptes ────────────────────────────────────────────────────────────

    def _make_staff(self, username, email, first_name, last_name, role):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": username, "first_name": first_name, "last_name": last_name,
                "is_staff": True, "is_superuser": role == "ADMIN",
            },
        )
        if not created:
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.is_staff = True
            user.is_superuser = role == "ADMIN"
        user.set_password(STAFF_PASSWORD)
        user.save()
        ClientProfile.objects.update_or_create(
            user=user, defaults={"role": role, "organisation": "LANEMA - DEA"},
        )
        label = "Cree" if created else "Mis a jour"
        self.stdout.write(f"  [{label}] {email} ({role})")
        return user

    def _make_client(self, username, email, raison_sociale, first_name, last_name):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"username": username, "first_name": first_name, "last_name": last_name},
        )
        if not created:
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
        user.set_password(CLIENT_PASSWORD)
        user.save()
        ClientProfile.objects.update_or_create(
            user=user,
            defaults={
                "role": "CLIENT",
                "organisation": raison_sociale,
                "raison_sociale": raison_sociale,
                "adresse": "Abidjan, Cote d'Ivoire",
                "telephone": "+225 07 00 00 00",
                "contact_nom": f"{first_name} {last_name}",
                "type_subscription": "STANDARD",
            },
        )
        label = "Cree" if created else "Mis a jour"
        self.stdout.write(f"  [{label}] {email} ({raison_sociale})")
        return user

    # ─── Scenarios ──────────────────────────────────────────────────────────

    def _make_devis_et_proforma(self, client, today, type_analyse, categorie, objet, montant_base, devis_statut, proforma_statut):
        montant_ht, montant_ttc = _montant(montant_base)
        demande = DemandeDevis.objects.create(
            numero=f"DEV-{DemandeDevis.objects.count() + 1:05d}",
            client=client, type_analyse=type_analyse, categorie=categorie,
            objet=objet, description=f"{objet}.", statut=devis_statut,
        )
        proforma = Proforma.objects.create(
            numero=f"PROF-{Proforma.objects.count() + 1:05d}",
            client=client, demande_devis=demande,
            montant_ht=montant_ht, montant_ttc=montant_ttc, devise="FCFA",
            statut=proforma_statut,
        )
        return demande, proforma, montant_ht, montant_ttc

    def _scenario_premiere_phase(self, client, today, index, type_analyse, categorie, objet, montant_base):
        self.stdout.write(f"\n-- Client {index} ({client.email}) : premiere phase, demande de devis seule --")
        self._make_devis_et_proforma(
            client, today, type_analyse, categorie, objet, montant_base,
            devis_statut="EN_ATTENTE", proforma_statut="BROUILLON",
        )

    def _scenario_attente_paiement(self, client, responsable, today, index, type_analyse, categorie, objet, montant_base):
        self.stdout.write(f"\n-- Client {index} ({client.email}) : bon de commande signe, paiement en attente de validation --")
        demande, proforma, montant_ht, montant_ttc = self._make_devis_et_proforma(
            client, today, type_analyse, categorie, objet, montant_base,
            devis_statut="ACCEPTEE", proforma_statut="ACCEPTEE",
        )
        proforma.valide_par_responsable = responsable
        proforma.date_validation_responsable = today
        proforma.signature_responsable_appliquee = True
        proforma.save(update_fields=["valide_par_responsable", "date_validation_responsable", "signature_responsable_appliquee"])

        bon_commande = BonCommande.objects.create(
            numero=f"BC-{BonCommande.objects.count() + 1:05d}",
            client=client, proforma=proforma,
            montant_ht=montant_ht, montant_ttc=montant_ttc, devise="FCFA",
            statut="SIGNE_CLIENT", date_signature_client=today,
            valide_par_responsable=responsable, date_validation_responsable=today,
            signature_responsable_appliquee=True,
        )
        Facture.objects.create(
            numero=f"FAC-{Facture.objects.count() + 1:05d}",
            client=client, proforma=proforma, bon_commande=bon_commande,
            montant_ht=montant_ht, montant_ttc=montant_ttc, devise="FCFA",
            statut="EN_ATTENTE_VALIDATION",
            date_echeance=today + timedelta(days=30),
            mode_paiement="CHEQUE", paiement_valide=False, visible_client=True,
        )

    def _scenario_analyse_en_cours(self, client, responsable, technicien, labo, today, index, type_analyse, categorie, objet, montant_base):
        self.stdout.write(f"\n-- Client {index} ({client.email}) : paye, echantillon receptionne, analyse en cours --")
        facture, analyse, montant_ht, montant_ttc = self._payer_jusqu_a_analyse(
            client, responsable, today, type_analyse, categorie, objet, montant_base,
        )
        analyse.statut = "EN_COURS"
        analyse.date_depot_echantillons = today - timedelta(days=2)
        analyse.date_debut_analyse = today - timedelta(days=1)
        analyse.save(update_fields=["statut", "date_depot_echantillons", "date_debut_analyse"])

        echantillon = Echantillon.objects.create(
            designation=f"{categorie} - echantillon principal",
            type_echantillon=categorie, demande=analyse, quantite="1 unite",
            statut="EN_ANALYSE", conforme=None,
            date_reception=today - timedelta(days=2),
            emplacement_stockage="Chambre froide A1",
        )
        Essai.objects.create(
            type_essai=objet, echantillon=echantillon, laboratoire=labo,
            statut="EN_COURS", technicien=technicien.get_full_name(), technicien_user=technicien,
            date_debut=today - timedelta(days=1),
        )

    def _scenario_complet(self, client, responsable, technicien, labo, today, index, type_analyse, categorie, objet, montant_base):
        self.stdout.write(f"\n-- Client {index} ({client.email}) : parcours complet, paye, resultats envoyes --")
        facture, analyse, montant_ht, montant_ttc = self._payer_jusqu_a_analyse(
            client, responsable, today, type_analyse, categorie, objet, montant_base,
        )
        analyse.statut = "RESULTATS_ENVOYES"
        analyse.date_depot_echantillons = today - timedelta(days=6)
        analyse.date_debut_analyse = today - timedelta(days=5)
        analyse.date_fin_analyse = today - timedelta(days=1)
        analyse.observations = "Resultats conformes aux normes en vigueur."
        analyse.save(update_fields=[
            "statut", "date_depot_echantillons", "date_debut_analyse", "date_fin_analyse", "observations",
        ])

        echantillon = Echantillon.objects.create(
            designation=f"{categorie} - echantillon principal",
            type_echantillon=categorie, demande=analyse, quantite="1 unite",
            statut="TERMINE", conforme=True,
            date_reception=today - timedelta(days=6),
            emplacement_stockage="Chambre froide A2",
        )
        Essai.objects.create(
            type_essai=objet, echantillon=echantillon, laboratoire=labo,
            statut="VALIDE", technicien=technicien.get_full_name(), technicien_user=technicien,
            date_debut=today - timedelta(days=5), date_fin=today - timedelta(days=1),
            norme="NI 09-01 / OMS",
        )

    def _payer_jusqu_a_analyse(self, client, responsable, today, type_analyse, categorie, objet, montant_base):
        """Deroule le pipeline commun jusqu'a la facture payee + creation de la
        DemandeAnalyse (EN_ATTENTE_ECHANTILLONS), exactement comme le fait
        FactureViewSet.valider_paiement en production."""
        demande, proforma, montant_ht, montant_ttc = self._make_devis_et_proforma(
            client, today, type_analyse, categorie, objet, montant_base,
            devis_statut="ACCEPTEE", proforma_statut="ACCEPTEE",
        )
        proforma.valide_par_responsable = responsable
        proforma.date_validation_responsable = today
        proforma.signature_responsable_appliquee = True
        proforma.save(update_fields=["valide_par_responsable", "date_validation_responsable", "signature_responsable_appliquee"])

        bon_commande = BonCommande.objects.create(
            numero=f"BC-{BonCommande.objects.count() + 1:05d}",
            client=client, proforma=proforma,
            montant_ht=montant_ht, montant_ttc=montant_ttc, devise="FCFA",
            statut="SIGNE_CLIENT", date_signature_client=today,
            valide_par_responsable=responsable, date_validation_responsable=today,
            signature_responsable_appliquee=True,
        )
        facture = Facture.objects.create(
            numero=f"FAC-{Facture.objects.count() + 1:05d}",
            client=client, proforma=proforma, bon_commande=bon_commande,
            montant_ht=montant_ht, montant_ttc=montant_ttc, devise="FCFA",
            statut="PAYEE", date_echeance=today + timedelta(days=30),
            mode_paiement="COMPTANT", paiement_valide=True, visible_client=True,
            date_paiement=today - timedelta(days=7),
            valide_par_responsable=responsable, date_validation_responsable=today,
            signature_responsable_appliquee=True,
        )
        analyse = DemandeAnalyse.objects.create(
            numero=f"DA-{DemandeAnalyse.objects.count() + 1:05d}",
            client=client, demande_devis=demande, proforma=proforma, facture=facture,
            laboratoire=None, statut="EN_ATTENTE_ECHANTILLONS",
            montant_ht=montant_ht, montant_ttc=montant_ttc,
        )
        return facture, analyse, montant_ht, montant_ttc

    # ─── Recap ──────────────────────────────────────────────────────────────

    def _print_recap(self):
        self.stdout.write(self.style.SUCCESS("\n=== Seed termine ==="))
        self.stdout.write(self.style.MIGRATE_HEADING("Personnel DEA (portail staff /app) :"))
        self.stdout.write(f"  ADMIN        responsable.labo@lanema-ci.com  / {STAFF_PASSWORD}")
        self.stdout.write(f"  GESTIONNAIRE gestionnaire.labo@lanema-ci.com / {STAFF_PASSWORD}")
        self.stdout.write(f"  COMPTABLE    comptable.labo@lanema-ci.com    / {STAFF_PASSWORD}")
        self.stdout.write(f"  TECHNICIEN   technicien.labo@lanema-ci.com   / {STAFF_PASSWORD}")
        self.stdout.write(self.style.MIGRATE_HEADING("\nClients (portail client) :"))
        self.stdout.write(f"  1. contact@agrosarl.ci     - AGRO SARL              - complet, paye, resultats envoyes")
        self.stdout.write(f"  2. qualite@ivoireeau.ci    - Ivoire Eau Distribution - complet, paye, resultats envoyes")
        self.stdout.write(f"  3. labo@nutrifoods.ci      - NutriFoods CI          - paye, analyse en cours")
        self.stdout.write(f"  4. achats@batico.ci        - BATICO Industries      - bon de commande signe, paiement en attente")
        self.stdout.write(f"  5. contact@pharmaplus.ci   - PharmaPlus CI          - demande de devis seule (premiere phase)")
        self.stdout.write(f"     mot de passe commun : {CLIENT_PASSWORD}")
