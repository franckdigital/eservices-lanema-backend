"""
Crée / met à jour la structure organisationnelle du LANEMA :
Cabinet + Direction Générale + Directions -> Sous-Directions -> Services.

Idempotent : `get_or_create` partout, relançable sans doublon.
Ne crée AUCUNE donnée de démo (pas d'agents, courriers, pointages).

Usage :
    python manage.py seed_lanema_structure
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Direction, SousDirection, Service


# type_direction : 'cabinet' | 'direction_generale' | 'direction'
LANEMA_STRUCTURE = [
    {
        'type': 'cabinet',
        'nom': "Cabinet du Ministère du Commerce, de l'Industrie et de l'Artisanat",
        'sous_directions': {
            'Sous-Direction du Cabinet': [
                'Service Protocole et Relations Publiques',
                'Service des Conseillers Techniques',
            ],
        },
    },
    {
        'type': 'direction_generale',
        'nom': 'Direction Générale du LANEMA - DG',
        'sous_directions': {
            'Sous-Direction de la Coordination Générale': [
                'Service Secrétariat de Direction Générale',
                'Service Contrôle de Gestion',
                'Service Suivi-Évaluation et Planification',
            ],
            'Sous-Direction Qualité et Audit Interne': [
                'Service Management de la Qualité',
                'Service Audit Interne',
            ],
            'Sous-Direction Juridique et Communication': [
                'Service Affaires Juridiques et Contentieux',
                'Service Communication et Relations Publiques',
            ],
        },
    },
    {
        'type': 'direction',
        'nom': 'Direction Administrative et Financière - DAAF',
        'sous_directions': {
            'Sous-Direction des Ressources Humaines': [
                'Service Gestion Administrative du Personnel',
                'Service Paie et Rémunérations',
                'Service Formation et Développement des Compétences',
            ],
            'Sous-Direction Financière et Comptable': [
                'Service Comptabilité Générale',
                'Service Budget et Engagement',
                'Service Trésorerie et Recouvrement',
            ],
            'Sous-Direction des Achats et Moyens Généraux': [
                'Service Achats et Marchés Publics',
                'Service Patrimoine et Logistique',
                'Service Courrier et Archives',
            ],
        },
    },
    {
        'type': 'direction',
        'nom': 'Direction des Essais et Analyses - DEA',
        'sous_directions': {
            'Sous-Direction des Analyses Physico-Chimiques': [
                'Service Analyses des Eaux',
                'Service Analyses des Denrées Alimentaires',
                'Service Analyses des Produits Pétroliers et Chimiques',
            ],
            'Sous-Direction des Analyses Microbiologiques': [
                'Service Microbiologie Alimentaire',
                'Service Microbiologie des Eaux et Environnement',
            ],
            'Sous-Direction des Essais sur Produits': [
                'Service Essais Physiques et Mécaniques',
                'Service Essais sur Matériaux de Construction',
                'Service Essais Électrotechniques',
            ],
            'Sous-Direction Gestion des Échantillons': [
                'Service Réception et Enregistrement',
                'Service Archivage des Échantillons',
            ],
        },
    },
    {
        'type': 'direction',
        'nom': "Direction de l'Aéronautique - DAE",
        'sous_directions': {
            'Sous-Direction Navigabilité et Certification': [
                'Service Certification des Aéronefs',
                'Service Suivi de Navigabilité',
                'Service Agréments des Ateliers de Maintenance',
            ],
            'Sous-Direction Sécurité et Sûreté Aéroportuaire': [
                'Service Inspection Aéroportuaire',
                'Service Gestion des Risques et Audits',
            ],
            'Sous-Direction Licences et Personnel Aéronautique': [
                'Service Licences et Qualifications',
                'Service Examens et Formation Aéronautique',
            ],
        },
    },
    {
        'type': 'direction',
        'nom': 'Direction de la Métrologie et des Contrôles Techniques - DMCT',
        'sous_directions': {
            'Sous-Direction de la Métrologie Légale': [
                'Service Instruments de Pesage',
                'Service Instruments de Mesurage',
                'Service Vérification et Surveillance du Marché',
            ],
            'Sous-Direction de la Métrologie Industrielle et Scientifique': [
                'Service Étalonnage Masse et Dimension',
                'Service Étalonnage Température, Pression et Débit',
                'Service Étalonnage Électricité et Temps',
            ],
            'Sous-Direction des Contrôles Techniques': [
                'Service Contrôle des Véhicules',
                'Service Contrôle des Équipements sous Pression',
                'Service Contrôle des Installations Électriques',
            ],
        },
    },
    {
        'type': 'direction',
        'nom': 'Direction Formation, Innovation et Recherche - DFIR',
        'sous_directions': {
            'Sous-Direction de la Formation': [
                'Service Ingénierie de Formation',
                'Service Organisation des Sessions',
                'Service Certification des Compétences',
            ],
            "Sous-Direction de l'Innovation et de la Recherche": [
                'Service Veille Technologique et Normative',
                'Service Projets de Recherche',
                'Service Partenariats Scientifiques',
            ],
            'Sous-Direction Assistance et Conseil aux Entreprises': [
                'Service Assistance Technique',
                'Service Documentation et Information Technique',
            ],
        },
    },
    {
        'type': 'direction',
        'nom': "Direction des Systèmes d'Information - DSI",
        'sous_directions': {
            'Sous-Direction Infrastructures et Réseaux': [
                'Service Réseaux et Télécommunications',
                'Service Systèmes et Serveurs',
                "Service Sécurité des Systèmes d'Information",
            ],
            'Sous-Direction Études et Développement': [
                'Service Développement Applicatif',
                'Service Gestion de Projets SI',
                'Service Qualité et Recette Logicielle',
            ],
            'Sous-Direction Support et Assistance': [
                'Service Support aux Utilisateurs',
                'Service Gestion du Parc Informatique',
            ],
        },
    },
]


class Command(BaseCommand):
    help = "Crée/actualise la structure organisationnelle du LANEMA (sans données de démo)."

    @transaction.atomic
    def handle(self, *args, **options):
        n_dir = n_sd = n_svc = 0

        for bloc in LANEMA_STRUCTURE:
            direction, created = Direction.objects.get_or_create(
                nom=bloc['nom'],
                defaults={'type_direction': bloc['type']},
            )
            # corrige le type si la direction existait déjà mal typée
            if direction.type_direction != bloc['type']:
                direction.type_direction = bloc['type']
                direction.save(update_fields=['type_direction', 'updated_at'])
            n_dir += 1
            self.stdout.write(f"[{direction.type_direction}] {direction.nom}")

            for sd_nom, services in bloc['sous_directions'].items():
                sous_dir, _ = SousDirection.objects.get_or_create(
                    nom=sd_nom, direction=direction,
                )
                n_sd += 1
                self.stdout.write(f"    └─ {sous_dir.nom}")

                for svc_nom in services:
                    Service.objects.get_or_create(
                        nom=svc_nom, sous_direction=sous_dir,
                        defaults={'direction': direction},
                    )
                    n_svc += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nOK — {n_dir} directions, {n_sd} sous-directions, {n_svc} services "
            f"(total base : {Direction.objects.count()} / {SousDirection.objects.count()} / {Service.objects.count()})."
        ))
