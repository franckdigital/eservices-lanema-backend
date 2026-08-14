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
            name='Equipement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=100, unique=True)),
                ('designation', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[('BALANCE', 'Balance'), ('ETUVE', 'Étuve'), ('PRESSE', 'Presse'), ('THERMOMETRE', 'Thermomètre'), ('AUTRE', 'Autre')], default='BALANCE', max_length=50)),
                ('marque', models.CharField(blank=True, max_length=100)),
                ('modele', models.CharField(blank=True, max_length=100)),
                ('date_dernier_etalonnage', models.DateField(blank=True, null=True)),
                ('date_prochain_etalonnage', models.DateField(blank=True, null=True)),
                ('localisation', models.CharField(blank=True, max_length=255)),
                ('statut', models.CharField(choices=[('OPERATIONNEL', 'Opérationnel'), ('ETALONNAGE_REQUIS', 'Étalonnage requis'), ('MAINTENANCE', 'Maintenance'), ('HORS_SERVICE', 'Hors service')], default='OPERATIONNEL', max_length=20)),
                ('responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='equipements_metrologie', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Etalonnage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_etalonnage', models.DateField()),
                ('date_prochain', models.DateField()),
                ('prestataire', models.CharField(blank=True, max_length=255)),
                ('resultat', models.CharField(default='CONFORME', max_length=50)),
                ('equipement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='etalonnages', to='metrologie.equipement')),
            ],
        ),
    ]
