"""
Management command: seed_sous_traitants

Cree (de facon idempotente) le catalogue de demonstration des sous-traitants
partenaires officiels LANEMA, affiches sur le formulaire public de demande de
devis lorsque le client coche "Accord de sous-traitance". Cree egalement un
creneau de disponibilite par defaut (delai de realisation annonce) si aucun
n'existe encore.

Usage:
    python manage.py seed_sous_traitants
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from demandes.models import CreneauDisponibilite, SousTraitantPartenaire

PARTENAIRES = [
    {"nom": "AFRILAB Métrologie", "specialite": "Étalonnage de masse et de pression", "contact": "contact@afrilab-ci.com"},
    {"nom": "CI-CALIB", "specialite": "Étalonnage électrique et température", "contact": "contact@ci-calib.ci"},
    {"nom": "BioTest Laboratoires", "specialite": "Microbiologie et parasitologie", "contact": "contact@biotest-ci.com"},
    {"nom": "ChimAfrique Analyses", "specialite": "Chimie alimentaire et industrielle", "contact": "contact@chimafrique.ci"},
    {"nom": "AeroTech Services CI", "specialite": "Maintenance et contrôle aéronautique", "contact": "contact@aerotech-ci.com"},
]


class Command(BaseCommand):
    help = "Cree le catalogue de demonstration des sous-traitants partenaires LANEMA et un creneau de delai par defaut."

    def handle(self, *args, **options):
        for entry in PARTENAIRES:
            obj, created = SousTraitantPartenaire.objects.get_or_create(
                nom=entry["nom"],
                defaults={
                    "specialite": entry["specialite"],
                    "contact": entry["contact"],
                    "type_sous_traitant": "PARTENAIRE",
                    "actif": True,
                },
            )
            action = "cree" if created else "deja existant"
            self.stdout.write(f"  [{action}] {obj.nom}")

        if not CreneauDisponibilite.objects.filter(actif=True).exists():
            today = timezone.now().date()
            creneau = CreneauDisponibilite.objects.create(
                date_debut=today,
                date_fin=today + timedelta(days=180),
                delai_jours_ouvres=10,
                label="Délai standard",
                actif=True,
            )
            self.stdout.write(f"  [cree] Créneau de disponibilité par défaut : {creneau}")
        else:
            self.stdout.write("  [deja existant] Un créneau de disponibilité actif existe déjà")

        self.stdout.write(self.style.SUCCESS(
            "\nSous-traitants partenaires prets. "
            "Gerez le catalogue et les creneaux depuis le portail staff (/app/reception)."
        ))
