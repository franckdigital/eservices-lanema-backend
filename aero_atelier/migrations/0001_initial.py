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
            name='EquipementAtelier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=100, unique=True)),
                ('designation', models.CharField(max_length=255)),
                ('statut', models.CharField(choices=[('OPERATIONNEL', 'Opérationnel'), ('MAINTENANCE', 'Maintenance'), ('HORS_SERVICE', 'Hors service')], default='OPERATIONNEL', max_length=20)),
            ],
            options={
                'ordering': ['designation'],
            },
        ),
        migrations.CreateModel(
            name='PanneEquipementAtelier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_panne', models.DateField(auto_now_add=True)),
                ('date_reparation', models.DateField(blank=True, null=True)),
                ('description', models.TextField(blank=True)),
                ('equipement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pannes', to='aero_atelier.equipementatelier')),
            ],
            options={
                'ordering': ['-date_panne'],
            },
        ),
        migrations.CreateModel(
            name='MaintenancePreventiveAtelier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_prevue', models.DateField()),
                ('date_realisee', models.DateField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('PLANIFIEE', 'Planifiée'), ('REALISEE', 'Réalisée'), ('REPORTEE', 'Reportée')], default='PLANIFIEE', max_length=20)),
                ('equipement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maintenances_preventives', to='aero_atelier.equipementatelier')),
            ],
            options={
                'ordering': ['-date_prevue'],
            },
        ),
        migrations.CreateModel(
            name='EtalonnageAtelier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_etalonnage', models.DateField()),
                ('date_prochain', models.DateField()),
                ('resultat', models.CharField(default='CONFORME', max_length=50)),
                ('equipement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='etalonnages', to='aero_atelier.equipementatelier')),
            ],
            options={
                'ordering': ['-date_etalonnage'],
            },
        ),
        migrations.CreateModel(
            name='CertificationTechnicien',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('competence', models.CharField(max_length=255)),
                ('date_obtention', models.DateField()),
                ('date_expiration', models.DateField(blank=True, null=True)),
                ('technicien', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='certifications_dae', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_obtention'],
            },
        ),
    ]
