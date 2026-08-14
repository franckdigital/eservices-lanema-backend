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
            name='Bien',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=100, unique=True)),
                ('designation', models.CharField(max_length=255)),
                ('categorie', models.CharField(choices=[('MOBILIER', 'Mobilier'), ('INFORMATIQUE', 'Informatique'), ('VEHICULE', 'Véhicule'), ('IMMOBILIER', 'Immobilier'), ('EQUIPEMENT', 'Équipement technique'), ('AUTRE', 'Autre')], default='AUTRE', max_length=20)),
                ('date_acquisition', models.DateField(blank=True, null=True)),
                ('valeur_acquisition', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('valeur_actuelle', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ('duree_amortissement_ans', models.PositiveIntegerField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('EN_SERVICE', 'En service'), ('EN_MAINTENANCE', 'En maintenance'), ('REFORME', 'Réformé'), ('PERDU', 'Perdu'), ('SORTI', 'Sorti')], default='EN_SERVICE', max_length=20)),
                ('localisation', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='biens_patrimoine', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='InventairePatrimoine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_inventaire', models.DateField()),
                ('nombre_biens_verifies', models.PositiveIntegerField(default=0)),
                ('ecarts_constates', models.PositiveIntegerField(default=0)),
                ('observations', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inventaires_patrimoine', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_inventaire'],
            },
        ),
        migrations.CreateModel(
            name='MouvementBien',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_mouvement', models.CharField(choices=[('ENTREE', 'Entrée'), ('SORTIE', 'Sortie'), ('TRANSFERT', 'Transfert'), ('REFORME', 'Réforme'), ('PERTE', 'Perte')], max_length=20)),
                ('motif', models.TextField(blank=True)),
                ('date_mouvement', models.DateTimeField(auto_now_add=True)),
                ('bien', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mouvements', to='dg_patrimoine.bien')),
                ('effectue_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mouvements_bien', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_mouvement'],
            },
        ),
        migrations.CreateModel(
            name='MaintenanceBien',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_maintenance', models.CharField(choices=[('PREVENTIVE', 'Préventive'), ('CORRECTIVE', 'Corrective')], default='PREVENTIVE', max_length=20)),
                ('date_maintenance', models.DateField()),
                ('date_fin', models.DateField(blank=True, null=True)),
                ('cout', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('description', models.TextField(blank=True)),
                ('bien', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maintenances', to='dg_patrimoine.bien')),
            ],
            options={
                'ordering': ['-date_maintenance'],
            },
        ),
    ]
