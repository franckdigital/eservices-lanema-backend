from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0003_clientprofile_signature_cachet'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientprofile',
            name='role',
            field=models.CharField(
                choices=[
                    ('ADMIN', 'Administrateur'),
                    ('GESTIONNAIRE', 'Gestionnaire'),
                    ('TECHNICIEN', 'Technicien'),
                    ('CLIENT', 'Client'),
                    ('FOURNISSEUR', 'Fournisseur'),
                    ('COMPTABLE', 'Comptable'),
                ],
                default='CLIENT',
                max_length=20,
            ),
        ),
    ]
