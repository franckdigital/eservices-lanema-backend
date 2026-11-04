"""Alimente les 4 modules "services rattachés à la Direction Générale"
(Communication/Marketing, Juridique, Patrimoine, Qualité) avec des données de
démonstration réalistes, pour que les écrans KPI/CRUD ne soient plus vides.

Usage :
    python manage.py seed_dg_services            # ajoute des données
    python manage.py seed_dg_services --flush     # supprime d'abord tout ce
                                                    # qui a été créé par ce
                                                    # seed (pas les autres
                                                    # données de l'app)

Conçu pour être rejouable sans dupliquer à l'infini : chaque exécution sans
--flush ajoute un nouveau lot, --flush repart de zéro sur ces 4 modules.
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Service
from dg_communication.models import ActionCommunication, Partenariat, Prospect, SatisfactionClient
from dg_juridique.models import (
    AvisJuridique, Contentieux, Contrat, DossierJuridique, ProcedureDisciplinaire, TexteReglementaire,
)
from dg_patrimoine.models import Bien, InventairePatrimoine, MaintenanceBien, MouvementBien
from dg_qualite.models import (
    ActionQualite, AuditQualite, IndicateurQualite, NonConformiteQualite, ReclamationClient, RevueDirection,
)

User = get_user_model()


def jours_avant(n):
    return timezone.now().date() - timedelta(days=n)


class Command(BaseCommand):
    help = "Alimente les modules DG (Communication, Juridique, Patrimoine, Qualité) avec des données de démo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush", action="store_true",
            help="Supprime d'abord toutes les données existantes de ces 4 modules avant de re-semer.",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write("Suppression des données existantes des modules DG…")
            for model in [
                Prospect, Partenariat, SatisfactionClient, ActionCommunication,
                AvisJuridique, Contentieux, Contrat, TexteReglementaire, ProcedureDisciplinaire, DossierJuridique,
                MouvementBien, MaintenanceBien, InventairePatrimoine, Bien,
                ActionQualite, AuditQualite, ReclamationClient, RevueDirection, IndicateurQualite, NonConformiteQualite,
            ]:
                count, _ = model.objects.all().delete()
                self.stdout.write(f"  - {model.__name__} : {count} supprimé(s)")

        responsable = User.objects.filter(is_active=True).order_by("id").first()
        if responsable is None:
            self.stdout.write(self.style.WARNING(
                "Aucun utilisateur actif trouvé — les champs 'responsable' resteront vides."
            ))
        services = list(Service.objects.all()[:10])

        self.seed_communication(responsable)
        self.seed_juridique(responsable)
        self.seed_patrimoine(responsable)
        self.seed_qualite(responsable, services)

        self.stdout.write(self.style.SUCCESS("Seed DG terminé."))

    # ------------------------------------------------------------------
    def seed_communication(self, responsable):
        self.stdout.write("Communication & Marketing…")

        actions_data = [
            ("CAMPAGNE", "Campagne de notoriété LANEMA 2026", "REALISEE", 2_500_000, 4_200_000, 60, 30),
            ("CAMPAGNE", "Campagne digitale réseaux sociaux", "EN_COURS", 800_000, 1_100_000, 20, None),
            ("COMMUNIQUE", "Communiqué — nouveaux services e-Diligence", "REALISEE", 0, None, 45, 44),
            ("COMMUNIQUE", "Communiqué — résultats semestriels", "REALISEE", 0, None, 15, 14),
            ("EVENEMENT", "Journée portes ouvertes LANEMA", "REALISEE", 1_200_000, 600_000, 50, 48),
            ("EVENEMENT", "Séminaire partenaires institutionnels", "PLANIFIEE", 1_800_000, None, -20, None),
            ("SALON", "Salon international de l'administration publique", "REALISEE", 3_000_000, 2_300_000, 90, 85),
            ("SALON", "Foire économique d'Abidjan", "EN_COURS", 1_500_000, None, 10, None),
            ("SUPPORT", "Refonte brochure institutionnelle", "REALISEE", 400_000, None, 70, 65),
            ("SUPPORT", "Vidéo de présentation LANEMA", "PLANIFIEE", 900_000, None, -10, None),
        ]
        actions = []
        for type_, titre, statut, budget, ca, debut_j, fin_j in actions_data:
            a = ActionCommunication.objects.create(
                type=type_, titre=titre, statut=statut,
                budget=Decimal(budget), chiffre_affaires_genere=Decimal(ca) if ca else None,
                date_debut=jours_avant(debut_j) if debut_j else None,
                date_fin=jours_avant(fin_j) if fin_j else None,
                responsable=responsable,
                description=f"Action de type {type_.lower()} — données de démonstration.",
            )
            actions.append(a)

        prospects_data = [
            ("Ministère XYZ", "ENTREPRISE_A", "CONVERTI", 3_500_000, 40),
            ("SARL Koffi & Fils", "ENTREPRISE_B", "CONVERTI", 1_200_000, 30),
            ("Cabinet Juridique Touré", "ENTREPRISE_C", "DEVIS_ENVOYE", 800_000, 10),
            ("ONG Avenir Jeunesse", "ENTREPRISE_D", "QUALIFIE", None, 5),
            ("Groupe Industriel CI", "ENTREPRISE_E", "PERDU", 2_000_000, 25),
            ("Agence Immobilière Plateau", "ENTREPRISE_F", "NOUVEAU", None, 2),
        ]
        for nom, org, statut, montant, j in prospects_data:
            Prospect.objects.create(
                nom=nom, organisation=org, contact_email=f"{org.lower()}@example.com",
                source=random.choice(["Salon", "Site web", "Recommandation", "Campagne digitale"]),
                action_origine=random.choice(actions) if actions else None,
                statut=statut, montant_devis=Decimal(montant) if montant else None,
                date_conversion=jours_avant(j - 3) if statut == "CONVERTI" else None,
            )

        partenariats_data = [
            ("Chambre de Commerce CI", "ACTIF"), ("Ministère du Commerce", "ACTIF"),
            ("Université FHB", "EN_NEGOCIATION"), ("ONG Transparency CI", "TERMINE"),
        ]
        for nom, statut in partenariats_data:
            Partenariat.objects.create(
                nom_partenaire=nom, statut=statut, responsable=responsable,
                date_signature=jours_avant(random.randint(30, 300)) if statut != "EN_NEGOCIATION" else None,
                description="Partenariat institutionnel — données de démonstration.",
            )

        services_demo = ["Essais de laboratoire", "Métrologie", "Certification", "Formation", "Audit qualité"]
        for i in range(12):
            SatisfactionClient.objects.create(
                client_nom=f"Client démo {i + 1}",
                organisation=random.choice(["SARL Koffi & Fils", "Ministère XYZ", "Groupe Industriel CI", ""]),
                contact_email=f"client.demo{i + 1}@example.com",
                contact_telephone=f"07{random.randint(10000000, 99999999)}",
                action_liee=random.choice(actions) if actions and random.random() > 0.3 else None,
                service_concerne=random.choice(services_demo),
                canal_recueil=random.choice(["TELEPHONE", "EMAIL", "ENTRETIEN", "FORMULAIRE"]),
                recueilli_par=responsable,
                note=random.choice([3, 4, 4, 5, 5, 5, 2]),
                recommanderait=random.choice([True, True, False, None]),
                fidele=random.random() > 0.4,
                commentaire="Retour client — données de démonstration.",
            )

    # ------------------------------------------------------------------
    def seed_juridique(self, responsable):
        self.stdout.write("Juridique…")

        dossiers = []
        types_dossiers = ["CONTRAT", "CONTENTIEUX", "CONSULTATION", "AVIS", "DISCIPLINAIRE"]
        titres = [
            "Révision du contrat de prestation IT", "Litige foncier Zone Industrielle",
            "Consultation sur la réforme du droit du travail", "Avis sur conformité RGPD",
            "Procédure disciplinaire agent — absences répétées", "Contrat de maintenance véhicules",
            "Contentieux fournisseur matériel bureautique", "Consultation marchés publics",
        ]
        for i, titre in enumerate(titres):
            statut = random.choice(["OUVERT", "EN_COURS", "CLOTURE", "CLOTURE"])
            d = DossierJuridique.objects.create(
                type_dossier=types_dossiers[i % len(types_dossiers)],
                titre=titre, statut=statut, responsable=responsable,
                description="Dossier juridique — données de démonstration.",
            )
            if statut == "CLOTURE":
                DossierJuridique.objects.filter(pk=d.pk).update(date_cloture=jours_avant(random.randint(1, 60)))
            DossierJuridique.objects.filter(pk=d.pk).update(date_ouverture=jours_avant(random.randint(10, 180)))
            dossiers.append(d)

        for i in range(6):
            statut = random.choice(["BROUILLON", "VALIDE", "SIGNE", "RENOUVELE", "EXPIRE"])
            c = Contrat.objects.create(
                dossier=random.choice(dossiers), intitule=f"Contrat #{i + 1} — démonstration",
                partie_prenante=random.choice(["Fournisseur A", "Prestataire B", "Partenaire C"]),
                statut=statut,
                date_expiration=jours_avant(-random.randint(5, 90)) if statut in ("VALIDE", "SIGNE") else None,
            )
            Contrat.objects.filter(pk=c.pk).update(date_redaction=jours_avant(random.randint(30, 200)))

        for i in range(4):
            statut = random.choice(["EN_COURS", "CLOTURE", "EVITE"])
            ct = Contentieux.objects.create(
                dossier=random.choice(dossiers), partie_adverse=f"Partie adverse {i + 1}",
                objet="Contentieux — données de démonstration.", statut=statut,
                issue="Favorable" if statut == "CLOTURE" else "",
            )
            if statut != "EN_COURS":
                Contentieux.objects.filter(pk=ct.pk).update(date_cloture=jours_avant(random.randint(1, 45)))
            Contentieux.objects.filter(pk=ct.pk).update(date_ouverture=jours_avant(random.randint(10, 120)))

        for i in range(5):
            a = AvisJuridique.objects.create(
                dossier=random.choice(dossiers), demandeur=responsable,
                sujet=f"Demande d'avis #{i + 1} — démonstration",
                reponse="Avis favorable sous réserve de modifications mineures." if i % 2 == 0 else "",
            )
            if i % 2 == 0:
                AvisJuridique.objects.filter(pk=a.pk).update(date_reponse=jours_avant(random.randint(1, 20)))
            AvisJuridique.objects.filter(pk=a.pk).update(date_demande=jours_avant(random.randint(5, 40)))

        pd = ProcedureDisciplinaire.objects.create(
            agent_concerne=responsable, motif="Absences répétées non justifiées — démonstration.",
            statut="CLOTUREE",
        )
        ProcedureDisciplinaire.objects.filter(pk=pd.pk).update(
            date_ouverture=jours_avant(60), date_cloture=jours_avant(20)
        )

        for i in range(3):
            t = TexteReglementaire.objects.create(
                reference=f"DEC-2026-{i + 1:03d}", intitule=f"Décret relatif au domaine {i + 1} — démonstration",
                statut=random.choice(["APPLICABLE", "A_SURVEILLER"]), analyse_par=responsable,
                synthese="Synthèse de démonstration.",
            )
            TexteReglementaire.objects.filter(pk=t.pk).update(date_analyse=jours_avant(random.randint(5, 90)))

    # ------------------------------------------------------------------
    def seed_patrimoine(self, responsable):
        self.stdout.write("Patrimoine…")

        biens_data = [
            ("VEH-001", "Véhicule de service Toyota Hilux", "VEHICULE", 18_000_000, 12_000_000, 7, "EN_SERVICE"),
            ("VEH-002", "Véhicule de service Toyota Corolla", "VEHICULE", 12_000_000, 9_000_000, 7, "EN_SERVICE"),
            ("INFO-001", "Serveur principal datacenter", "INFORMATIQUE", 5_500_000, 3_200_000, 5, "EN_SERVICE"),
            ("INFO-002", "Parc ordinateurs Direction (x15)", "INFORMATIQUE", 9_000_000, 4_500_000, 4, "EN_SERVICE"),
            ("MOB-001", "Mobilier de bureau Direction Générale", "MOBILIER", 3_200_000, 2_000_000, 10, "EN_SERVICE"),
            ("EQ-001", "Groupe électrogène 100 kVA", "EQUIPEMENT", 7_000_000, 5_000_000, 8, "EN_MAINTENANCE"),
            ("IMMO-001", "Bâtiment annexe Cocody", "IMMOBILIER", 85_000_000, 80_000_000, 30, "EN_SERVICE"),
            ("VEH-003", "Véhicule de liaison (réformé)", "VEHICULE", 9_000_000, 500_000, 7, "REFORME"),
            ("INFO-003", "Imprimante multifonction (perdue)", "INFORMATIQUE", 450_000, 0, 3, "PERDU"),
            ("MOB-002", "Chaises de réunion (sorties)", "MOBILIER", 600_000, 100_000, 10, "SORTI"),
        ]
        biens = []
        for code, designation, cat, acq, actuelle, duree, statut in biens_data:
            b = Bien.objects.create(
                code=code, designation=designation, categorie=cat,
                date_acquisition=jours_avant(random.randint(200, 1800)),
                valeur_acquisition=Decimal(acq), valeur_actuelle=Decimal(actuelle),
                duree_amortissement_ans=duree, statut=statut,
                localisation="Siège LANEMA, Abidjan", responsable=responsable,
            )
            biens.append(b)

        emplacements = ["Siège LANEMA, Abidjan", "Annexe Cocody", "Entrepôt Yopougon", "Direction Générale"]
        mouv_types = {"EN_SERVICE": "ENTREE", "EN_MAINTENANCE": "TRANSFERT", "REFORME": "REFORME", "PERDU": "PERTE", "SORTI": "SORTIE"}
        for b in biens:
            MouvementBien.objects.create(
                bien=b, type_mouvement=mouv_types.get(b.statut, "ENTREE"),
                quantite=1, emplacement=random.choice(emplacements),
                motif=f"Mouvement initial — {b.get_statut_display()}", effectue_par=responsable,
            )
        # quelques mouvements supplémentaires pour varier les stats
        for _ in range(5):
            b = random.choice(biens)
            MouvementBien.objects.create(
                bien=b, type_mouvement=random.choice(["TRANSFERT", "ENTREE"]),
                quantite=random.choice([1, 1, 2, 5]), emplacement=random.choice(emplacements),
                motif="Mouvement complémentaire — démonstration.", effectue_par=responsable,
            )

        for b in [biens[5], biens[0], biens[2]]:  # groupe électrogène, véhicule, serveur
            MaintenanceBien.objects.create(
                bien=b, type_maintenance=random.choice(["PREVENTIVE", "CORRECTIVE"]),
                quantite=1, emplacement=random.choice(emplacements),
                date_maintenance=jours_avant(random.randint(5, 120)),
                date_fin=jours_avant(random.randint(1, 4)),
                cout=Decimal(random.choice([50_000, 120_000, 300_000, 450_000])),
                description="Opération de maintenance — démonstration.",
            )

        for i, j in enumerate([30, 120, 300]):
            InventairePatrimoine.objects.create(
                date_inventaire=jours_avant(j), responsable=responsable,
                emplacement=emplacements[i % len(emplacements)],
                nombre_biens_verifies=len(biens) - i, ecarts_constates=i,
                observations="Inventaire — données de démonstration.",
            )

    # ------------------------------------------------------------------
    def seed_qualite(self, responsable, services):
        self.stdout.write("Qualité…")

        nc_list = []
        descriptions = [
            "Non-respect du délai de traitement des diligences",
            "Document non archivé selon la procédure",
            "Écart constaté lors de l'inventaire du patrimoine",
            "Réclamation client non traitée dans les délais",
            "Procédure de validation des contrats non suivie",
        ]
        for i, desc in enumerate(descriptions):
            statut = random.choice(["OUVERTE", "EN_TRAITEMENT", "CLOTUREE", "CLOTUREE"])
            nc = NonConformiteQualite.objects.create(
                description=desc, gravite=random.choice(["MINEURE", "MAJEURE", "CRITIQUE"]),
                service_concerne=random.choice(services) if services else None,
                statut=statut,
            )
            if statut == "CLOTUREE":
                NonConformiteQualite.objects.filter(pk=nc.pk).update(date_cloture=jours_avant(random.randint(1, 30)))
            NonConformiteQualite.objects.filter(pk=nc.pk).update(date_detection=jours_avant(random.randint(10, 90)))
            nc_list.append(nc)

        for nc in nc_list:
            statut = random.choice(["PLANIFIEE", "EN_COURS", "CLOTUREE", "CLOTUREE"])
            aq = ActionQualite.objects.create(
                non_conformite=nc, type=random.choice(["CORRECTIVE", "PREVENTIVE"]),
                description=f"Action liée à : {nc.description[:40]}", responsable=responsable,
                statut=statut,
            )
            if statut == "CLOTUREE":
                ActionQualite.objects.filter(pk=aq.pk).update(date_cloture=jours_avant(random.randint(1, 20)))
            ActionQualite.objects.filter(pk=aq.pk).update(date_planification=jours_avant(random.randint(5, 60)))

        audits_data = [
            ("INTERNE", "", "CONFORME"), ("INTERNE", "", "NON_CONFORME"),
            ("EXTERNE", "Cabinet Audit CI", "CONFORME"), ("ISO", "Bureau Veritas", "CONFORME"),
            ("ISO", "Bureau Veritas", "NON_CONFORME"),
        ]
        for i, (type_, organisme, resultat) in enumerate(audits_data):
            AuditQualite.objects.create(
                reference=f"AUD-DEMO-{i + 1:03d}",
                type_audit=type_, organisme=organisme, date_audit=jours_avant(random.randint(10, 300)),
                resultat=resultat, observations="Audit — données de démonstration.",
            )

        for i in range(8):
            statut = random.choice(["OUVERTE", "TRAITEE", "TRAITEE"])
            r = ReclamationClient.objects.create(
                client_nom=f"Client réclamant {i + 1}",
                description="Réclamation — données de démonstration.", statut=statut,
                note_satisfaction=random.choice([3, 4, 5]) if statut == "TRAITEE" else None,
            )
            if statut == "TRAITEE":
                ReclamationClient.objects.filter(pk=r.pk).update(date_traitement=jours_avant(random.randint(1, 15)))
            ReclamationClient.objects.filter(pk=r.pk).update(date_reception=jours_avant(random.randint(5, 40)))

        for j in [15, 90, 180]:
            RevueDirection.objects.create(
                date_revue=jours_avant(j), participants="Direction Générale, Chefs de service",
                decisions="Décisions de la revue — données de démonstration.",
            )

        indicateurs_data = [
            ("Taux de satisfaction client", 90, 87), ("Taux de conformité ISO", 95, 92),
            ("Délai moyen de traitement des réclamations", 5, 4), ("Taux de clôture des actions correctives", 85, 78),
        ]
        for nom, cible, actuel in indicateurs_data:
            IndicateurQualite.objects.create(
                nom=nom, cible=Decimal(cible), valeur_actuelle=Decimal(actuel), periode="2026-T4",
            )
