from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('aero_maintenance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IncidentTechnique',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('gravite', models.CharField(choices=[('MINEURE', 'Mineure'), ('MAJEURE', 'Majeure'), ('CRITIQUE', 'Critique')], default='MINEURE', max_length=10)),
                ('description', models.TextField()),
                ('date_incident', models.DateField(auto_now_add=True)),
                ('est_accident', models.BooleanField(default=False)),
                ('ordre_travail', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='incidents_techniques', to='aero_maintenance.ordretravail')),
            ],
            options={
                'ordering': ['-date_incident'],
            },
        ),
        migrations.CreateModel(
            name='EcartReglementaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField()),
                ('date_constat', models.DateField(auto_now_add=True)),
                ('resolu', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-date_constat'],
            },
        ),
        migrations.CreateModel(
            name='RapportSecurite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('date_creation', models.DateField(auto_now_add=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['-date_creation'],
            },
        ),
        migrations.CreateModel(
            name='ControleReglementaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('organisme', models.CharField(default='ANAC', max_length=100)),
                ('date_controle', models.DateField()),
                ('resultat', models.CharField(choices=[('REUSSI', 'Réussi'), ('ECHEC', 'Échec')], default='REUSSI', max_length=10)),
            ],
            options={
                'ordering': ['-date_controle'],
            },
        ),
        migrations.CreateModel(
            name='FormationSecurite',
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
