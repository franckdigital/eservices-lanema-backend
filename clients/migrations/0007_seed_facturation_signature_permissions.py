from django.db import migrations

# Nouveaux codes introduits pour rendre dynamiques (Administration > Permissions)
# des controles qui etaient en dur dans facturation/views.py : validation du
# paiement, et signature du responsable labo sur devis/bon de commande/facture.
NEW_GRANTS = {
    "GESTIONNAIRE": ["facturation.valider_paiement", "facturation.valider_responsable"],
    "COMPTABLE": ["facturation.valider_paiement"],
}


def seed_permissions(apps, schema_editor):
    LaboRolePermission = apps.get_model('clients', 'LaboRolePermission')
    rows = [
        LaboRolePermission(role=role, permission_code=code, is_granted=True)
        for role, codes in NEW_GRANTS.items()
        for code in codes
    ]
    LaboRolePermission.objects.bulk_create(rows, ignore_conflicts=True)


def unseed_permissions(apps, schema_editor):
    LaboRolePermission = apps.get_model('clients', 'LaboRolePermission')
    for role, codes in NEW_GRANTS.items():
        LaboRolePermission.objects.filter(role=role, permission_code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0006_seed_labo_role_permissions'),
    ]

    operations = [
        migrations.RunPython(seed_permissions, unseed_permissions),
    ]
