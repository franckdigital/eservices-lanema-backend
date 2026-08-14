"""
Importe les donnees historiques de l'ancienne base MySQL 'labo' (projet
laboratoire-backend d'origine) dans ce projet, apres la reorganisation des
modules laboratoire en apps de ce depot.

Ne modifie JAMAIS la base source : toutes les lectures se font via la
connexion secondaire en lecture seule 'labo_legacy' (voir ediligence/settings.py,
activee uniquement si LABO_LEGACY_DB_NAME est definie dans l'environnement).

Usage :
    python manage.py import_laboratoire_data --dry-run   # verifie le mapping, n'ecrit rien
    python manage.py import_laboratoire_data              # importe reellement

Pourquoi une commande dediee plutot qu'un simple dump/restore SQL :
- La table clients_user (ancien AUTH_USER_MODEL du labo) n'existe plus telle
  quelle : ses comptes doivent devenir des lignes auth_user + clients_clientprofile.
  Les ids clients_user.id ne peuvent pas etre reutilises tels quels dans
  auth_user (qui contient deja les comptes ediligence existants) : on construit
  une table de correspondance ancien_id -> nouvel_id et on l'applique a toutes
  les colonnes qui referencaient un utilisateur (client_id, fournisseur_id,
  utilisateur_id, responsable_id, ...).
- Les autres tables (stock_*, demandes_*, qualite_*, facturation_*, metrologie_*,
  notifications_*, landing_*, core_activity) sont neuves dans ce projet : leurs
  ids d'origine sont preserves tels quels, seules les colonnes FK vers un
  utilisateur sont remappees.
"""
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction

from clients.models import ClientProfile


# Tables copiees telles quelles (dans l'ordre des dependances), avec la liste
# des colonnes contenant un ancien id d'utilisateur clients_user a remapper.
TABLES = [
    ("landing_news_articles", []),
    ("landing_faqs", []),
    ("landing_ai_keyword_responses", []),
    ("landing_contact_messages", []),
    ("metrologie_equipement", ["responsable_id"]),
    ("metrologie_etalonnage", []),
    ("demandes_demandedevis", ["client_id"]),
    ("qualite_typeechantillon", []),
    ("qualite_echantillon", []),
    ("qualite_essai", []),
    ("qualite_nonconformite", ["responsable_id"]),
    ("qualite_audit", []),
    ("facturation_proforma", ["client_id"]),
    ("facturation_facture", ["client_id"]),
    ("facturation_demandeanalyse", ["client_id"]),
    ("stock_entrepot", []),
    ("stock_domaine", []),
    ("stock_emplacement", []),
    ("stock_categoriearticle", []),
    ("stock_article", []),
    ("stock_lot", []),
    ("stock_alerte", ["traite_par_id"]),
    ("stock_quarantaine", ["mis_en_quarantaine_par_id", "leve_par_id"]),
    ("stock_reception", ["fournisseur_id", "receptionne_par_id", "verifie_par_id", "valide_par_id"]),
    ("stock_lignereception", []),
    ("stock_transfertinterne", []),
    ("stock_sortiestock", ["utilisateur_id", "valide_par_id"]),
    ("stock_mouvementstock", ["utilisateur_id"]),
    ("stock_inventaire", ["responsable_id"]),
    ("stock_ligneinventaire", ["compte_par_id"]),
    ("notifications_notification", ["user_id"]),
    ("core_activity", ["utilisateur_id"]),
]


class Command(BaseCommand):
    help = "Importe les donnees de l'ancienne base MySQL 'labo' dans ce projet (lecture seule sur la source)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="N'ecrit rien : affiche uniquement ce qui serait importe (comptes, tables, doublons).",
        )

    def handle(self, *args, **options):
        if "labo_legacy" not in connections.databases:
            raise CommandError(
                "Connexion 'labo_legacy' non configuree. Definissez LABO_LEGACY_DB_NAME "
                "(et eventuellement LABO_LEGACY_DB_USER/PASSWORD/HOST/PORT) dans l'environnement."
            )

        dry_run = options["dry_run"]
        mode = "DRY-RUN (aucune ecriture)" if dry_run else "IMPORT REEL"
        self.stdout.write(self.style.MIGRATE_HEADING(f"=== Import donnees laboratoire ({mode}) ===\n"))

        user_id_map = self._import_users(dry_run)

        for table, user_fk_columns in TABLES:
            self._copy_table(table, user_fk_columns, user_id_map, dry_run)

        self.stdout.write(self.style.SUCCESS("\nTermine."))
        if dry_run:
            self.stdout.write("Relancez sans --dry-run pour ecrire reellement les donnees.")

    # ------------------------------------------------------------------
    def _import_users(self, dry_run):
        """Migre clients_user -> auth_user + clients_clientprofile.

        Retourne le mapping {ancien_clients_user_id: nouvel_auth_user_id}.
        """
        src = connections["labo_legacy"].cursor()
        src.execute("SELECT * FROM clients_user")
        columns = [c[0] for c in src.description]
        rows = [dict(zip(columns, row)) for row in src.fetchall()]

        self.stdout.write(f"Comptes trouves dans clients_user : {len(rows)}")

        user_id_map = {}
        created, reused, skipped = 0, 0, 0

        with transaction.atomic():
            for row in rows:
                old_id = row["id"]
                username = row["username"]
                email = row.get("email") or ""

                existing = User.objects.filter(username=username).first()
                if existing is None and email:
                    existing = User.objects.filter(email=email).first()

                if existing is not None:
                    # Compte deja present cote ediligence (ex: meme username/email) :
                    # on reutilise son id, on ne duplique pas le compte.
                    user_id_map[old_id] = existing.id
                    reused += 1
                    continue

                if dry_run:
                    # On ne connait pas encore le futur id auto-incremente : on ne
                    # peut pas construire le mapping complet en dry-run pour les FK,
                    # mais on peut au moins compter et signaler les doublons.
                    skipped += 1
                    continue

                user = User(
                    username=username,
                    email=email,
                    first_name=row.get("first_name") or "",
                    last_name=row.get("last_name") or "",
                    is_active=bool(row.get("is_active", True)),
                    is_staff=bool(row.get("is_staff", False)),
                    is_superuser=bool(row.get("is_superuser", False)),
                    date_joined=row.get("date_joined"),
                    last_login=row.get("last_login"),
                )
                # Le hash de mot de passe Django (algo$iterations$salt$hash) est
                # directement reutilisable tel quel, peu importe le projet.
                user.password = row.get("password") or make_password(None)
                user.save()

                ClientProfile.objects.create(
                    user=user,
                    role=row.get("role") or "CLIENT",
                    type_subscription=row.get("type_subscription") or "",
                    organisation=row.get("organisation") or "",
                    raison_sociale=row.get("raison_sociale") or "",
                    adresse=row.get("adresse") or "",
                    telephone=row.get("telephone") or "",
                    siret=row.get("siret") or "",
                    contact_nom=row.get("contact_nom") or "",
                    expo_push_token=row.get("expo_push_token"),
                )
                user_id_map[old_id] = user.id
                created += 1

        self.stdout.write(
            f"  -> {created} comptes crees, {reused} comptes reutilises (deja existants), "
            f"{skipped} a creer (dry-run)."
        )
        return user_id_map

    # ------------------------------------------------------------------
    def _copy_table(self, table, user_fk_columns, user_id_map, dry_run):
        src = connections["labo_legacy"].cursor()
        try:
            src.execute(f"SELECT * FROM {table}")
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"  [{table}] ignoree : {exc}"))
            return

        columns = [c[0] for c in src.description]
        rows = src.fetchall()

        if dry_run:
            self.stdout.write(f"  [{table}] {len(rows)} lignes a copier")
            return

        placeholders = ", ".join(["%s"] * len(columns))
        columns_sql = ", ".join(f"`{c}`" for c in columns)
        insert_sql = f"INSERT INTO `{table}` ({columns_sql}) VALUES ({placeholders})"

        dst = connections["default"].cursor()
        inserted = 0
        for row in rows:
            values = list(row)
            for fk_col in user_fk_columns:
                idx = columns.index(fk_col)
                old_val = values[idx]
                if old_val is not None:
                    values[idx] = user_id_map.get(old_val, old_val)
            dst.execute(insert_sql, values)
            inserted += 1

        self.stdout.write(f"  [{table}] {inserted} lignes importees")
