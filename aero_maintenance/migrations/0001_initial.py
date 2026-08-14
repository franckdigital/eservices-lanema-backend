from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('aero_clients', '0001_initial'),
        ('aero_stock', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrdreTravail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('type_intervention', models.CharField(choices=[('PREVENTIVE', 'Maintenance préventive'), ('CORRECTIVE', 'Maintenance corrective'), ('URGENCE', 'Urgence')], default='CORRECTIVE', max_length=20)),
                ('date_demande', models.DateTimeField(auto_now_add=True)),
                ('date_prise_charge', models.DateTimeField(blank=True, null=True)),
                ('date_debut', models.DateTimeField(blank=True, null=True)),
                ('date_fin_prevue', models.DateField(blank=True, null=True)),
                ('date_fin', models.DateField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('EN_ATTENTE', 'En attente'), ('EN_COURS', 'En cours'), ('TERMINE', 'Terminé'), ('ANNULE', 'Annulé')], default='EN_ATTENTE', max_length=20)),
                ('aeronef', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ordres_travail', to='aero_clients.aeronef')),
                ('piece_utilisee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ordres_travail', to='aero_stock.piecerechange')),
                ('technicien', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ordres_travail_dae', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_demande'],
            },
        ),
        migrations.CreateModel(
            name='RoueAeronef',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_serie', models.CharField(max_length=50, unique=True)),
                ('statut', models.CharField(choices=[('EN_SERVICE', 'En service'), ('EN_INSPECTION', 'En inspection'), ('REPAREE', 'Réparée'), ('REMPLACEE', 'Remplacée'), ('NON_CONFORME', 'Non conforme')], default='EN_SERVICE', max_length=20)),
                ('nombre_cycles', models.PositiveIntegerField(default=0)),
                ('aeronef', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='roues', to='aero_clients.aeronef')),
            ],
            options={
                'ordering': ['numero_serie'],
            },
        ),
        migrations.CreateModel(
            name='InspectionRoue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_inspection', models.DateField(auto_now_add=True)),
                ('conforme', models.BooleanField(default=True)),
                ('type_inspection', models.CharField(choices=[('INSPECTION_PERIODIQUE', 'Inspection périodique'), ('REPARATION', 'Réparation'), ('REMPLACEMENT', 'Remplacement')], default='INSPECTION_PERIODIQUE', max_length=25)),
                ('ordre_travail', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inspections_roues', to='aero_maintenance.ordretravail')),
                ('roue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inspections', to='aero_maintenance.roueaeronef')),
            ],
            options={
                'ordering': ['-date_inspection'],
            },
        ),
        migrations.CreateModel(
            name='BatterieAeronef',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_serie', models.CharField(max_length=50, unique=True)),
                ('statut', models.CharField(choices=[('EN_SERVICE', 'En service'), ('EN_TEST', 'En test'), ('RECHARGEE', 'Rechargée'), ('REPAREE', 'Réparée'), ('REMPLACEE', 'Remplacée'), ('HORS_SERVICE', 'Hors service')], default='EN_SERVICE', max_length=20)),
                ('date_mise_en_service', models.DateField(blank=True, null=True)),
                ('date_derniere_maintenance', models.DateField(blank=True, null=True)),
                ('aeronef', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='batteries', to='aero_clients.aeronef')),
            ],
            options={
                'ordering': ['numero_serie'],
            },
        ),
    ]
