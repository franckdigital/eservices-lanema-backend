from django.db import migrations


def seed_permissions(apps, schema_editor):
    from clients.permissions_catalog import DEFAULT_ROLE_PERMISSIONS

    LaboRolePermission = apps.get_model('clients', 'LaboRolePermission')
    rows = [
        LaboRolePermission(role=role, permission_code=code, is_granted=True)
        for role, codes in DEFAULT_ROLE_PERMISSIONS.items()
        for code in codes
    ]
    LaboRolePermission.objects.bulk_create(rows, ignore_conflicts=True)


def unseed_permissions(apps, schema_editor):
    LaboRolePermission = apps.get_model('clients', 'LaboRolePermission')
    LaboRolePermission.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0005_laborolepermission'),
    ]

    operations = [
        migrations.RunPython(seed_permissions, unseed_permissions),
    ]
