"""Catalogue des permissions du portail staff labo (/app) et matrice de
droits par defaut par role (ClientProfile.role).

Le catalogue est statique (code, libelle, module) : les permissions
elles-memes ne sont pas creees/supprimees depuis l'UI, seul leur octroi par
role l'est (cf. clients.models.LaboRolePermission, ecran Administration >
Permissions)."""

PERMISSION_CATALOG = [
    ("dashboard.view", "Voir le tableau de bord", "Tableau de bord"),

    ("clients.view", "Voir les clients", "Clients"),
    ("clients.manage", "Gerer les clients", "Clients"),

    ("echantillons.view", "Voir les echantillons", "Echantillons"),
    ("echantillons.manage", "Gerer les echantillons", "Echantillons"),

    ("essais.view", "Voir les essais", "Essais"),
    ("essais.manage", "Gerer les essais", "Essais"),

    ("metrologie.view", "Voir la metrologie", "Metrologie"),
    ("metrologie.manage", "Gerer la metrologie", "Metrologie"),

    ("facturation.view", "Voir la facturation", "Facturation"),
    ("facturation.manage", "Gerer la facturation", "Facturation"),

    ("qualite.view", "Voir la qualite", "Qualite"),
    ("qualite.manage", "Gerer la qualite", "Qualite"),

    ("stock.view", "Voir le stock", "Stock"),
    ("stock.manage", "Gerer le stock", "Stock"),

    ("reporting.view", "Voir le reporting", "Reporting"),
    ("notifications.view", "Voir les notifications", "Notifications"),

    ("admin.users", "Administrer les utilisateurs", "Administration"),
    ("admin.proformas", "Administrer les devis", "Administration"),
    ("admin.analyses", "Administrer les demandes d'analyse", "Administration"),
    ("admin.permissions", "Administrer les permissions", "Administration"),
    ("admin.vitrine", "Administrer la vitrine du site", "Administration"),
]

PERMISSION_CODES = [code for code, _label, _module in PERMISSION_CATALOG]

# Matrice de droits par defaut, appliquee a la premiere migration puis
# librement modifiable ensuite depuis l'ecran Administration > Permissions.
DEFAULT_ROLE_PERMISSIONS = {
    "ADMIN": list(PERMISSION_CODES),  # toujours tout, cf. user_permission_codes
    "GESTIONNAIRE": [
        "dashboard.view",
        "clients.view", "clients.manage",
        "echantillons.view", "echantillons.manage",
        "essais.view", "essais.manage",
        "metrologie.view", "metrologie.manage",
        "facturation.view", "facturation.manage",
        "qualite.view", "qualite.manage",
        "stock.view", "stock.manage",
        "reporting.view",
        "notifications.view",
    ],
    "TECHNICIEN": [
        "dashboard.view",
        "echantillons.view", "echantillons.manage",
        "essais.view", "essais.manage",
        "metrologie.view",
        "qualite.view",
        "notifications.view",
    ],
    "COMPTABLE": [
        "dashboard.view",
        "clients.view",
        "facturation.view", "facturation.manage",
        "reporting.view",
        "notifications.view",
    ],
}
