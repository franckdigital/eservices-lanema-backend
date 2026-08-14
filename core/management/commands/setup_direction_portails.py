"""
Management command: setup_direction_portails
Crée (de façon idempotente) les Direction "techniques" DAE, DMCT, DFIR ainsi
que les services rattachés à la Direction Générale (Communication, Patrimoine,
Qualité, Juridique), distincts de l'organigramme administratif de
seed_lanema.py, pour permettre la fusion de comptes : un compte e-diligence
existant est rattaché à l'une de ces entrées (UserProfile.direction) via
l'écran Utilisateurs existant, ce qui lui donne accès au portail (KPI +
gestion) correspondant.

Usage:
    python manage.py setup_direction_portails
"""
from django.core.management.base import BaseCommand

from core.models import Direction, Service, SousDirection

# nom persisté en base → code stable utilisé par le frontend (cf.
# core/direction_access.py DIRECTION_CODE_MAP, qui doit rester synchronisé
# avec cette liste).
DIRECTION_PORTAILS = [
    {
        'nom': "Direction de l'Aéronautique",
        'description': "Portail DAE : maintenance, atelier, qualité, sécurité (ANAC), stock, financiers.",
    },
    {
        'nom': "Direction de la Métrologie et des Contrôles Techniques",
        'description': "Portail DMCT : demandes, instruments, prestations, qualité, financiers.",
    },
    {
        'nom': "Direction de la Formation, de l'Innovation et de la Recherche",
        'description': "Portail DFIR : formations, recherche, innovation, financiers.",
    },
    {
        'nom': "DG — Communication et Marketing",
        'description': "Service rattaché à la DG : actions de communication/marketing, prospects, partenariats.",
    },
    {
        'nom': "DG — Patrimoine",
        'description': "Service rattaché à la DG : biens, mouvements, maintenances, inventaires.",
    },
    {
        'nom': "DG — Qualité",
        'description': "Service rattaché à la DG : non-conformités, actions, audits, réclamations, revues de direction.",
    },
    {
        'nom': "DG — Juridique",
        'description': "Service rattaché à la DG : dossiers, contrats, contentieux, avis, procédures disciplinaires.",
    },
    {
        'nom': "DG — Information et Documentation",
        'description': "Service rattaché à la DG : GED et archivage électronique central (catégories, rétention, corbeille, partage, destruction).",
    },
]

# Sous-Direction + Services internes de chaque service rattaché à la DG, pour
# la hiérarchie de visibilité (Directeur > Sous-Directeur > Chef de service /
# Agent) : un compte est rattaché à un Service précis (UserProfile.service),
# ce qui détermine ce qu'il voit dans son palier — cf. core/direction_access.py.
# Seul Communication est scindé en 2 (Communication / Marketing), fidèle au
# cahier des charges ; les 3 autres n'ont qu'un service unique.
DG_SOUS_SERVICES = {
    "DG — Communication et Marketing": {
        'sous_direction': "Communication et Marketing",
        'services': ["Communication", "Marketing"],
    },
    "DG — Patrimoine": {
        'sous_direction': "Patrimoine",
        'services': ["Patrimoine"],
    },
    "DG — Qualité": {
        'sous_direction': "Qualité",
        'services': ["Qualité"],
    },
    "DG — Juridique": {
        'sous_direction': "Juridique",
        'services': ["Juridique"],
    },
    "DG — Information et Documentation": {
        'sous_direction': "Information et Documentation",
        'services': ["Information et Documentation"],
    },
}


class Command(BaseCommand):
    help = (
        "Crée les Direction DAE / DMCT / DFIR et les services rattachés à la DG "
        "(avec leur Sous-Direction et Services internes) utilisés par les "
        "portails de direction (fusion de comptes)."
    )

    def handle(self, *args, **options):
        for entry in DIRECTION_PORTAILS:
            direction, created = Direction.objects.get_or_create(
                nom=entry['nom'],
                defaults={'type_direction': 'direction', 'description': entry['description']},
            )
            action = 'créée' if created else 'déjà existante'
            self.stdout.write(f"  [{action}] {direction.nom} (id={direction.id})")

            spec = DG_SOUS_SERVICES.get(entry['nom'])
            if not spec:
                continue

            sous_direction, sd_created = SousDirection.objects.get_or_create(
                nom=spec['sous_direction'], direction=direction,
            )
            sd_action = 'créée' if sd_created else 'déjà existante'
            self.stdout.write(f"    [{sd_action}] Sous-direction {sous_direction.nom} (id={sous_direction.id})")

            for service_nom in spec['services']:
                service, s_created = Service.objects.get_or_create(
                    nom=service_nom, sous_direction=sous_direction,
                )
                s_action = 'créé' if s_created else 'déjà existant'
                self.stdout.write(f"      [{s_action}] Service {service.nom} (id={service.id})")

        self.stdout.write(self.style.SUCCESS(
            "Directions, sous-directions et services DG prêts. "
            "Rattachez les comptes existants depuis l'écran Utilisateurs "
            "(champs Direction + Service)."
        ))
