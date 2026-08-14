from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0002_reclamationclient'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientprofile',
            name='signature_image',
            field=models.ImageField(blank=True, null=True, upload_to='clients/signatures_responsable/'),
        ),
        migrations.AddField(
            model_name='clientprofile',
            name='cachet_image',
            field=models.ImageField(blank=True, null=True, upload_to='clients/cachets_responsable/'),
        ),
    ]
