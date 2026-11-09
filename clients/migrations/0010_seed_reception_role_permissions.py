from django.db import migrations


def seed_permissions(apps, schema_editor):
    from clients.permissions_catalog import DEFAULT_ROLE_PERMISSIONS

    LaboRolePermission = apps.get_model('clients', 'LaboRolePermission')
    rows = [
        LaboRolePermission(role='RECEPTION', permission_code=code, is_granted=True)
        for code in DEFAULT_ROLE_PERMISSIONS['RECEPTION']
    ]
    LaboRolePermission.objects.bulk_create(rows, ignore_conflicts=True)


def unseed_permissions(apps, schema_editor):
    LaboRolePermission = apps.get_model('clients', 'LaboRolePermission')
    LaboRolePermission.objects.filter(role='RECEPTION').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0009_alter_clientprofile_role_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_permissions, unseed_permissions),
    ]
