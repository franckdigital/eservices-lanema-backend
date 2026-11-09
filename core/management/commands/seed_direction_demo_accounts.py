"""
Management command: seed_direction_demo_accounts

Cree (de facon idempotente) un compte de demonstration par portail de
direction/service concerne par le cloisonnement d'acces mis en place cote
frontend (DirectionRoute, cf. core/direction_access.py) :

- DMCT (Metrologie et Controles Techniques)      -> /kpi-dmct/*, /dmct/*
- DAE  (Aeronautique)                             -> /kpi-aero/*, /dae/*
- DEAL (Essais et Analyses de Laboratoire / "DEA") -> /kpi-dea/* + portail
  labo /app (fusion de comptes automatique, cf. core/views.py UserProfileView)
- Service Reception (portail labo /app uniquement, role clients.RECEPTION)
  -> /app/reception, /app/echantillons, etc. (cf. clients/permissions_catalog.py)

Chaque compte recoit le role 'DIRECTEUR' (acces complet a son portail de
direction, cf. ROLE_TIERS) pour DMCT/DAE/DEAL, et le role labo dedie
'RECEPTION' pour le service reception.

Usage:
    python manage.py seed_direction_demo_accounts
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from clients.models import ClientProfile
from core.models import Direction, UserProfile

DEFAULT_PASSWORD = 'Lanema2024!'

# nom persiste en base -> doit rester synchronise avec
# core/direction_access.py DIRECTION_CODE_MAP.
DIRECTIONS = {
    'DMCT': "Direction de la Métrologie et des Contrôles Techniques",
    'DAE': "Direction de l'Aéronautique",
    'DEAL': "Direction des Essais et Analyses de Laboratoire",
}


class Command(BaseCommand):
    help = "Cree un compte de demonstration par portail de direction (DMCT, DAE, DEAL) et pour le Service Reception."

    def handle(self, *args, **options):
        dmct_dir, _ = Direction.objects.get_or_create(
            nom=DIRECTIONS['DMCT'], defaults={'type_direction': 'direction'}
        )
        dae_dir, _ = Direction.objects.get_or_create(
            nom=DIRECTIONS['DAE'], defaults={'type_direction': 'direction'}
        )
        deal_dir, _ = Direction.objects.get_or_create(
            nom=DIRECTIONS['DEAL'], defaults={'type_direction': 'direction'}
        )

        self._create_direction_account(
            username='dmct.demo', email='dmct.demo@lanema.ci',
            first_name='Compte', last_name='DMCT', direction=dmct_dir,
        )
        self._create_direction_account(
            username='dae.demo', email='dae.demo@lanema.ci',
            first_name='Compte', last_name='DAE', direction=dae_dir,
        )
        self._create_direction_account(
            username='dea.demo', email='dea.demo@lanema.ci',
            first_name='Compte', last_name='DEA', direction=deal_dir,
            bridge_labo=True,
        )
        self._create_reception_account()

        self.stdout.write(self.style.SUCCESS(
            "\nComptes de demonstration prets (mot de passe commun : "
            f"{DEFAULT_PASSWORD}) :\n"
            "  - dmct.demo@lanema.ci      -> /kpi-dmct, /dmct/*\n"
            "  - dae.demo@lanema.ci       -> /kpi-aero, /dae/*\n"
            "  - dea.demo@lanema.ci       -> /kpi-dea/* + portail labo /app (ADMIN)\n"
            "  - reception.demo@lanema.ci -> portail labo /app (role Service Reception)\n"
        ))

    def _create_direction_account(self, *, username, email, first_name, last_name, direction, bridge_labo=False):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'first_name': first_name, 'last_name': last_name, 'is_active': True},
        )
        if created:
            user.set_password(DEFAULT_PASSWORD)
            user.save()
        action = 'cree' if created else 'deja existant'
        self.stdout.write(f"  [{action}] {username} (direction={direction.nom})")

        UserProfile.objects.update_or_create(
            user=user,
            defaults={'role': 'DIRECTEUR', 'direction': direction},
        )

        if bridge_labo:
            # Meme regle que l'auto-bridge de core/views.py UserProfileView :
            # un compte DEAL de palier "direction" recoit le role labo ADMIN,
            # pour un acces immediat au portail /app sans attendre la
            # premiere connexion (qui l'aurait cree automatiquement).
            ClientProfile.objects.get_or_create(user=user, defaults={'role': 'ADMIN'})

    def _create_reception_account(self):
        username, email = 'reception.demo', 'reception.demo@lanema.ci'
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email, 'first_name': 'Service', 'last_name': 'Réception', 'is_active': True},
        )
        if created:
            user.set_password(DEFAULT_PASSWORD)
            user.save()
        action = 'cree' if created else 'deja existant'
        self.stdout.write(f"  [{action}] {username} (role labo=RECEPTION)")

        ClientProfile.objects.update_or_create(
            user=user,
            defaults={'role': 'RECEPTION', 'contact_nom': 'Service Réception'},
        )
