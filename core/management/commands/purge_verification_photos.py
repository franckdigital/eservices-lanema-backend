"""
Supprime du disque les photos de vérification faciale déjà stockées pour les
pointages assistés (Presence.verification_photo), avant que la migration
0124_remove_presence_verification_photo ne retire la colonne.

À exécuter UNE SEULE FOIS, avant `python manage.py migrate core` :

    python manage.py purge_verification_photos
    python manage.py migrate core

Le champ étant supprimé du modèle par ce même déploiement, cette commande
doit tourner avant la migration (sinon le champ n'existe plus pour requêter
les fichiers à effacer).
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Supprime du disque les photos de vérification déjà stockées (Presence.verification_photo)."

    def handle(self, *args, **options):
        from core.models import Presence

        try:
            qs = Presence.objects.exclude(verification_photo='').exclude(verification_photo__isnull=True)
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f"Champ verification_photo introuvable (déjà migré ?) : {e}"
            ))
            return

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS("Aucune photo de vérification à supprimer."))
            return

        deleted, errors = 0, 0
        for presence in qs.iterator():
            try:
                if presence.verification_photo:
                    presence.verification_photo.delete(save=False)
                    deleted += 1
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f"  Presence #{presence.id} : {e}"))

        self.stdout.write(self.style.SUCCESS(
            f"{deleted}/{total} fichier(s) supprimé(s) du disque ({errors} erreur(s))."
        ))
