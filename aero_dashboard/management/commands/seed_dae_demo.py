"""Seed de demonstration pour la Direction de l'Aeronautique (DAE) —
alimente l'integralite des modules aero_* (clients, aeronefs, demandes,
maintenance, roues, batteries, equipements, stock, qualite, securite,
atelier, finance, satisfaction, reclamations) afin que le portail staff
(/dae/*, /kpi-aero/*) et le portail client (/dae-client/*) aient des
donnees realistes a afficher.

Idempotent sur les entites "catalogue" (clients, aeronefs, pieces,
equipements atelier, utilisateurs demo) via get_or_create — les rejouer
ne duplique rien. Les entites "journal" (demandes, ordres de travail,
interventions, tests, non-conformites, factures...) sont recreees a
chaque execution : relancer la commande ajoute davantage de donnees de
demo plutot que d'etre strictement idempotent sur ces objets.

Usage : python manage.py seed_dae_demo
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from aero_atelier.models import (
    CertificationTechnicien,
    EquipementAtelier,
    EtalonnageAtelier,
    MaintenancePreventiveAtelier,
    PanneEquipementAtelier,
)
from aero_clients.models import Aeronef, ClientAeronautique, DemandeDAE, ReclamationClientDAE, SatisfactionDAE
from aero_finance.models import BonCommandeDAE, DevisDAE, FactureDAE
from aero_maintenance.models import (
    BatterieAeronef,
    CertificatDAE,
    EquipementAeronautique,
    InspectionRoue,
    InterventionTechnique,
    OrdreTravail,
    RoueAeronef,
    TestBatterie,
)
from aero_qualite.models import ActionCorrectiveDAE, AuditQualiteDAE, NonConformiteDAE
from aero_securite.models import ControleReglementaire, EcartReglementaire, FormationSecurite, IncidentTechnique, RapportSecurite
from aero_stock.models import MouvementPieceRechange, PieceRechange
from core.models import Direction, UserProfile

NOW = timezone.now()
TODAY = NOW.date()


def jours_avant(n):
    return TODAY - timedelta(days=n)


def dt_jours_avant(n):
    return NOW - timedelta(days=n)


CLIENTS_DATA = [
    dict(nom="Ivoire Airways", type_client="COMPAGNIE_AERIENNE", adresse="Aéroport FHB, Zone Fret, Abidjan",
         telephone="+225 27 21 75 00 00", email="maintenance@ivoire-airways.example", numero_identification="CI-RCCM-2011-B-4521",
         contact="Koffi ADJOUMANI"),
    dict(nom="Garde Nationale — Escadrille Aviation", type_client="FORCES_ARMEES", adresse="Base aérienne 701, Yamoussoukro",
         telephone="+225 27 30 64 12 00", email="logistique.aviation@garde-nationale.example", numero_identification="GN-AV-701",
         contact="Cdt. Bakary TRAORE"),
    dict(nom="Aéroclub d'Abidjan", type_client="AEROCLUB", adresse="Aérodrome de Bouaké, Abidjan",
         telephone="+225 05 04 12 34 56", email="secretariat@aeroclub-abidjan.example", numero_identification="CI-ASSOC-1998-0231",
         contact="Marie-Claire KOUASSI"),
    dict(nom="AeroTech Maintenance SARL", type_client="SOCIETE_MAINTENANCE", adresse="Zone Industrielle Yopougon, Abidjan",
         telephone="+225 27 23 45 67 89", email="contact@aerotech-maintenance.example", numero_identification="CI-RCCM-2016-B-8890",
         contact="Ibrahim SANOGO"),
    dict(nom="West Africa Cargo Charter", type_client="OPERATEUR_PRIVE", adresse="Aéroport FHB, Terminal Cargo, Abidjan",
         telephone="+225 27 21 98 76 54", email="ops@wa-cargocharter.example", numero_identification="CI-RCCM-2019-B-1207",
         contact="Aminata DIALLO"),
]

AERONEFS_PAR_CLIENT = {
    "Ivoire Airways": [
        dict(immatriculation="TU-IVA", type_aeronef="Avion de ligne", constructeur="ATR", modele="ATR 72-600",
             numero_serie="1487", annee_fabrication=2018, nombre_heures_vol=8400, nombre_cycles=6200),
        dict(immatriculation="TU-IVB", type_aeronef="Avion de ligne", constructeur="Airbus", modele="A319-100",
             numero_serie="6215", annee_fabrication=2014, nombre_heures_vol=21500, nombre_cycles=14300),
    ],
    "Garde Nationale — Escadrille Aviation": [
        dict(immatriculation="TU-GNA", type_aeronef="Hélicoptère", constructeur="Airbus Helicopters", modele="H145",
             numero_serie="20034", annee_fabrication=2019, nombre_heures_vol=3100, nombre_cycles=0),
        dict(immatriculation="TU-GNB", type_aeronef="Avion de transport", constructeur="Lockheed", modele="C-130H",
             numero_serie="4892", annee_fabrication=1998, nombre_heures_vol=15600, nombre_cycles=7800),
    ],
    "Aéroclub d'Abidjan": [
        dict(immatriculation="TU-CAA", type_aeronef="Avion léger", constructeur="Cessna", modele="172 Skyhawk",
             numero_serie="17281455", annee_fabrication=2005, nombre_heures_vol=4200, nombre_cycles=5100),
        dict(immatriculation="TU-CAB", type_aeronef="Avion léger", constructeur="Robin", modele="DR400",
             numero_serie="2214", annee_fabrication=2001, nombre_heures_vol=3600, nombre_cycles=4400),
        dict(immatriculation="TU-CAC", type_aeronef="Planeur", constructeur="Schleicher", modele="ASK 21",
             numero_serie="21456", annee_fabrication=1996, nombre_heures_vol=1900, nombre_cycles=3200),
    ],
    "AeroTech Maintenance SARL": [
        dict(immatriculation="TU-ATM", type_aeronef="Avion léger", constructeur="Beechcraft", modele="King Air 350",
             numero_serie="FL-812", annee_fabrication=2010, nombre_heures_vol=6700, nombre_cycles=4900),
    ],
    "West Africa Cargo Charter": [
        dict(immatriculation="TU-WCC", type_aeronef="Avion cargo", constructeur="Boeing", modele="737-400F",
             numero_serie="24124", annee_fabrication=1990, nombre_heures_vol=42000, nombre_cycles=21000),
        dict(immatriculation="TU-WCD", type_aeronef="Avion cargo", constructeur="ATR", modele="ATR 42-320F",
             numero_serie="0289", annee_fabrication=1994, nombre_heures_vol=31000, nombre_cycles=28500),
    ],
}

STAFF_USERS = [
    dict(username="dae_technicien1", first_name="Yao", last_name="KONAN", role="AGENT"),
    dict(username="dae_technicien2", first_name="Fatoumata", last_name="COULIBALY", role="AGENT"),
    dict(username="dae_qualite", first_name="Serge", last_name="ABLAN", role="CHEF_SERVICE"),
    dict(username="dae_magasinier", first_name="Paul", last_name="N'GUESSAN", role="AGENT"),
]

PIECES_CATALOGUE = [
    dict(reference="PR-JT-001", designation="Joint torique moteur", categorie="Étanchéité", prix_unitaire=Decimal("8500"), seuil_alerte=10, est_critique=False),
    dict(reference="PR-RL-002", designation="Roulement à billes train d'atterrissage", categorie="Mécanique", prix_unitaire=Decimal("145000"), seuil_alerte=3, est_critique=True),
    dict(reference="PR-PF-003", designation="Plaquette de frein", categorie="Freinage", prix_unitaire=Decimal("62000"), seuil_alerte=5, est_critique=True),
    dict(reference="PR-FL-004", designation="Filtre à huile moteur", categorie="Lubrification", prix_unitaire=Decimal("31000"), seuil_alerte=8, est_critique=False),
    dict(reference="PR-BT-005", designation="Batterie NiCd 24V", categorie="Électrique", prix_unitaire=Decimal("980000"), seuil_alerte=2, est_critique=True),
    dict(reference="PR-PN-006", designation="Pneu principal", categorie="Roues", prix_unitaire=Decimal("410000"), seuil_alerte=4, est_critique=True),
    dict(reference="PR-CH-007", designation="Chambre à air roue", categorie="Roues", prix_unitaire=Decimal("52000"), seuil_alerte=6, est_critique=False),
    dict(reference="PR-BG-008", designation="Bougie d'allumage", categorie="Moteur", prix_unitaire=Decimal("14500"), seuil_alerte=12, est_critique=False),
    dict(reference="PR-CB-009", designation="Câble de commande de vol", categorie="Structure", prix_unitaire=Decimal("78000"), seuil_alerte=4, est_critique=True),
    dict(reference="PR-HY-010", designation="Flexible hydraulique", categorie="Hydraulique", prix_unitaire=Decimal("46000"), seuil_alerte=5, est_critique=False),
    dict(reference="PR-AM-011", designation="Ampoule de balisage", categorie="Électrique", prix_unitaire=Decimal("9200"), seuil_alerte=15, est_critique=False),
    dict(reference="PR-JV-012", designation="Joint de verrière", categorie="Étanchéité", prix_unitaire=Decimal("23000"), seuil_alerte=6, est_critique=False),
]

EQUIPEMENTS_ATELIER = [
    dict(code="EQA-001", designation="Banc de test hydraulique"),
    dict(code="EQA-002", designation="Compresseur d'atelier"),
    dict(code="EQA-003", designation="Pont élévateur aéronef léger"),
    dict(code="EQA-004", designation="Testeur de batteries NiCd"),
    dict(code="EQA-005", designation="Station de charge pneumatique"),
    dict(code="EQA-006", designation="Banc d'équilibrage de roues"),
    dict(code="EQA-007", designation="Multimètre de précision"),
    dict(code="EQA-008", designation="Torquemètre étalonné"),
]


class Command(BaseCommand):
    help = "Alimente l'ensemble des donnees de demonstration de la Direction de l'Aeronautique (DAE)"

    def handle(self, *args, **options):
        with transaction.atomic():
            self._run()

    def _run(self):
        self.stdout.write("Démarrage du seed DAE…")
        direction = self._get_or_create_direction()
        users = self._seed_users(direction)
        clients = self._seed_clients()
        aeronefs = self._seed_aeronefs(clients)
        pieces = self._seed_pieces()
        equipements_atelier = self._seed_equipements_atelier()
        self._seed_maintenance_atelier(equipements_atelier, users)
        self._seed_certifications(users)
        demandes, ordres = self._seed_demandes_et_ot(clients, aeronefs, users)
        self._seed_interventions(ordres, users, pieces)
        self._seed_roues(aeronefs, ordres, users)
        self._seed_batteries(aeronefs, ordres, users)
        self._seed_equipements_aeronautiques(aeronefs)
        non_conformites = self._seed_qualite(ordres, users)
        self._seed_actions_correctives(non_conformites, users)
        self._seed_securite(ordres)
        self._seed_finance(clients, ordres)
        self._seed_satisfaction(ordres)
        self._seed_reclamations(clients, ordres, users)
        self.stdout.write(self.style.SUCCESS("Seed DAE terminé avec succès."))

    # ------------------------------------------------------------------
    def _get_or_create_direction(self):
        direction, _ = Direction.objects.get_or_create(
            nom="Direction de l'Aéronautique", defaults={"type_direction": "direction"}
        )
        return direction

    def _seed_users(self, direction):
        users = {}
        for data in STAFF_USERS:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={"first_name": data["first_name"], "last_name": data["last_name"], "email": f"{data['username']}@lanema-ci.example"},
            )
            if created:
                user.set_password("DaeDemo2026!")
                user.save()
            UserProfile.objects.update_or_create(
                user=user, defaults={"direction": direction, "role": data["role"]}
            )
            users[data["username"]] = user
        self.stdout.write(f"  Utilisateurs DAE : {len(users)}")
        return users

    def _seed_clients(self):
        clients = {}
        for data in CLIENTS_DATA:
            client, _ = ClientAeronautique.objects.get_or_create(nom=data["nom"], defaults=data)
            clients[data["nom"]] = client
        self.stdout.write(f"  Clients aéronautiques : {len(clients)}")
        return clients

    def _seed_aeronefs(self, clients):
        aeronefs = []
        for nom_client, liste in AERONEFS_PAR_CLIENT.items():
            client = clients[nom_client]
            for data in liste:
                aeronef, _ = Aeronef.objects.get_or_create(
                    immatriculation=data["immatriculation"],
                    defaults={**data, "client": client, "statut": "EN_SERVICE"},
                )
                aeronefs.append(aeronef)
        self.stdout.write(f"  Aéronefs : {len(aeronefs)}")
        return aeronefs

    def _seed_pieces(self):
        pieces = []
        for data in PIECES_CATALOGUE:
            stock_initial = random.randint(0, data["seuil_alerte"] * 3)
            piece, created = PieceRechange.objects.get_or_create(
                reference=data["reference"],
                defaults={**data, "quantite_stock": stock_initial},
            )
            pieces.append(piece)
            if created:
                MouvementPieceRechange.objects.create(piece=piece, type_mouvement="ENTREE", quantite=stock_initial + 10)
                MouvementPieceRechange.objects.create(piece=piece, type_mouvement="SORTIE", quantite=10)
        self.stdout.write(f"  Pièces de rechange : {len(pieces)}")
        return pieces

    def _seed_equipements_atelier(self):
        equipements = []
        for data in EQUIPEMENTS_ATELIER:
            statut = random.choices(["OPERATIONNEL", "MAINTENANCE", "HORS_SERVICE"], weights=[8, 1, 1])[0]
            eq, _ = EquipementAtelier.objects.get_or_create(code=data["code"], defaults={**data, "statut": statut})
            equipements.append(eq)
        self.stdout.write(f"  Équipements d'atelier : {len(equipements)}")
        return equipements

    def _seed_maintenance_atelier(self, equipements, users):
        for eq in equipements[:4]:
            PanneEquipementAtelier.objects.create(
                equipement=eq, description=f"Panne détectée sur {eq.designation.lower()}",
                date_reparation=jours_avant(random.randint(1, 20)) if random.random() > 0.3 else None,
            )
        for i, eq in enumerate(equipements):
            statut = "REALISEE" if i % 3 == 0 else ("PLANIFIEE" if i % 3 == 1 else "REPORTEE")
            date_prevue = jours_avant(-random.randint(1, 15)) if statut == "PLANIFIEE" else jours_avant(random.randint(5, 60))
            MaintenancePreventiveAtelier.objects.create(
                equipement=eq, date_prevue=date_prevue,
                date_realisee=jours_avant(random.randint(1, 30)) if statut == "REALISEE" else None,
                statut=statut,
            )
            EtalonnageAtelier.objects.create(
                equipement=eq, date_etalonnage=jours_avant(random.randint(10, 200)),
                date_prochain=jours_avant(-random.randint(1, 300)), resultat="CONFORME",
            )
        self.stdout.write("  Maintenance & étalonnages atelier alimentés")

    def _seed_certifications(self, users):
        competences = ["Maintenance ATR 72", "Maintenance Airbus A320", "Habilitation électrique B2", "Contrôle qualité NDT"]
        for username in ["dae_technicien1", "dae_technicien2"]:
            user = users[username]
            for competence in random.sample(competences, 2):
                CertificationTechnicien.objects.get_or_create(
                    technicien=user, competence=competence,
                    defaults={"date_obtention": jours_avant(random.randint(200, 900)),
                              "date_expiration": jours_avant(-random.randint(100, 500))},
                )
        self.stdout.write("  Certifications techniciens alimentées")

    def _seed_demandes_et_ot(self, clients, aeronefs, users):
        demandes = []
        ordres = []
        aeronefs_par_client = {}
        for a in aeronefs:
            aeronefs_par_client.setdefault(a.client_id, []).append(a)

        statuts_demande = ["NOUVELLE", "A_ETUDIER", "ACCEPTEE", "ACCEPTEE", "ACCEPTEE", "REFUSEE", "EN_TRAITEMENT"]
        statuts_ot_pool = [
            "A_PLANIFIER", "PLANIFIE", "EN_COURS", "EN_ATTENTE_PIECE", "EN_ATTENTE_CLIENT",
            "CONTROLE_QUALITE", "TERMINE", "VALIDE", "CLOTURE", "ANNULE",
        ]
        techniciens = [users["dae_technicien1"], users["dae_technicien2"]]

        demande_seq = DemandeDAE.objects.count()
        ot_seq = OrdreTravail.objects.count()
        annee = TODAY.year

        for client in clients.values():
            client_aeronefs = aeronefs_par_client.get(client.id, [])
            if not client_aeronefs:
                continue
            for i in range(4):
                aeronef = random.choice(client_aeronefs)
                demande_seq += 1
                statut_demande = statuts_demande[i % len(statuts_demande)]
                type_intervention = random.choice(["PREVENTIVE", "CORRECTIVE", "URGENCE"])
                urgence = random.choice(["NORMALE", "NORMALE", "HAUTE", "URGENTE"])
                jours_recul = random.randint(2, 150)
                demande = DemandeDAE.objects.create(
                    reference=f"DEM-DAE-{annee}-{demande_seq:05d}",
                    client=client, aeronef=aeronef, type_intervention=type_intervention,
                    description=f"{dict(PREVENTIVE='Maintenance préventive programmée', CORRECTIVE='Panne signalée par l’équipage', URGENCE='Intervention urgente requise')[type_intervention]} sur {aeronef.immatriculation}",
                    urgence=urgence, statut=statut_demande,
                )
                DemandeDAE.objects.filter(pk=demande.pk).update(date_reception=dt_jours_avant(jours_recul))
                demande.refresh_from_db()
                demandes.append(demande)

                if statut_demande == "ACCEPTEE":
                    ot_seq += 1
                    statut_ot = random.choice(statuts_ot_pool)
                    ot = OrdreTravail.objects.create(
                        reference=f"OT-DAE-{annee}-{ot_seq:05d}",
                        aeronef=aeronef, type_intervention=type_intervention,
                        technicien=random.choice(techniciens),
                        statut=statut_ot,
                    )
                    date_demande_ot = dt_jours_avant(jours_recul - 1)
                    # date_demande est auto_now_add : ne s'applique qu'a l'INSERT initial,
                    # donc une reaffectation en memoire suivie d'un save() complet la
                    # persiste correctement (contrairement a un .filter().update() qui
                    # serait ensuite ecrase par le ot.save() plus bas, l'objet en memoire
                    # n'etant jamais rafraichi).
                    ot.date_demande = date_demande_ot
                    if statut_ot != "A_PLANIFIER":
                        ot.date_prise_charge = date_demande_ot + timedelta(hours=random.randint(2, 48))
                    if statut_ot not in ("A_PLANIFIER", "PLANIFIE", "ANNULE"):
                        ot.date_debut = date_demande_ot + timedelta(days=random.randint(1, 3))
                    if statut_ot in ("TERMINE", "VALIDE", "CLOTURE"):
                        ot.date_fin = (date_demande_ot + timedelta(days=random.randint(4, 10))).date()
                        ot.date_fin_prevue = ot.date_fin - timedelta(days=random.choice([-1, 0, 1, 2]))
                    elif statut_ot not in ("A_PLANIFIER",):
                        ot.date_fin_prevue = jours_avant(-random.randint(1, 10))
                    ot.save()
                    demande.ordre_travail = ot
                    demande.date_traitement = date_demande_ot
                    demande.save(update_fields=["ordre_travail", "date_traitement"])
                    ordres.append(ot)
                elif statut_demande == "REFUSEE":
                    demande.date_traitement = dt_jours_avant(jours_recul - 1)
                    demande.save(update_fields=["date_traitement"])

        self.stdout.write(f"  Demandes : {len(demandes)} · Ordres de travail : {len(ordres)}")
        return demandes, ordres

    def _seed_interventions(self, ordres, users, pieces):
        techniciens = [users["dae_technicien1"], users["dae_technicien2"]]
        operations = ["DIAGNOSTIC", "DEMONTAGE", "INSPECTION", "REPARATION", "REMONTAGE", "TEST", "CONTROLE"]
        count = 0
        for ot in ordres:
            if ot.statut in ("A_PLANIFIER", "PLANIFIE", "ANNULE"):
                continue
            nb = random.randint(1, 4)
            for op in random.sample(operations, min(nb, len(operations))):
                interv = InterventionTechnique.objects.create(
                    ordre_travail=ot, technicien=random.choice(techniciens), operation=op,
                    description=f"{op.capitalize()} réalisé(e) sur {ot.aeronef.immatriculation}",
                    temps_passe_minutes=random.randint(30, 240),
                    mesures="Conforme aux tolérances constructeur" if random.random() > 0.2 else "",
                    resultat="Conforme" if random.random() > 0.15 else "Non conforme — reprise nécessaire",
                    observations="",
                )
                if random.random() > 0.5:
                    interv.pieces_utilisees.add(random.choice(pieces))
                count += 1
        self.stdout.write(f"  Interventions techniques : {count}")

    def _seed_roues(self, aeronefs, ordres, users):
        techniciens = [users["dae_technicien1"], users["dae_technicien2"]]
        types_roue = ["Roue principale", "Roue avant"]
        etapes = ["RECEPTION", "DEMONTAGE", "INSPECTION_PERIODIQUE", "NETTOYAGE", "REPARATION", "REMONTAGE", "CONTROLE_FINAL", "VALIDATION"]
        roues = []
        for i, aeronef in enumerate(aeronefs):
            for j in range(random.randint(1, 2)):
                numero_serie = f"ROU-{aeronef.immatriculation}-{j + 1}"
                statut = random.choice(["EN_SERVICE", "EN_INSPECTION", "REPAREE", "NON_CONFORME"])
                roue, created = RoueAeronef.objects.get_or_create(
                    numero_serie=numero_serie,
                    defaults=dict(
                        reference=f"RF-{numero_serie}", constructeur=random.choice(["Michelin", "Goodyear", "Dunlop"]),
                        type_roue=random.choice(types_roue), aeronef=aeronef, statut=statut,
                        nombre_cycles=random.randint(500, 8000), prochaine_inspection=jours_avant(-random.randint(10, 180)),
                    ),
                )
                roues.append(roue)
                if created:
                    for etape in random.sample(etapes, random.randint(2, 4)):
                        InspectionRoue.objects.create(
                            roue=roue, ordre_travail=random.choice(ordres) if ordres and random.random() > 0.5 else None,
                            technicien=random.choice(techniciens), conforme=random.random() > 0.15,
                            type_inspection=etape, observations="",
                        )
        self.stdout.write(f"  Roues aéronautiques : {len(roues)}")

    def _seed_batteries(self, aeronefs, ordres, users):
        techniciens = [users["dae_technicien1"], users["dae_technicien2"]]
        batteries = []
        for aeronef in aeronefs:
            numero_serie = f"BAT-{aeronef.immatriculation}"
            statut = random.choice(["EN_SERVICE", "EN_TEST", "RECHARGEE", "HORS_SERVICE"])
            batterie, created = BatterieAeronef.objects.get_or_create(
                numero_serie=numero_serie,
                defaults=dict(
                    reference=f"RF-{numero_serie}", type_batterie=random.choice(["NiCd", "Plomb-acide", "Li-ion"]),
                    capacite_nominale=random.choice(["24 Ah", "30 Ah", "40 Ah"]), tension_nominale="24 V",
                    aeronef=aeronef, statut=statut,
                    date_mise_en_service=jours_avant(random.randint(200, 1500)),
                    date_derniere_maintenance=jours_avant(random.randint(10, 200)),
                    prochain_controle=jours_avant(-random.randint(5, 90)),
                ),
            )
            batteries.append(batterie)
            if created:
                for _ in range(random.randint(1, 3)):
                    resultat = random.choices(["CONFORME", "NON_CONFORME", "A_REPARER", "A_REMPLACER"], weights=[6, 1, 1, 1])[0]
                    TestBatterie.objects.create(
                        batterie=batterie, ordre_travail=random.choice(ordres) if ordres and random.random() > 0.6 else None,
                        technicien=random.choice(techniciens), tension_mesuree="24.1 V", capacite_mesuree="28.5 Ah",
                        etat="Bon état" if resultat == "CONFORME" else "Dégradé", temperature="22°C",
                        charge=True, decharge=random.random() > 0.4, resultat=resultat, observations="",
                    )
        self.stdout.write(f"  Batteries d'aéronefs : {len(batteries)}")

    def _seed_equipements_aeronautiques(self, aeronefs):
        types_eq = ["ELECTRIQUE", "HYDRAULIQUE", "MECANIQUE", "AUTRE"]
        fabricants = ["Honeywell", "Collins Aerospace", "Safran", "Thales"]
        count = 0
        for aeronef in aeronefs:
            for _ in range(random.randint(1, 2)):
                type_eq = random.choice(types_eq)
                numero_serie = f"EQ-{aeronef.immatriculation}-{count + 1}"
                EquipementAeronautique.objects.get_or_create(
                    numero_serie=numero_serie,
                    defaults=dict(
                        reference=f"RF-{numero_serie}", type_equipement=type_eq, fabricant=random.choice(fabricants),
                        modele=f"Modèle-{random.randint(100, 999)}", aeronef=aeronef,
                        statut=random.choice(["EN_SERVICE", "EN_CONTROLE", "REPARE", "NON_CONFORME"]),
                    ),
                )
                count += 1
        self.stdout.write(f"  Équipements aéronautiques génériques : {count}")

    def _seed_qualite(self, ordres, users):
        origines = ["CONTROLE_QUALITE", "AUDIT", "INTERVENTION", "CLIENT", "INCIDENT"]
        gravites = ["MINEURE", "MAJEURE", "CRITIQUE"]
        non_conformites = []
        ordres_avec_nc = [o for o in ordres if o.statut in ("CONTROLE_QUALITE", "TERMINE", "VALIDE", "CLOTURE")]
        cibles = random.sample(ordres_avec_nc, min(6, len(ordres_avec_nc))) if ordres_avec_nc else []
        for ot in cibles:
            gravite = random.choices(gravites, weights=[5, 3, 2])[0]
            statut = "OUVERTE" if ot.statut == "CONTROLE_QUALITE" else random.choice(["OUVERTE", "EN_COURS", "CLOTUREE"])
            nc = NonConformiteDAE.objects.create(
                origine=random.choice(origines), ordre_travail=ot, gravite=gravite,
                description=f"Non-conformité détectée sur {ot.aeronef.immatriculation} — {ot.reference}",
                cause="Usure prématurée constatée lors du contrôle" if random.random() > 0.4 else "",
                responsable=users["dae_qualite"], statut=statut,
                date_echeance=jours_avant(-random.randint(5, 30)) if statut != "CLOTUREE" else None,
            )
            non_conformites.append(nc)
        for i in range(4):
            AuditQualiteDAE.objects.create(
                type_audit=random.choice(["Audit interne procédures", "Audit ANAC", "Audit constructeur"]),
                date_audit=jours_avant(random.randint(10, 300)),
                resultat=random.choices(["CONFORME", "NON_CONFORME", "CONFORME_AVEC_RESERVES"], weights=[5, 1, 2])[0],
            )
        self.stdout.write(f"  Non-conformités : {len(non_conformites)} · Audits qualité : 4")
        return non_conformites

    def _seed_actions_correctives(self, non_conformites, users):
        count = 0
        for nc in non_conformites:
            for _ in range(random.randint(1, 2)):
                if nc.statut == "CLOTUREE":
                    statut = "CLOTUREE"
                    efficace = True
                    date_verif = jours_avant(random.randint(1, 20))
                elif nc.statut == "EN_COURS":
                    statut = random.choice(["EN_COURS", "REALISEE", "VERIFIEE"])
                    efficace = True if statut == "VERIFIEE" else None
                    date_verif = jours_avant(random.randint(1, 10)) if statut == "VERIFIEE" else None
                else:
                    statut = "PLANIFIEE"
                    efficace = None
                    date_verif = None
                date_prevue = jours_avant(-random.randint(1, 15)) if statut == "PLANIFIEE" else jours_avant(random.randint(5, 40))
                ActionCorrectiveDAE.objects.create(
                    non_conformite=nc, analyse_cause="Analyse en cours de rédaction" if statut == "PLANIFIEE" else "Cause racine identifiée : défaut de lubrification",
                    description=f"Action corrective liée à {nc.reference}",
                    responsable=random.choice([users["dae_technicien1"], users["dae_technicien2"], users["dae_qualite"]]),
                    statut=statut, date_prevue=date_prevue,
                    date_realisation=jours_avant(random.randint(1, 15)) if statut in ("REALISEE", "VERIFIEE", "CLOTUREE") else None,
                    verification_efficacite="Efficacité confirmée lors du contrôle suivant" if efficace else "",
                    efficace=efficace, date_verification=date_verif,
                )
                count += 1
        self.stdout.write(f"  Actions correctives : {count}")

    def _seed_securite(self, ordres):
        for i in range(4):
            IncidentTechnique.objects.create(
                reference=f"INC-DAE-{i + 1:04d}", ordre_travail=random.choice(ordres) if ordres and random.random() > 0.5 else None,
                gravite=random.choice(["MINEURE", "MAJEURE", "CRITIQUE"]),
                description="Incident technique constaté lors d'une intervention", est_accident=False,
            )
        for i in range(3):
            EcartReglementaire.objects.create(
                reference=f"ECART-DAE-{i + 1:04d}", description="Écart constaté par rapport à la réglementation ANAC",
                resolu=random.random() > 0.4,
            )
        for i in range(2):
            RapportSecurite.objects.create(reference=f"RAPSEC-DAE-{i + 1:04d}", description="Rapport de sécurité périodique")
        for i in range(3):
            ControleReglementaire.objects.create(
                reference=f"CTRL-DAE-{i + 1:04d}", organisme="ANAC",
                date_controle=jours_avant(random.randint(10, 300)),
                resultat=random.choices(["REUSSI", "ECHEC"], weights=[4, 1])[0],
            )
        for titre in ["Formation sécurité piste", "Recyclage facteurs humains", "Formation gestion des risques"]:
            FormationSecurite.objects.create(
                titre=titre, date_formation=jours_avant(random.randint(10, 250)),
                nombre_participants=random.randint(5, 20), duree_heures=Decimal(random.choice([4, 8, 16])),
            )
        self.stdout.write("  Sécurité (incidents, écarts, rapports, contrôles ANAC, formations) alimentée")

    def _seed_finance(self, clients, ordres):
        annee = TODAY.year
        devis_seq = DevisDAE.objects.count()
        bc_seq = BonCommandeDAE.objects.count()
        facture_seq = FactureDAE.objects.count()
        ordres_valides = [o for o in ordres if o.statut in ("TERMINE", "VALIDE", "CLOTURE")]

        for client in clients.values():
            for _ in range(2):
                mo = Decimal(random.randint(20, 150)) * 5000
                pi = Decimal(random.randint(5, 60)) * 10000
                frais = Decimal(random.randint(0, 5)) * 10000
                devis_seq += 1
                devis = DevisDAE.objects.create(
                    reference=f"DEV-DAE-{annee}-{devis_seq:05d}", client=client,
                    description="Devis pour intervention de maintenance",
                    montant_main_oeuvre=mo, montant_pieces=pi, frais_supplementaires=frais,
                    taux_tva=Decimal("18"),
                    statut=random.choice(["BROUILLON", "ENVOYE", "ACCEPTE", "REFUSE"]),
                    date_validite=jours_avant(-30),
                )
                if devis.statut == "ACCEPTE" and random.random() > 0.4:
                    bc_seq += 1
                    BonCommandeDAE.objects.create(
                        reference=f"BC-DAE-{annee}-{bc_seq:05d}", devis=devis, client=client,
                        montant_ttc=devis.montant_ttc, statut=random.choice(["EN_ATTENTE", "SIGNE"]),
                        date_signature=jours_avant(random.randint(1, 20)) if random.random() > 0.5 else None,
                    )

        for ot in ordres_valides:
            facture_seq += 1
            mo = Decimal(random.randint(20, 100)) * 5000
            pi = Decimal(random.randint(5, 40)) * 10000
            frais = Decimal(random.randint(0, 3)) * 10000
            facture = FactureDAE(
                reference=f"FACT-DAE-{annee}-{facture_seq:05d}", ordre_travail=ot, client=ot.aeronef.client,
                montant_main_oeuvre=mo, montant_pieces=pi, frais_supplementaires=frais,
                taux_tva=Decimal("18"),
                statut=random.choices(["EMISE", "PAYEE", "IMPAYEE"], weights=[3, 5, 2])[0],
            )
            facture.recalculer_totaux()
            if facture.statut == "PAYEE":
                facture.date_paiement = jours_avant(random.randint(1, 30))
            facture.save()
        self.stdout.write(f"  Devis, bons de commande et factures alimentés ({len(ordres_valides)} factures)")

    def _seed_satisfaction(self, ordres):
        count = 0
        for ot in ordres:
            if ot.statut not in ("TERMINE", "VALIDE", "CLOTURE"):
                continue
            if random.random() > 0.7:
                continue
            satisfaction, created = SatisfactionDAE.objects.get_or_create(ordre_travail=ot)
            if not created:
                continue
            satisfaction.date_envoi = dt_jours_avant(random.randint(1, 20))
            if random.random() > 0.4:
                for champ in ["note_qualite", "note_delai", "note_accueil", "note_communication", "note_prestation_technique"]:
                    setattr(satisfaction, champ, random.randint(3, 5))
                satisfaction.commentaire = "Intervention satisfaisante, délais respectés."
                satisfaction.date_evaluation = satisfaction.date_envoi + timedelta(days=random.randint(1, 5))
            satisfaction.save()
            count += 1
        self.stdout.write(f"  Fiches de satisfaction : {count}")

    def _seed_reclamations(self, clients, ordres, users):
        types_recl = ["RETARD", "PROBLEME_TECHNIQUE", "PROBLEME_ADMINISTRATIF", "PROBLEME_FACTURATION", "QUALITE_INSUFFISANTE"]
        statuts = ["ENREGISTREE", "EN_ANALYSE", "AFFECTEE", "EN_TRAITEMENT", "REPONSE_ENVOYEE", "CLOTUREE"]
        count = 0
        for client in clients.values():
            for _ in range(2):
                statut = random.choice(statuts)
                ot = random.choice(ordres) if ordres and random.random() > 0.4 else None
                reclamation = ReclamationClientDAE.objects.create(
                    client=client, ordre_travail=ot, type_reclamation=random.choice(types_recl),
                    description="Réclamation formulée par le client concernant une intervention récente",
                    analyse="Analyse effectuée par le service qualité" if statut not in ("ENREGISTREE",) else "",
                    responsable=users["dae_qualite"] if statut not in ("ENREGISTREE", "EN_ANALYSE") else None,
                    reponse="Nos excuses, mesures correctives engagées." if statut in ("REPONSE_ENVOYEE", "CLOTUREE") else "",
                    statut=statut,
                    note_satisfaction=random.randint(2, 5) if statut == "CLOTUREE" and random.random() > 0.3 else None,
                )
                if statut == "CLOTUREE":
                    ReclamationClientDAE.objects.filter(pk=reclamation.pk).update(date_traitement=jours_avant(random.randint(1, 15)))
                count += 1
        self.stdout.write(f"  Réclamations clients : {count}")
