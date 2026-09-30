"""
Audite les photos de référence RH (FicheAgent.photo) utilisées par la
comparaison faciale du pointage assisté : signale celles qui feraient
échouer la comparaison (illisible, aucun visage détecté, plusieurs visages).

Important après le passage en politique "fail closed" (ProxyPresenceView) :
tant qu'une fiche agent a une photo de référence problématique, le pointage
assisté de CET agent sera désormais bloqué (avant, il passait sans
vérification — c'était la faille). Cette commande permet de corriger les
photos en amont plutôt que de découvrir le blocage en salle d'accueil.

Usage :
    python manage.py check_reference_photos
    python manage.py check_reference_photos --fix-missing   # liste aussi les fiches sans AUCUNE photo
"""
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Vérifie que les photos de référence RH sont exploitables par la comparaison faciale."

    def add_arguments(self, parser):
        parser.add_argument('--fix-missing', action='store_true',
                             help="Liste aussi les fiches agent sans aucune photo de référence.")

    def handle(self, *args, **options):
        try:
            import face_recognition  # noqa: F401
        except ImportError:
            raise CommandError(
                "Le module 'face_recognition' n'est pas installé dans cet environnement — "
                "c'est probablement la cause de la faille (comparaison jamais effectuée, "
                "pointage toujours accepté). Installez-le : pip install face_recognition "
                "(nécessite cmake + build-essential + dlib, voir requirements.txt)."
            )

        from core.models import FicheAgent
        from core.face_match import compare_faces

        qs = FicheAgent.objects.exclude(photo='').exclude(photo__isnull=True)
        total = qs.count()
        self.stdout.write(f"Vérification de {total} photo(s) de référence…\n")

        problemes = []
        for fiche in qs.iterator():
            try:
                fiche.photo.open('rb')
                image = face_recognition.load_image_file(fiche.photo)
                encodings = face_recognition.face_encodings(image)
            except Exception as e:
                problemes.append((fiche, f"illisible : {e}"))
                continue
            finally:
                try:
                    fiche.photo.close()
                except Exception:
                    pass
            if not encodings:
                problemes.append((fiche, "aucun visage détecté"))
            elif len(encodings) > 1:
                problemes.append((fiche, f"{len(encodings)} visages détectés (photo de groupe ?)"))

        if problemes:
            self.stdout.write(self.style.WARNING(
                f"\n{len(problemes)} photo(s) de référence à corriger (pointage assisté BLOQUÉ pour ces agents) :"
            ))
            for fiche, raison in problemes:
                self.stdout.write(f"  - #{fiche.id} {fiche.matricule} {fiche.nom} {fiche.prenoms} — {raison}")
        else:
            self.stdout.write(self.style.SUCCESS("Toutes les photos de référence existantes sont exploitables."))

        if options['fix_missing']:
            sans_photo = FicheAgent.objects.filter(photo='') | FicheAgent.objects.filter(photo__isnull=True)
            n = sans_photo.count()
            self.stdout.write(f"\n{n} fiche(s) agent sans AUCUNE photo de référence "
                              "(pointage assisté accepté sans vérification faciale pour eux) :")
            for fiche in sans_photo.iterator():
                self.stdout.write(f"  - #{fiche.id} {fiche.matricule} {fiche.nom} {fiche.prenoms}")
