from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('ADMIN', 'Administrateur'), ('GESTIONNAIRE', 'Gestionnaire'), ('TECHNICIEN', 'Technicien'), ('CLIENT', 'Client'), ('FOURNISSEUR', 'Fournisseur')], default='CLIENT', max_length=20)),
                ('type_subscription', models.CharField(blank=True, max_length=50)),
                ('organisation', models.CharField(blank=True, max_length=255)),
                ('raison_sociale', models.CharField(blank=True, max_length=255)),
                ('adresse', models.CharField(blank=True, max_length=255)),
                ('telephone', models.CharField(blank=True, max_length=50)),
                ('siret', models.CharField(blank=True, max_length=50)),
                ('contact_nom', models.CharField(blank=True, max_length=255)),
                ('expo_push_token', models.CharField(blank=True, max_length=255, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='client_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
