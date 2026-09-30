"""
Calcule et met en cache FicheAgent.face_encoding pour toutes les fiches ayant
une photo de référence mais pas encore d'encodage — nécessaire une fois après
le déploiement de l'identification 1:N (les photos existantes avant ce
déploiement n'ont pas encore été encodées).

Usage : python manage.py backfill_face_encodings
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Calcule FicheAgent.face_encoding pour les fiches avec photo mais sans encodage en cache."

    def handle(self, *args, **options):
        from core.models import FicheAgent
        from core.views import sync_face_encoding

        qs = (FicheAgent.objects.exclude(photo='').exclude(photo__isnull=True)
              .filter(face_encoding__isnull=True))
        total = qs.count()
        self.stdout.write(f"{total} fiche(s) à encoder…")

        ok, echecs = 0, 0
        for fiche in qs.iterator():
            sync_face_encoding(fiche)
            fiche.refresh_from_db(fields=['face_encoding'])
            if fiche.face_encoding:
                ok += 1
            else:
                echecs += 1
                self.stdout.write(self.style.WARNING(
                    f"  - #{fiche.id} {fiche.matricule} {fiche.nom} {fiche.prenoms} : photo inexploitable"
                ))

        self.stdout.write(self.style.SUCCESS(f"\n{ok} encodé(s), {echecs} en échec (photo à remplacer)."))
