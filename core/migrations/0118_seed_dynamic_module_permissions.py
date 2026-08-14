from django.db import migrations

# Reproduit exactement le comportement actuel (avant passage au controle
# dynamique) : ces 4 modules etaient reserves au palier 'direction'
# (role DIRECTEUR, en plus d'ADMIN qui bypasse toujours). Cette seed evite
# tout verrouillage/elargissement accidentel au moment de la migration ;
# les droits restent ensuite modifiables depuis Droits & Permissions.
DEFAULT_GRANTS = {
    'DIRECTEUR': [
        'dae_view_finance',
        'dmct_view_finance',
        'dfir_view_finance',
        'dfir_view_email',
    ],
}


def seed_permissions(apps, schema_editor):
    RolePermission = apps.get_model('core', 'RolePermission')
    rows = [
        RolePermission(role=role, permission=code)
        for role, codes in DEFAULT_GRANTS.items()
        for code in codes
    ]
    RolePermission.objects.bulk_create(rows, ignore_conflicts=True)


def unseed_permissions(apps, schema_editor):
    RolePermission = apps.get_model('core', 'RolePermission')
    codes = [code for codes in DEFAULT_GRANTS.values() for code in codes]
    RolePermission.objects.filter(permission__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0117_pointage_hors_ligne'),
    ]

    operations = [
        migrations.RunPython(seed_permissions, unseed_permissions),
    ]
