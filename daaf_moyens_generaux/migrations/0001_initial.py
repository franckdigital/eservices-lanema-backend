from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0113_absence_prolongee_tracking'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vehicule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('immatriculation', models.CharField(max_length=50, unique=True)),
                ('marque', models.CharField(blank=True, max_length=100)),
                ('modele', models.CharField(blank=True, max_length=100)),
                ('statut', models.CharField(choices=[('DISPONIBLE', 'Disponible'), ('EN_MISSION', 'En mission'), ('EN_PANNE', 'En panne'), ('EN_MAINTENANCE', 'En maintenance')], default='DISPONIBLE', max_length=20)),
                ('kilometrage', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['immatriculation'],
            },
        ),
        migrations.CreateModel(
            name='Batiment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255)),
                ('disponible', models.BooleanField(default=True)),
                ('etat', models.CharField(blank=True, max_length=100)),
                ('site', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='batiments', to='core.site')),
            ],
            options={
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='PanneVehicule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_panne', models.DateField(auto_now_add=True)),
                ('date_reparation', models.DateField(blank=True, null=True)),
                ('cout', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('description', models.TextField(blank=True)),
                ('vehicule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pannes', to='daaf_moyens_generaux.vehicule')),
            ],
            options={
                'ordering': ['-date_panne'],
            },
        ),
        migrations.CreateModel(
            name='Salle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255)),
                ('capacite', models.PositiveIntegerField(default=0)),
                ('batiment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='salles', to='daaf_moyens_generaux.batiment')),
            ],
            options={
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='ReservationSalle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_debut', models.DateTimeField()),
                ('date_fin', models.DateTimeField()),
                ('motif', models.CharField(blank=True, max_length=255)),
                ('salle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='daaf_moyens_generaux.salle')),
            ],
            options={
                'ordering': ['-date_debut'],
            },
        ),
        migrations.CreateModel(
            name='InterventionTechnique',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_intervention', models.CharField(blank=True, max_length=100)),
                ('date_intervention', models.DateField(auto_now_add=True)),
                ('description', models.TextField(blank=True)),
                ('batiment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='interventions', to='daaf_moyens_generaux.batiment')),
            ],
            options={
                'ordering': ['-date_intervention'],
            },
        ),
    ]
