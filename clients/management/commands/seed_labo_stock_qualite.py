"""Seed complementaire du portail labo — alimente tout ce que
`seed_labo_workflow` (demandes -> proforma -> facture -> echantillon/essai)
ne couvre pas : Stock (Articles, Entrepots, Emplacements, Lots, Alertes,
Quarantaines, Transferts, Receptions, Sorties, Tracabilite, Inventaires),
Metrologie, Qualite (non-conformites, audits, actions), Reporting,
Notifications, Reclamations et Administration > Vitrine du site.

Reutilise (par email) les comptes crees par `seed_labo_workflow` s'ils
existent deja ; sinon les cree lui-meme, pour rester executable seul.

Usage : python manage.py seed_labo_workflow   (recommande d'abord)
        python manage.py seed_labo_stock_qualite
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from clients.models import ClientProfile, ReclamationClient
from laboratoires.models import Laboratoire
from landing.models import AIKeywordResponse, ContactMessage, FAQ, NewsArticle
from metrologie.models import Equipement, Etalonnage, MaintenancePreventive, PanneEquipement
from notifications.models import Notification
from qualite.models import ActionQualite, Audit, Essai, NonConformite, RecommandationAudit, TypeEchantillon
from reporting.models import Rapport, RapportEssai
from stock.models import (
    Alerte,
    Article,
    CategorieArticle,
    Domaine,
    Emplacement,
    Entrepot,
    Inventaire,
    LigneInventaire,
    LigneReception,
    Lot,
    MouvementStock,
    Quarantaine,
    Reception,
    SortieStock,
    TransfertInterne,
)

STAFF_PASSWORD = "Lanema2026!"
TODAY = timezone.now().date()
NOW = timezone.now()


def jours_avant(n):
    return TODAY - timedelta(days=n)


def dt_jours_avant(n):
    return NOW - timedelta(days=n)


class Command(BaseCommand):
    help = "Alimente Stock, Metrologie, Qualite (NC/audits), Reporting, Notifications, Reclamations et la Vitrine du site (portail labo)"

    def handle(self, *args, **options):
        with transaction.atomic():
            self._run()

    def _run(self):
        self.stdout.write("Démarrage du seed complémentaire portail labo…")
        staff = self._ensure_staff()
        clients = self._ensure_clients()
        laboratoires = self._ensure_laboratoires(staff)

        domaines, categories, entrepots, emplacements = self._seed_stock_referentiel()
        articles, lots = self._seed_articles_et_lots(categories, emplacements)
        self._seed_alertes_et_quarantaines(articles, lots, staff)
        self._seed_receptions(articles, entrepots, staff)
        self._seed_transferts(lots, emplacements, staff)
        self._seed_sorties(lots, staff)
        self._seed_inventaires(entrepots, articles, lots, staff)

        equipements = self._seed_metrologie(laboratoires, staff)
        self._seed_maintenance_metrologie(equipements)

        types_echantillon = self._seed_types_echantillon()
        non_conformites = self._seed_qualite(staff)
        self._seed_actions_qualite(non_conformites, staff)
        self._seed_audits()

        self._seed_reporting(staff)
        self._seed_notifications(staff, clients)
        self._seed_landing()
        self._seed_reclamations(clients)

        self.stdout.write(self.style.SUCCESS("Seed complémentaire portail labo terminé."))

    # ------------------------------------------------------------------
    def _get_or_make_user(self, username, email, first_name, last_name, role, organisation="", extra=None):
        user, created = User.objects.get_or_create(
            email=email, defaults={"username": username, "first_name": first_name, "last_name": last_name}
        )
        if created:
            user.set_password(STAFF_PASSWORD)
            user.save()
        ClientProfile.objects.update_or_create(
            user=user, defaults={"role": role, "organisation": organisation, **(extra or {})}
        )
        return user

    def _ensure_staff(self):
        staff = {
            "responsable": self._get_or_make_user("responsable.labo", "responsable.labo@lanema-ci.com", "Aya", "Koffi", "ADMIN", "LANEMA - DEA"),
            "gestionnaire": self._get_or_make_user("gestionnaire.labo", "gestionnaire.labo@lanema-ci.com", "Bakary", "Traore", "GESTIONNAIRE", "LANEMA - DEA"),
            "comptable": self._get_or_make_user("comptable.labo", "comptable.labo@lanema-ci.com", "Chantal", "Nguessan", "COMPTABLE", "LANEMA - DEA"),
            "technicien1": self._get_or_make_user("technicien.labo", "technicien.labo@lanema-ci.com", "David", "Ouattara", "TECHNICIEN", "LANEMA - DEA"),
            "technicien2": self._get_or_make_user("technicien2.labo", "technicien2.labo@lanema-ci.com", "Estelle", "Assamoi", "TECHNICIEN", "LANEMA - DEA"),
            "fournisseur": self._get_or_make_user(
                "fournisseur.reactifs", "contact@reactifs-ouest-afrique.example", "Moussa", "Kone", "FOURNISSEUR",
                "Réactifs Ouest Afrique SARL", extra={"raison_sociale": "Réactifs Ouest Afrique SARL", "telephone": "+225 07 12 34 56 78"},
            ),
        }
        self.stdout.write(f"  Personnel labo (staff + fournisseur) : {len(staff)}")
        return staff

    def _ensure_clients(self):
        data = [
            ("client1.entreprise", "contact@agrosarl.ci", "AGRO SARL", "Jean", "Kouassi"),
            ("client2.entreprise", "qualite@ivoireeau.ci", "Ivoire Eau Distribution", "Fatou", "Diabate"),
            ("client3.entreprise", "labo@nutrifoods.ci", "NutriFoods CI", "Marc", "Yao"),
            ("client4.entreprise", "achats@batico.ci", "BATICO Industries", "Aicha", "Sanogo"),
            ("client5.entreprise", "contact@pharmaplus.ci", "PharmaPlus CI", "Yves", "Brou"),
        ]
        clients = []
        for username, email, raison_sociale, first_name, last_name in data:
            user = self._get_or_make_user(
                username, email, first_name, last_name, "CLIENT", raison_sociale,
                extra={"raison_sociale": raison_sociale, "adresse": "Abidjan, Côte d'Ivoire",
                       "telephone": "+225 07 00 00 00", "contact_nom": f"{first_name} {last_name}",
                       "type_subscription": "STANDARD"},
            )
            clients.append(user)
        self.stdout.write(f"  Clients labo : {len(clients)}")
        return clients

    def _ensure_laboratoires(self, staff):
        labos = {}
        labos["deal"], _ = Laboratoire.objects.get_or_create(
            code="DEAL", defaults={"nom": "Direction des Essais et Analyses de Laboratoire", "responsable": staff["responsable"], "capacite_journaliere": 20},
        )
        labos["micro"], _ = Laboratoire.objects.get_or_create(
            code="MICRO", defaults={"nom": "Laboratoire de Microbiologie", "responsable": staff["gestionnaire"], "capacite_journaliere": 15},
        )
        labos["met"], _ = Laboratoire.objects.get_or_create(
            code="MET", defaults={"nom": "Laboratoire de Métrologie & Étalonnage", "responsable": staff["technicien1"], "capacite_journaliere": 10},
        )
        self.stdout.write(f"  Laboratoires : {len(labos)}")
        return labos

    # ------------------------------------------------------------------
    def _seed_stock_referentiel(self):
        domaines = {}
        for nom, code in [("Analyses Laboratoire", "DOM-ANA"), ("Métrologie & Étalonnage", "DOM-MET")]:
            domaines[code], _ = Domaine.objects.get_or_create(code=code, defaults={"nom": nom, "description": nom})

        categories = {}
        cat_data = [
            ("Réactifs chimiques", "CAT-REACT", "DOM-ANA"),
            ("Verrerie de laboratoire", "CAT-VERRE", "DOM-ANA"),
            ("Consommables microbiologie", "CAT-MICRO", "DOM-ANA"),
            ("Équipements de protection", "CAT-EPI", "DOM-ANA"),
            ("Pièces & masses étalons", "CAT-METPIECE", "DOM-MET"),
        ]
        for nom, code, dom_code in cat_data:
            categories[code], _ = CategorieArticle.objects.get_or_create(
                code=code, defaults={"nom": nom, "domaine": domaines[dom_code]}
            )

        entrepots = {}
        for nom, code in [("Entrepôt Principal Abidjan", "ENT-ABJ"), ("Entrepôt Annexe Bouaké", "ENT-BKE")]:
            entrepots[code], _ = Entrepot.objects.get_or_create(code=code, defaults={"nom": nom, "adresse": nom})

        emplacements = []
        for ent_code, ent in entrepots.items():
            for allee in ["A", "B", "C"]:
                code = f"EMP-{ent_code}-{allee}1"
                emp, _ = Emplacement.objects.get_or_create(
                    code=code, defaults={"entrepot": ent, "allee": allee, "rayon": "1"}
                )
                emplacements.append(emp)

        self.stdout.write(f"  Référentiel stock : {len(domaines)} domaines, {len(categories)} catégories, {len(entrepots)} entrepôts, {len(emplacements)} emplacements")
        return domaines, categories, entrepots, emplacements

    def _seed_articles_et_lots(self, categories, emplacements):
        articles_data = [
            ("ART-001", "Acide sulfurique 98% (1L)", "CAT-REACT", "L", 45000),
            ("ART-002", "Hydroxyde de sodium (500g)", "CAT-REACT", "KG", 18000),
            ("ART-003", "Éthanol absolu (1L)", "CAT-REACT", "L", 22000),
            ("ART-004", "Milieu de culture gélosé (boîte de 20)", "CAT-MICRO", "BOITE", 35000),
            ("ART-005", "Écouvillons stériles (sachet de 100)", "CAT-MICRO", "SACHET", 12000),
            ("ART-006", "Béchers 250 mL", "CAT-VERRE", "UNITE", 4500),
            ("ART-007", "Fioles jaugées 100 mL", "CAT-VERRE", "UNITE", 8500),
            ("ART-008", "Pipettes graduées 10 mL", "CAT-VERRE", "UNITE", 3200),
            ("ART-009", "Gants nitrile (boîte de 100)", "CAT-EPI", "BOITE", 9500),
            ("ART-010", "Blouses de laboratoire", "CAT-EPI", "UNITE", 15000),
            ("ART-011", "Lunettes de protection", "CAT-EPI", "UNITE", 6000),
            ("ART-012", "Masses étalons classe E2 (jeu)", "CAT-METPIECE", "JEU", 320000),
            ("ART-013", "Certificats de vérification (lot)", "CAT-METPIECE", "LOT", 25000),
            ("ART-014", "Solutions tampon pH (jeu de 3)", "CAT-REACT", "JEU", 28000),
            ("ART-015", "Boîtes de Petri jetables (sachet de 50)", "CAT-MICRO", "SACHET", 16000),
        ]
        articles = []
        for ref, designation, cat_code, unite, prix in articles_data:
            seuil = random.choice([5, 8, 10, 15])
            stock = random.choice([0, 2, 5, 8, 15, 30, 50])
            article, _ = Article.objects.get_or_create(
                reference_interne=ref,
                defaults=dict(
                    designation=designation, categorie=categories[cat_code], emplacement=random.choice(emplacements),
                    unite_mesure=unite, quantite_stock=stock, seuil_alerte=seuil,
                    est_critique=stock <= seuil, prix_unitaire=Decimal(prix),
                ),
            )
            articles.append(article)

        lots = []
        for article in articles:
            for i in range(random.randint(1, 2)):
                numero_lot = f"LOT-{article.reference_interne}-{i + 1}"
                quantite_initiale = float(random.randint(10, 100))
                quantite_restante = round(quantite_initiale * random.uniform(0.1, 1.0), 1)
                peremption = jours_avant(-random.randint(-60, 180)) if random.random() > 0.3 else None
                lot, created = Lot.objects.get_or_create(
                    article=article, numero_lot=numero_lot,
                    defaults=dict(
                        quantite_attendue=quantite_initiale, quantite_initiale=quantite_initiale,
                        quantite_restante=quantite_restante, unite=article.unite_mesure,
                        date_peremption=peremption, ouvert=random.random() > 0.5,
                        emplacement=article.emplacement,
                    ),
                )
                if created:
                    lots.append(lot)
        self.stdout.write(f"  Articles : {len(articles)} · Lots : {len(lots)}")
        return articles, lots

    def _seed_alertes_et_quarantaines(self, articles, lots, staff):
        count_alertes = 0
        for article in articles:
            if article.quantite_stock <= 0:
                type_alerte, priorite = "RUPTURE", "CRITIQUE"
            elif article.quantite_stock <= article.seuil_alerte:
                type_alerte, priorite = "STOCK_CRITIQUE", "URGENT"
            else:
                continue
            traitee = random.random() > 0.6
            Alerte.objects.create(
                titre=f"{dict(RUPTURE='Rupture de stock', STOCK_CRITIQUE='Stock critique')[type_alerte]} — {article.designation}",
                message=f"L'article {article.reference_interne} ({article.designation}) est en dessous du seuil d'alerte.",
                type_alerte=type_alerte, niveau_priorite=priorite, traitee=traitee,
                commentaire="Réapprovisionnement demandé au fournisseur." if traitee else "",
                date_traitement=dt_jours_avant(random.randint(1, 10)) if traitee else None,
                traite_par=staff["gestionnaire"] if traitee else None,
            )
            count_alertes += 1

        lots_perimes = [l for l in lots if l.date_peremption and l.date_peremption < TODAY]
        for lot in lots_perimes[:5]:
            Alerte.objects.create(
                titre=f"Péremption — lot {lot.numero_lot}",
                message=f"Le lot {lot.numero_lot} de {lot.article.designation} est périmé depuis le {lot.date_peremption}.",
                type_alerte="PEREMPTION", niveau_priorite="URGENT", traitee=False,
            )
            count_alertes += 1

        count_quarantaines = 0
        for lot in random.sample(lots, min(4, len(lots))):
            levee = random.random() > 0.5
            Quarantaine.objects.create(
                lot=lot, motif="Non-conformité constatée lors du contrôle de réception",
                mis_en_quarantaine_par=staff["technicien1"], levee=levee,
                date_levee=dt_jours_avant(random.randint(1, 15)) if levee else None,
                leve_par=staff["gestionnaire"] if levee else None,
                decision="Libéré après contrôle complémentaire" if levee else "",
                commentaire="",
            )
            if levee:
                MouvementStock.objects.create(
                    article=lot.article, lot=lot, type_mouvement="QUARANTAINE_SORTIE",
                    quantite=lot.quantite_restante, quantite_avant=0, quantite_apres=lot.quantite_restante,
                    reference_document=lot.numero_lot, description="Levée de quarantaine", utilisateur=staff["gestionnaire"],
                )
            else:
                MouvementStock.objects.create(
                    article=lot.article, lot=lot, type_mouvement="QUARANTAINE_ENTREE",
                    quantite=lot.quantite_restante, quantite_avant=lot.quantite_restante, quantite_apres=0,
                    reference_document=lot.numero_lot, description="Mise en quarantaine", utilisateur=staff["technicien1"],
                )
            count_quarantaines += 1

        self.stdout.write(f"  Alertes : {count_alertes} · Quarantaines : {count_quarantaines}")

    def _seed_receptions(self, articles, entrepots, staff):
        count = 0
        for i in range(4):
            statut = random.choice(["EN_COURS", "VERIFIEE", "VALIDEE", "REJETEE"])
            reception = Reception.objects.create(
                fournisseur=staff["fournisseur"], date_livraison_prevue=jours_avant(-random.randint(1, 20)),
                numero_commande=f"CMD-{2026}-{i + 1:04d}", numero_bl=f"BL-{i + 1:05d}",
                statut=statut, receptionne_par=staff["technicien1"],
                verifie_par=staff["gestionnaire"] if statut in ("VERIFIEE", "VALIDEE", "REJETEE") else None,
                valide_par=staff["responsable"] if statut == "VALIDEE" else None,
                date_verification=dt_jours_avant(random.randint(1, 10)) if statut in ("VERIFIEE", "VALIDEE", "REJETEE") else None,
                date_validation=dt_jours_avant(random.randint(1, 5)) if statut == "VALIDEE" else None,
            )
            for article in random.sample(articles, 3):
                qte_attendue = float(random.randint(10, 50))
                qte_recue = qte_attendue if random.random() > 0.2 else qte_attendue - random.randint(1, 5)
                LigneReception.objects.create(
                    reception=reception, article=article, quantite_attendue=qte_attendue, quantite_recue=qte_recue,
                    unite=article.unite_mesure, numero_lot=f"LOT-{article.reference_interne}-REC{i + 1}",
                    date_peremption=jours_avant(-random.randint(60, 400)), conforme=qte_recue == qte_attendue,
                )
                if statut == "VALIDEE":
                    MouvementStock.objects.create(
                        article=article, type_mouvement="ENTREE", quantite=qte_recue,
                        quantite_avant=article.quantite_stock, quantite_apres=article.quantite_stock + qte_recue,
                        reference_document=f"REC-{i + 1}", description="Réception validée", reception=reception,
                        utilisateur=staff["technicien1"],
                    )
            count += 1
        self.stdout.write(f"  Réceptions : {count}")

    def _seed_transferts(self, lots, emplacements, staff):
        count = 0
        for lot in random.sample(lots, min(3, len(lots))):
            destination = random.choice(emplacements)
            valide = random.random() > 0.3
            execute = valide and random.random() > 0.3
            transfert = TransfertInterne.objects.create(
                lot=lot, emplacement_source=lot.emplacement, emplacement_destination=destination,
                quantite=min(lot.quantite_restante, 5), unite=lot.unite,
                motif="Réorganisation de l'entrepôt", valide=valide, execute=execute,
            )
            if execute:
                MouvementStock.objects.create(
                    article=lot.article, lot=lot, type_mouvement="TRANSFERT", quantite=transfert.quantite,
                    quantite_avant=lot.quantite_restante, quantite_apres=lot.quantite_restante,
                    reference_document=f"TRF-{transfert.id}", description="Transfert interne exécuté",
                    transfert=transfert, utilisateur=staff["technicien1"],
                )
            count += 1
        self.stdout.write(f"  Transferts internes : {count}")

    def _seed_sorties(self, lots, staff):
        types_sortie = ["CONSOMMATION", "ANALYSE", "PERTE", "PEREMPTION", "RETOUR_FOURNISSEUR", "DESTRUCTION", "AUTRE"]
        count = 0
        for lot in random.sample(lots, min(6, len(lots))):
            quantite = min(lot.quantite_restante, round(random.uniform(1, 5), 1))
            valide = random.random() > 0.3
            sortie = SortieStock.objects.create(
                lot=lot, quantite=quantite, type_sortie=random.choice(types_sortie),
                motif="Sortie pour analyse en cours", utilisateur=staff["technicien1"],
                valide=valide, valide_par=staff["gestionnaire"] if valide else None,
                date_validation=dt_jours_avant(random.randint(1, 10)) if valide else None,
            )
            if valide:
                MouvementStock.objects.create(
                    article=lot.article, lot=lot, type_mouvement="SORTIE", quantite=quantite,
                    quantite_avant=lot.quantite_restante, quantite_apres=max(0, lot.quantite_restante - quantite),
                    reference_document=sortie.numero_sortie, description="Sortie de stock validée",
                    sortie=sortie, utilisateur=staff["technicien1"],
                )
            count += 1
        self.stdout.write(f"  Sorties de stock : {count}")

    def _seed_inventaires(self, entrepots, articles, lots, staff):
        count = 0
        for ent_code, entrepot in list(entrepots.items())[:2]:
            statut = random.choice(["PLANIFIE", "EN_COURS", "TERMINE", "VALIDE"])
            inventaire = Inventaire.objects.create(
                type_inventaire=random.choice(["COMPLET", "PARTIEL", "TOURNANT"]), statut=statut,
                entrepot=entrepot, date_debut=dt_jours_avant(random.randint(5, 30)),
                date_fin=dt_jours_avant(random.randint(1, 4)) if statut in ("TERMINE", "VALIDE") else None,
                responsable=staff["gestionnaire"],
            )
            for article in random.sample(articles, min(6, len(articles))):
                quantite_comptee = article.quantite_stock + random.choice([-2, -1, 0, 0, 0, 1, 2]) if statut in ("TERMINE", "VALIDE") else None
                LigneInventaire.objects.create(
                    inventaire=inventaire, article=article, emplacement=article.emplacement,
                    quantite_theorique=article.quantite_stock, quantite_comptee=quantite_comptee,
                    compte_par=staff["technicien2"] if quantite_comptee is not None else None,
                    date_comptage=dt_jours_avant(random.randint(1, 5)) if quantite_comptee is not None else None,
                )
            count += 1
        self.stdout.write(f"  Inventaires : {count}")

    # ------------------------------------------------------------------
    def _seed_metrologie(self, laboratoires, staff):
        equipements_data = [
            ("EQM-001", "Balance analytique", "BALANCE", "Sartorius", "Entris II"),
            ("EQM-002", "Étuve de séchage", "ETUVE", "Memmert", "UF110"),
            ("EQM-003", "Presse hydraulique d'essai", "PRESSE", "Instron", "5960"),
            ("EQM-004", "Thermomètre étalon", "THERMOMETRE", "Testo", "735-2"),
            ("EQM-005", "Balance de précision", "BALANCE", "Mettler Toledo", "XPE205"),
            ("EQM-006", "Étuve à moufle", "ETUVE", "Nabertherm", "L9/11"),
            ("EQM-007", "pH-mètre de laboratoire", "AUTRE", "Hanna", "HI2020"),
            ("EQM-008", "Thermo-hygromètre", "THERMOMETRE", "Vaisala", "HM70"),
        ]
        equipements = []
        for code, designation, type_eq, marque, modele in equipements_data:
            dernier = jours_avant(random.randint(60, 400))
            prochain = jours_avant(-random.randint(-60, 200))
            statut = "ETALONNAGE_REQUIS" if prochain < TODAY else random.choice(["OPERATIONNEL", "OPERATIONNEL", "MAINTENANCE"])
            eq, _ = Equipement.objects.get_or_create(
                code=code, defaults=dict(
                    designation=designation, type=type_eq, marque=marque, modele=modele,
                    date_dernier_etalonnage=dernier, date_prochain_etalonnage=prochain,
                    localisation="Laboratoire métrologie", laboratoire=laboratoires["met"],
                    responsable=staff["technicien1"], statut=statut,
                ),
            )
            equipements.append(eq)
        self.stdout.write(f"  Équipements de métrologie : {len(equipements)}")
        return equipements

    def _seed_maintenance_metrologie(self, equipements):
        count_etal = count_panne = count_maint = 0
        for eq in equipements:
            for _ in range(random.randint(1, 2)):
                Etalonnage.objects.create(
                    equipement=eq, date_etalonnage=jours_avant(random.randint(30, 300)),
                    date_prochain=jours_avant(-random.randint(-30, 200)),
                    prestataire=random.choice(["COFRAC", "LNE", "Interne"]), resultat="CONFORME",
                )
                count_etal += 1
        for eq in equipements[:3]:
            PanneEquipement.objects.create(
                equipement=eq, date_reparation=jours_avant(random.randint(1, 20)) if random.random() > 0.3 else None,
                cout=Decimal(random.randint(20, 200) * 1000), description="Panne détectée lors du contrôle périodique",
            )
            count_panne += 1
        for eq in equipements:
            statut = random.choice(["PLANIFIEE", "REALISEE", "REPORTEE"])
            MaintenancePreventive.objects.create(
                equipement=eq, date_prevue=jours_avant(-random.randint(1, 15)) if statut == "PLANIFIEE" else jours_avant(random.randint(5, 60)),
                date_realisee=jours_avant(random.randint(1, 30)) if statut == "REALISEE" else None,
                statut=statut, reussie=True if statut == "REALISEE" else None,
            )
            count_maint += 1
        self.stdout.write(f"  Étalonnages : {count_etal} · Pannes : {count_panne} · Maintenances préventives : {count_maint}")

    # ------------------------------------------------------------------
    def _seed_types_echantillon(self):
        types = []
        for nom in ["Eau potable", "Sol agricole", "Produit alimentaire", "Échantillon microbiologique", "Instrument à étalonner"]:
            t, _ = TypeEchantillon.objects.get_or_create(nom=nom, defaults={"description": nom, "actif": True})
            types.append(t)
        return types

    def _seed_qualite(self, staff):
        essais_existants = list(Essai.objects.all()[:10])
        non_conformites = []
        gravites = ["MINEURE", "MAJEURE", "CRITIQUE"]
        for i in range(6):
            essai = random.choice(essais_existants) if essais_existants and random.random() > 0.3 else None
            nc = NonConformite.objects.create(
                type_nc=random.choice(["INTERNE", "EXTERNE"]), gravite=random.choices(gravites, weights=[5, 3, 2])[0],
                description="Non-conformité relevée lors du contrôle qualité du processus d'analyse.",
                responsable=staff["gestionnaire"], essai=essai,
            )
            non_conformites.append(nc)
        self.stdout.write(f"  Non-conformités qualité : {len(non_conformites)}")
        return non_conformites

    def _seed_actions_qualite(self, non_conformites, staff):
        count = 0
        for nc in non_conformites:
            for _ in range(random.randint(1, 2)):
                statut = random.choice(["PLANIFIEE", "EN_COURS", "CLOTUREE"])
                ActionQualite.objects.create(
                    non_conformite=nc, type=random.choice(["CORRECTIVE", "PREVENTIVE"]),
                    description=f"Action liée à la non-conformité #{nc.numero}",
                    responsable=random.choice([staff["technicien1"], staff["technicien2"], staff["gestionnaire"]]),
                    statut=statut, date_cloture=jours_avant(random.randint(1, 20)) if statut == "CLOTUREE" else None,
                )
                count += 1
        self.stdout.write(f"  Actions qualité : {count}")

    def _seed_audits(self):
        audits = []
        for i in range(4):
            audit = Audit.objects.create(
                reference=f"AUD-{TODAY.year}-{i + 1:03d}", type_audit=random.choice(["INTERNE", "EXTERNE"]),
                organisme=random.choice(["COFRAC", "Audit interne LANEMA", "ANOR"]),
                date_audit=jours_avant(random.randint(10, 300)),
                resultat=random.choice(["Conforme", "Conforme avec réserves", "Non conforme"]),
            )
            audits.append(audit)
            for _ in range(random.randint(1, 2)):
                RecommandationAudit.objects.create(
                    audit=audit, description="Recommandation issue de l'audit — mise à jour de la procédure concernée.",
                    appliquee=random.random() > 0.5, date_echeance=jours_avant(-random.randint(5, 60)),
                )
        self.stdout.write(f"  Audits qualité : {len(audits)}")

    # ------------------------------------------------------------------
    def _seed_reporting(self, staff):
        for type_rapport, titre in [
            ("SYNTHSE_DEMANDES", "Synthèse mensuelle des demandes"),
            ("SYNTHSE_FACTURATION", "Synthèse de facturation du trimestre"),
            ("PERSONNALISE", "Rapport d'activité du laboratoire microbiologie"),
            ("PERSONNALISE", "Bilan qualité annuel"),
        ]:
            Rapport.objects.create(type_rapport=type_rapport, titre=titre, parametres={}, cree_par=staff["responsable"])

        essais = list(Essai.objects.all()[:6])
        count = 0
        for essai in essais:
            statut = random.choice(["BROUILLON", "EN_ATTENTE_VALIDATION", "VALIDE", "SIGNE"])
            RapportEssai.objects.create(
                essai=essai, statut=statut,
                date_soumission=jours_avant(random.randint(5, 20)) if statut != "BROUILLON" else None,
                date_validation=jours_avant(random.randint(1, 10)) if statut in ("VALIDE", "SIGNE") else None,
                valide_par=staff["responsable"] if statut in ("VALIDE", "SIGNE") else None,
                signe_electroniquement=statut == "SIGNE",
                date_signature=jours_avant(random.randint(1, 5)) if statut == "SIGNE" else None,
                delai_reglementaire_jours=10,
            )
            count += 1
        self.stdout.write(f"  Rapports : 4 · Rapports d'essai : {count}")

    def _seed_notifications(self, staff, clients):
        types_notif = ["INFO", "ALERTE", "STOCK", "DEMANDE", "QUALITE", "FACTURATION", "METROLOGIE", "ECHANTILLON", "ESSAI"]
        priorites = ["BASSE", "NORMALE", "HAUTE", "URGENTE"]
        destinataires = list(staff.values()) + clients
        count = 0
        for _ in range(15):
            Notification.objects.create(
                user=random.choice(destinataires), titre="Notification portail laboratoire",
                message="Mise à jour concernant votre dossier ou une alerte du système.",
                type_notification=random.choice(types_notif), priorite=random.choice(priorites),
                lu=random.random() > 0.5,
            )
            count += 1
        self.stdout.write(f"  Notifications : {count}")

    def _seed_landing(self):
        for title, category in [
            ("LANEMA obtient l'accréditation COFRAC pour ses essais microbiologiques", "COMMUNIQUE"),
            ("Nouvelle réforme du cadre réglementaire de la métrologie légale", "REFORME"),
            ("Journée portes ouvertes du laboratoire national", "EVENEMENT"),
            ("Partenariat avec l'Université Félix Houphouët-Boigny", "PARTENARIAT"),
        ]:
            NewsArticle.objects.get_or_create(
                title=title, defaults=dict(
                    excerpt=title, content=f"{title}. Plus de détails à venir.",
                    category=category, is_featured=random.random() > 0.5,
                ),
            )
        for category, question, answer in [
            ("Devis", "Comment obtenir un devis pour une analyse ?", "Créez un compte client et déposez votre demande depuis l'espace client."),
            ("Devis", "Quel est le délai de réponse pour un devis ?", "Le devis est généré instantanément après validation de votre demande."),
            ("Paiement", "Quels sont les moyens de paiement acceptés ?", "Chèque ou paiement comptant, à valider par nos équipes."),
            ("Résultats", "Comment consulter mes résultats d'analyse ?", "Les résultats sont disponibles dans votre espace client une fois l'analyse terminée."),
            ("Échantillons", "Comment dois-je conditionner mes échantillons ?", "Suivez les instructions fournies avec votre bon de commande."),
            ("Métrologie", "Proposez-vous l'étalonnage d'instruments de mesure ?", "Oui, notre laboratoire de métrologie assure l'étalonnage de nombreux instruments."),
        ]:
            FAQ.objects.get_or_create(question=question, defaults=dict(category=category, answer=answer, is_active=True))
        for keyword, response in [
            ("devis, tarif, prix", "Pour obtenir un devis, créez un compte client sur notre portail et déposez votre demande."),
            ("délai, temps, durée", "Les délais varient selon le type d'analyse ; consultez votre espace client pour le suivi en temps réel."),
            ("échantillon, prélèvement", "Les instructions de prélèvement sont fournies après acceptation de votre devis."),
            ("étalonnage, métrologie", "Notre laboratoire de métrologie assure l'étalonnage de nombreux instruments de mesure."),
            ("default", "Merci de votre message, un conseiller LANEMA reviendra vers vous rapidement."),
        ]:
            AIKeywordResponse.objects.get_or_create(keyword=keyword, defaults={"response": response, "is_active": True})
        for name, email, subject in [
            ("Konan Assi", "konan.assi@example.com", "Demande d'information sur les analyses d'eau"),
            ("Diarra Fanta", "diarra.fanta@example.com", "Question sur les délais d'étalonnage"),
            ("Boni Serge", "boni.serge@example.com", "Demande de partenariat"),
        ]:
            ContactMessage.objects.create(name=name, email=email, phone="+225 07 00 00 00", subject=subject, message=subject, is_read=random.random() > 0.5)
        self.stdout.write("  Vitrine du site (actualités, FAQ, réponses IA, messages de contact) alimentée")

    def _seed_reclamations(self, clients):
        statuts = ["OUVERTE", "TRAITEE"]
        count = 0
        for client in clients:
            for _ in range(random.randint(0, 2)):
                statut = random.choice(statuts)
                ReclamationClient.objects.create(
                    client=client, description="Réclamation relative à un délai ou une prestation du laboratoire.",
                    date_traitement=jours_avant(random.randint(1, 15)) if statut == "TRAITEE" else None,
                    statut=statut, note_satisfaction=random.randint(2, 5) if statut == "TRAITEE" and random.random() > 0.4 else None,
                )
                count += 1
        self.stdout.write(f"  Réclamations clients : {count}")
