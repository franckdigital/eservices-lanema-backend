"""
Alimente le module Stock avec un historique de traçabilité et des inventaires
réalistes, en s'appuyant sur les articles/lots déjà présents en base.

Comble les manques observés sur l'environnement de test :
  • Mouvements de stock quasi inexistants (aucune entrée tracée, sorties
    partiellement reconstituées) → le module Traçabilité était vide.
  • Aucun inventaire → le module Inventaire était vide.
  • Article CONS-003 (Papier Filtre Whatman) à 0 de stock sans lot ni
    mouvement l'expliquant.

Idempotent : peut être relancé sans dupliquer les données (get_or_create
partout, numéros de pièces explicites).
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone


def backdate(model_cls, pk, **fields):
    """Force la valeur de champs `auto_now_add` en contournant .save()."""
    model_cls.objects.filter(pk=pk).update(**fields)


class Command(BaseCommand):
    help = "Alimente le stock : traçabilité (mouvements) et inventaires de démonstration"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== SEED STOCK : TRAÇABILITÉ & INVENTAIRE ===\n"))
        self.now = timezone.now()

        users = self._get_users()
        articles = self._get_articles()
        lots = self._seed_lots(articles)
        self._seed_mouvements_entree(lots)
        self._seed_sorties_manquantes(lots, users)
        self._seed_transfert_mouvement(users)
        self._seed_quarantaine_mouvements(users)
        self._seed_inventaires(lots, users)
        self._print_summary()

    # ------------------------------------------------------------------
    def _get_users(self):
        from django.contrib.auth.models import User

        users = {u.username: u for u in User.objects.filter(
            username__in=["admin_lanema", "sophie.manager", "jean.tech", "marie.tech"]
        )}
        missing = {"admin_lanema", "sophie.manager", "jean.tech", "marie.tech"} - set(users)
        if missing:
            self.stdout.write(self.style.ERROR(
                f"Utilisateurs manquants : {missing}. Lancez d'abord les seeds clients."
            ))
            raise SystemExit(1)
        self.stdout.write(self.style.MIGRATE_LABEL("Utilisateurs OK"))
        return users

    def _get_articles(self):
        from stock.models import Article

        refs = ["REAG-001", "REAG-002", "REAG-003", "CONS-001", "CONS-002", "CONS-003", "EQUIP-001", "EQUIP-002"]
        articles = {a.reference_interne: a for a in Article.objects.filter(reference_interne__in=refs)}
        missing = set(refs) - set(articles)
        if missing:
            self.stdout.write(self.style.ERROR(
                f"Articles manquants : {missing}. Lancez d'abord populate_stock_simple."
            ))
            raise SystemExit(1)
        self.stdout.write(self.style.MIGRATE_LABEL("Articles OK"))
        return articles

    # ------------------------------------------------------------------
    # LOTS
    # ------------------------------------------------------------------
    def _seed_lots(self, articles):
        from stock.models import Lot, Emplacement

        self.stdout.write(self.style.MIGRATE_LABEL("1. Lots"))

        lots = {l.numero_lot: l for l in Lot.objects.select_related("article").all()}

        # Papier Filtre Whatman N°1 : lot totalement consommé, explique le
        # stock à 0 déjà affiché dans l'écran Articles.
        cons003 = articles["CONS-003"]
        emplacement = cons003.emplacement or Emplacement.objects.filter(code="B-02-01").first()
        lot, created = Lot.objects.get_or_create(
            article=cons003,
            numero_lot="LOT-PAPF-2026-001",
            defaults={
                "quantite_attendue": 30,
                "quantite_initiale": 30,
                "quantite_restante": 0,
                "unite": cons003.unite_mesure,
                "date_peremption": (self.now + timedelta(days=365)).date(),
                "ouvert": True,
                "emplacement": emplacement,
            },
        )
        label = "Créé" if created else "Existant"
        self.stdout.write(f"   [{label}] {lot.numero_lot} ({cons003.designation}) — épuisé")
        lots[lot.numero_lot] = lot

        return lots

    # ------------------------------------------------------------------
    # MOUVEMENTS - ENTRÉES (reconstitue la traçabilité de réception)
    # ------------------------------------------------------------------
    def _seed_mouvements_entree(self, lots):
        from stock.models import MouvementStock

        self.stdout.write(self.style.MIGRATE_LABEL("2. Mouvements — Entrées"))

        # (numero_lot, offset_jours)
        plan = [
            ("LOT-ACID-2026-001", -42),
            ("LOT-HYDR-2026-001", -41),
            ("LOT-GANT-2026-001", -35),
            ("LOT-PIP-2026-001", -35),
            ("LOT-BEC-2026-001", -30),
            ("LOT-ERL-2026-001", -30),
            ("LOT-GANT-2025-099", -300),
            ("LOT-HCL-2026-001", -27),
            ("LOT-PAPF-2026-001", -33),
        ]
        count = 0
        for numero_lot, offset in plan:
            lot = lots.get(numero_lot)
            if not lot:
                continue
            if MouvementStock.objects.filter(lot=lot, type_mouvement="ENTREE").exists():
                continue
            mvt = MouvementStock.objects.create(
                article=lot.article,
                lot=lot,
                type_mouvement="ENTREE",
                quantite=lot.quantite_initiale,
                quantite_avant=0,
                quantite_apres=lot.quantite_initiale,
                reference_document=lot.numero_lot,
                description=f"Réception initiale du lot {lot.numero_lot}",
            )
            backdate(MouvementStock, mvt.pk, date_mouvement=self.now + timedelta(days=offset))
            count += 1
        self.stdout.write(f"   {count} mouvement(s) d'entrée créé(s)")

    # ------------------------------------------------------------------
    # MOUVEMENTS - SORTIES manquantes (réconcilie initiale vs restante)
    # ------------------------------------------------------------------
    def _seed_sorties_manquantes(self, lots, users):
        from stock.models import SortieStock, MouvementStock

        self.stdout.write(self.style.MIGRATE_LABEL("3. Mouvements — Sorties"))
        jean = users["jean.tech"]

        # (numero_sortie, numero_lot, quantite, offset_jours, motif)
        plan = [
            ("SOR-2026-00002", "LOT-GANT-2025-099", 8, -15,
             "Consommation courante — gants nitrile salle d'analyses"),
            ("SOR-2026-00003", "LOT-PAPF-2026-001", 15, -20,
             "Filtration séries d'analyses eau industrielle"),
            ("SOR-2026-00004", "LOT-PAPF-2026-001", 15, -4,
             "Filtration séries d'analyses eau industrielle — solde du lot"),
        ]

        for numero_sortie, numero_lot, quantite, offset, motif in plan:
            lot = lots.get(numero_lot)
            if not lot:
                continue
            if SortieStock.objects.filter(numero_sortie=numero_sortie).exists():
                continue
            if MouvementStock.objects.filter(reference_document=numero_sortie).exists():
                continue

            quantite_avant = MouvementStock.objects.filter(lot=lot).order_by(
                "-date_mouvement"
            ).values_list("quantite_apres", flat=True).first()
            if quantite_avant is None:
                quantite_avant = lot.quantite_initiale
            quantite_apres = quantite_avant - quantite

            sortie = SortieStock.objects.create(
                numero_sortie=numero_sortie,
                lot=lot,
                quantite=quantite,
                type_sortie="CONSOMMATION",
                motif=motif,
                utilisateur=jean,
                valide=True,
            )
            backdate(
                SortieStock, sortie.pk,
                date_sortie=self.now + timedelta(days=offset),
                date_validation=self.now + timedelta(days=offset),
            )

            mvt = MouvementStock.objects.create(
                article=lot.article,
                lot=lot,
                type_mouvement="SORTIE",
                quantite=quantite,
                quantite_avant=quantite_avant,
                quantite_apres=quantite_apres,
                reference_document=numero_sortie,
                description=f"Sortie de stock: Consommation laboratoire - {motif}",
                sortie=sortie,
                utilisateur=jean,
            )
            backdate(MouvementStock, mvt.pk, date_mouvement=self.now + timedelta(days=offset))
            self.stdout.write(f"   [Créé] {numero_sortie} — {lot.numero_lot} (-{quantite})")

    # ------------------------------------------------------------------
    # MOUVEMENT - TRANSFERT (relie le transfert existant à la traçabilité)
    # ------------------------------------------------------------------
    def _seed_transfert_mouvement(self, users):
        from stock.models import TransfertInterne, MouvementStock

        self.stdout.write(self.style.MIGRATE_LABEL("4. Mouvements — Transferts"))
        jean = users["jean.tech"]

        transferts = TransfertInterne.objects.filter(execute=True).select_related(
            "lot", "lot__article", "emplacement_source", "emplacement_destination"
        )
        count = 0
        for transfert in transferts:
            if MouvementStock.objects.filter(transfert=transfert).exists():
                continue
            lot = transfert.lot
            mvt = MouvementStock.objects.create(
                article=lot.article,
                lot=lot,
                type_mouvement="TRANSFERT",
                quantite=transfert.quantite,
                quantite_avant=lot.quantite_restante,
                quantite_apres=lot.quantite_restante,
                reference_document=f"TRF-{transfert.pk}",
                description=(
                    f"Transfert {transfert.emplacement_source} -> "
                    f"{transfert.emplacement_destination}"
                ),
                transfert=transfert,
                utilisateur=jean,
            )
            backdate(MouvementStock, mvt.pk, date_mouvement=self.now - timedelta(days=18))
            count += 1
        self.stdout.write(f"   {count} mouvement(s) de transfert créé(s)")

    # ------------------------------------------------------------------
    # MOUVEMENTS - QUARANTAINE (relie les quarantaines existantes)
    # ------------------------------------------------------------------
    def _seed_quarantaine_mouvements(self, users):
        from stock.models import Quarantaine, MouvementStock

        self.stdout.write(self.style.MIGRATE_LABEL("5. Mouvements — Quarantaines"))
        marie = users["marie.tech"]

        count = 0
        for quarantaine in Quarantaine.objects.select_related("lot", "lot__article").all():
            lot = quarantaine.lot
            ref = f"QUAR-{quarantaine.pk}"
            if MouvementStock.objects.filter(reference_document=ref).exists():
                continue
            mvt = MouvementStock.objects.create(
                article=lot.article,
                lot=lot,
                type_mouvement="QUARANTAINE_ENTREE",
                quantite=lot.quantite_restante,
                quantite_avant=lot.quantite_restante,
                quantite_apres=lot.quantite_restante,
                reference_document=ref,
                description=f"Mise en quarantaine: {quarantaine.motif[:200]}",
                utilisateur=marie,
            )
            backdate(MouvementStock, mvt.pk, date_mouvement=quarantaine.date_mise_en_quarantaine)
            count += 1
        self.stdout.write(f"   {count} mouvement(s) de quarantaine créé(s)")

    # ------------------------------------------------------------------
    # INVENTAIRES
    # ------------------------------------------------------------------
    def _seed_inventaires(self, lots, users):
        from stock.models import Inventaire, LigneInventaire, Entrepot, Lot

        self.stdout.write(self.style.MIGRATE_LABEL("6. Inventaires"))
        entrepot = Entrepot.objects.filter(code="ENT-001").first()
        sophie = users["sophie.manager"]
        jean = users["jean.tech"]

        # --- Inventaire A : COMPLET, TERMINE (comptage fait, écarts en attente de validation) ---
        inv_a, created = Inventaire.objects.get_or_create(
            numero_inventaire="INV-2026-00001",
            defaults={
                "type_inventaire": "COMPLET",
                "statut": "TERMINE",
                "entrepot": entrepot,
                "date_debut": self.now - timedelta(days=10),
                "date_fin": self.now - timedelta(days=9),
                "responsable": sophie,
                "observations": "Inventaire complet trimestriel — écarts constatés en attente de validation.",
            },
        )
        label = "Créé" if created else "Existant"
        self.stdout.write(f"   [{label}] {inv_a.numero_inventaire} — {inv_a.statut}")

        # écarts volontaires pour illustrer le mécanisme : (numero_lot, quantite_comptee)
        comptages_a = {
            "LOT-ACID-2026-001": 40,
            "LOT-HYDR-2026-001": 30,
            "LOT-GANT-2026-001": 98,   # écart -2
            "LOT-PIP-2026-001": 50,
            "LOT-BEC-2026-001": 25,    # écart +1
            "LOT-ERL-2026-001": 12,
            "LOT-GANT-2025-099": 12,
            "LOT-HCL-2026-001": 20,
        }
        self._seed_lignes_inventaire(
            inv_a, lots, comptages_a, jean, self.now - timedelta(days=9)
        )

        # --- Inventaire B : PARTIEL (réactifs), EN_COURS (comptage à moitié fait) ---
        inv_b, created = Inventaire.objects.get_or_create(
            numero_inventaire="INV-2026-00002",
            defaults={
                "type_inventaire": "PARTIEL",
                "statut": "EN_COURS",
                "entrepot": entrepot,
                "date_debut": self.now - timedelta(days=2),
                "responsable": jean,
                "observations": "Inventaire tournant — zone Réactifs Chimiques.",
            },
        )
        label = "Créé" if created else "Existant"
        self.stdout.write(f"   [{label}] {inv_b.numero_inventaire} — {inv_b.statut}")

        # Une seule ligne comptée sur les deux, pour illustrer la progression partielle
        comptages_b = {"LOT-ACID-2026-001": 40}
        self._seed_lignes_inventaire(
            inv_b, {"LOT-ACID-2026-001": lots["LOT-ACID-2026-001"],
                    "LOT-HYDR-2026-001": lots["LOT-HYDR-2026-001"]},
            comptages_b, jean, self.now - timedelta(days=1),
        )

        # --- Inventaire C : ANNUEL, PLANIFIE (pas encore démarré) ---
        inv_c, created = Inventaire.objects.get_or_create(
            numero_inventaire="INV-2026-00003",
            defaults={
                "type_inventaire": "ANNUEL",
                "statut": "PLANIFIE",
                "entrepot": entrepot,
                "date_debut": self.now + timedelta(days=5),
                "responsable": sophie,
                "observations": "Inventaire annuel — à démarrer.",
            },
        )
        label = "Créé" if created else "Existant"
        self.stdout.write(f"   [{label}] {inv_c.numero_inventaire} — {inv_c.statut}")
        self._seed_lignes_inventaire(inv_c, lots, {}, jean, None)

    def _seed_lignes_inventaire(self, inventaire, lots_subset, comptages, compte_par, date_comptage):
        from stock.models import LigneInventaire

        for numero_lot, lot in lots_subset.items():
            if lot.quantite_restante <= 0:
                continue
            ligne, created = LigneInventaire.objects.get_or_create(
                inventaire=inventaire,
                lot=lot,
                defaults={
                    "article": lot.article,
                    "emplacement": lot.emplacement,
                    "quantite_theorique": lot.quantite_restante,
                },
            )
            if numero_lot in comptages and ligne.quantite_comptee is None:
                ligne.quantite_comptee = comptages[numero_lot]
                ligne.compte_par = compte_par
                ligne.date_comptage = date_comptage
                ligne.save()

    # ------------------------------------------------------------------
    def _print_summary(self):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== RÉSUMÉ SEED STOCK ==="))
        self.stdout.write("Traçabilité : entrées, sorties, transfert et quarantaines reliés aux mouvements.")
        self.stdout.write("Inventaires  : INV-2026-00001 (TERMINE, écarts) | "
                           "INV-2026-00002 (EN_COURS, partiel) | INV-2026-00003 (PLANIFIE).")
        self.stdout.write(self.style.SUCCESS("\nSeed stock terminé avec succès !"))
        self.stdout.write("Relancer : python manage.py seed_stock_demo (idempotent)\n")
