"""
Attributions par rôle pour les portails de direction (DAE, DMCT, DFIR...).

Trois paliers, communs à toutes les directions, dérivés du rôle e-diligence
existant (core.UserProfile.role) — pas de nouveau système de rôles :

- 'direction'   (ADMIN, DIRECTEUR)                          -> accès total.
- 'encadrement' (SOUS_DIRECTEUR, CHEF_SERVICE)               -> tout sauf Finance.
- 'terrain'     (AGENT, SUPERIEUR, SECRETAIRE, PRESTATAIRE)  -> uniquement leurs
  propres dossiers d'exécution technique (ordre de travail / prestation dont
  ils sont le technicien/agent assigné) ; aucun accès Clients, Qualité,
  Sécurité/Inspections, Stock/Instruments, Finance.

ADMIN a toujours accès à tout, quelle que soit sa Direction de rattachement.

Nom persisté (core.Direction.nom) -> code stable. Reste la source unique de
vérité, importée par core/views.py (réponse /api/users/me/) et par les
permissions ci-dessous.
"""
from rest_framework import permissions

DIRECTION_CODE_MAP = {
    "Direction de l'Aéronautique": 'DAE',
    "Direction de la Métrologie et des Contrôles Techniques": 'DMCT',
    "Direction de la Formation, de l'Innovation et de la Recherche": 'DFIR',
    # Services rattachés à la Direction Générale — modélisés comme des
    # Direction (même mécanisme d'accès) même s'il ne s'agit pas de
    # directions à part entière dans l'organigramme administratif.
    "DG — Communication et Marketing": 'DG_COM',
    "DG — Patrimoine": 'DG_PATRIMOINE',
    "DG — Qualité": 'DG_QUALITE',
    "DG — Juridique": 'DG_JURIDIQUE',
    "DG — Information et Documentation": 'DG_GED',
}

ROLE_TIERS = {
    'ADMIN': 'direction',
    'DIRECTEUR': 'direction',
    'SOUS_DIRECTEUR': 'encadrement',
    'CHEF_SERVICE': 'encadrement',
    'SUPERIEUR': 'terrain',
    'AGENT': 'terrain',
    'SECRETAIRE': 'terrain',
    'PRESTATAIRE': 'terrain',
}

_TIER_ORDER = {'terrain': 0, 'encadrement': 1, 'direction': 2}


def is_full_access_user(user):
    """Vrai pour ADMIN et pour tout compte rattaché à la Direction Générale
    (UserProfile.direction_generale) : ce dernier voit tout le système comme
    ADMIN (DAE, DMCT, DFIR, les 4 services rattachés à la DG, sans
    restriction de palier ni de Service), en plus de la vue 360°
    (dg_dashboard) déjà accessible à tout compte authentifié."""
    profile = getattr(user, 'profile', None)
    if not profile:
        return False
    return profile.role == 'ADMIN' or bool(profile.direction_generale_id)


def user_direction_code(user):
    profile = getattr(user, 'profile', None)
    if not profile or not profile.direction_id:
        return None
    return DIRECTION_CODE_MAP.get(profile.direction.nom)


def user_tier(user):
    profile = getattr(user, 'profile', None)
    if not profile:
        return None
    return ROLE_TIERS.get(profile.role)


DYNAMIC_MODULE_PERMISSION_KEYS = [
    'dae_view_finance', 'dmct_view_finance', 'dfir_view_finance', 'dfir_view_email',
]


def dynamic_module_permissions_for(user):
    """Liste des cles de modules dynamiques accordees a l'utilisateur (par
    role), pour affichage cote frontend (ex: Sidebar). Admin recoit tout le
    catalogue, sans lignes RolePermission necessaires."""
    from core.models import RolePermission

    profile = getattr(user, 'profile', None)
    if not profile:
        return []
    if is_full_access_user(user):
        return list(DYNAMIC_MODULE_PERMISSION_KEYS)
    return list(
        RolePermission.objects.filter(role=profile.role, permission__in=DYNAMIC_MODULE_PERMISSION_KEYS)
        .values_list('permission', flat=True)
    )


def has_dynamic_module_permission(user, feature_key):
    """Verifie si le role de l'utilisateur s'est vu accorder dynamiquement
    l'acces a un module dont la visibilite est pilotee depuis l'ecran
    Droits & Permissions (core.RolePermission), plutot que figee dans
    ROLE_TIERS/min_tier. Admin toujours autorise, pour eviter tout
    verrouillage accidentel."""
    from core.models import RolePermission

    profile = getattr(user, 'profile', None)
    if not profile:
        return False
    if is_full_access_user(user):
        return True
    return RolePermission.objects.filter(role=profile.role, permission=feature_key).exists()


def direction_permission(direction_code, min_tier=None, feature_key=None):
    """Fabrique une classe de permission DRF : membre de la Direction
    `direction_code` (ou Admin, toujours autorisé), puis :
    - si `feature_key` est fourni, l'acces est pilote dynamiquement par
      la matrice Droits & Permissions (core.RolePermission) plutot que par
      le palier fige du role ;
    - sinon, palier >= `min_tier` si fourni. `min_tier` in
      {'terrain', 'encadrement', 'direction'}."""

    class _DirectionPermission(permissions.BasePermission):
        def has_permission(self, request, view):
            user = getattr(request, 'user', None)
            if not user or not user.is_authenticated:
                return False
            profile = getattr(user, 'profile', None)
            if not profile:
                return False
            if is_full_access_user(user):
                return True
            if user_direction_code(user) != direction_code:
                return False
            if feature_key is not None:
                return has_dynamic_module_permission(user, feature_key)
            if min_tier is None:
                return True
            tier = user_tier(user)
            return tier is not None and _TIER_ORDER.get(tier, -1) >= _TIER_ORDER[min_tier]

    return _DirectionPermission


def scope_queryset_to_owner(queryset, request, owner_field):
    """Palier 'terrain' (hors Admin) : ne renvoie que les enregistrements où
    `owner_field` = l'utilisateur courant (ex: technicien, agent)."""
    user = request.user
    profile = getattr(user, 'profile', None)
    if profile and not is_full_access_user(user) and user_tier(user) == 'terrain':
        return queryset.filter(**{owner_field: user})
    return queryset


def user_service_name(user):
    """Nom du Service (core.Service.nom) auquel l'utilisateur est rattaché,
    ou None si non renseigné."""
    profile = getattr(user, 'profile', None)
    if not profile or not profile.service_id:
        return None
    return profile.service.nom


def scope_dg_service_queryset(queryset, request, service_name, owner_field=None):
    """Cloisonnement hiérarchique pour les services rattachés à la DG
    (Communication/Marketing, Patrimoine, Qualité, Juridique), en plus du
    rattachement de Direction déjà vérifié par direction_permission :

    - ADMIN et palier 'direction' (Directeur) : aucune restriction, vue
      complète de tout le service DG (tous ses Services internes).
    - Palier 'encadrement' (Sous-Directeur/Chef de service) ou 'terrain'
      (Agent...) rattaché à un AUTRE Service que `service_name` (ex: un
      compte Marketing consultant les données Communication) : aucun
      résultat — cloisonnement strict entre sous-équipes.
    - Palier 'terrain' correctement rattaché : uniquement ses propres
      dossiers, si `owner_field` est fourni (le modèle a un champ
      responsable/propriétaire) ; sinon vue complète du Service.
    - Palier 'encadrement' correctement rattaché (ou sans Service précisé) :
      vue complète du Service.
    """
    user = request.user
    profile = getattr(user, 'profile', None)
    if not profile or is_full_access_user(user):
        return queryset
    tier = user_tier(user)
    if tier == 'direction':
        return queryset
    service_nom = user_service_name(user)
    if service_nom and service_nom != service_name:
        return queryset.none()
    if tier == 'terrain' and owner_field:
        return queryset.filter(**{owner_field: user})
    return queryset
