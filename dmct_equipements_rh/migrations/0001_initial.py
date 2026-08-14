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
            name='EquipementReference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=100, unique=True)),
                ('designation', models.CharField(max_length=255)),
                ('est_etalon', models.BooleanField(default=False)),
                ('statut', models.CharField(choices=[('OPERATIONNEL', 'Opérationnel'), ('MAINTENANCE', 'Maintenance'), ('HORS_SERVICE', 'Hors service')], default='OPERATIONNEL', max_length=20)),
                ('date_dernier_etalonnage', models.DateField(blank=True, null=True)),
                ('date_prochain_etalonnage', models.DateField(blank=True, null=True)),
            ],
            options={
                'ordering': ['designation'],
            },
        ),
        migrations.CreateModel(
            name='PanneEquipementReference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_panne', models.DateField(auto_now_add=True)),
                ('date_reparation', models.DateField(blank=True, null=True)),
                ('description', models.TextField(blank=True)),
                ('equipement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pannes', to='dmct_equipements_rh.equipementreference')),
            ],
            options={
                'ordering': ['-date_panne'],
            },
        ),
        migrations.CreateModel(
            name='MaintenancePreventiveReference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_prevue', models.DateField()),
                ('date_realisee', models.DateField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('PLANIFIEE', 'Planifiée'), ('REALISEE', 'Réalisée'), ('REPORTEE', 'Reportée')], default='PLANIFIEE', max_length=20)),
                ('equipement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maintenances_preventives', to='dmct_equipements_rh.equipementreference')),
            ],
            options={
                'ordering': ['-date_prevue'],
            },
        ),
        migrations.CreateModel(
            name='EtalonnageReference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_etalonnage', models.DateField()),
                ('date_prochain', models.DateField()),
                ('resultat', models.CharField(default='CONFORME', max_length=50)),
                ('equipement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='etalonnages', to='dmct_equipements_rh.equipementreference')),
            ],
            options={
                'ordering': ['-date_etalonnage'],
            },
        ),
        migrations.CreateModel(
            name='CertificationAgentDMCT',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('competence', models.CharField(max_length=255)),
                ('date_obtention', models.DateField()),
                ('date_expiration', models.DateField(blank=True, null=True)),
                ('agent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='certifications_dmct', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_obtention'],
            },
        ),
        migrations.CreateModel(
            name='FormationDMCT',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(max_length=255)),
                ('date_formation', models.DateField()),
                ('nombre_participants', models.PositiveIntegerField(default=0)),
                ('duree_heures', models.DecimalField(decimal_places=1, default=0, max_digits=6)),
            ],
            options={
                'ordering': ['-date_formation'],
            },
        ),
    ]
