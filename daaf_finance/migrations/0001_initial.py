from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0113_absence_prolongee_tracking'),
    ]

    operations = [
        migrations.CreateModel(
            name='Budget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('annee', models.CharField(max_length=10)),
                ('categorie', models.CharField(choices=[('FONCTIONNEMENT', 'Fonctionnement'), ('INVESTISSEMENT', 'Investissement')], default='FONCTIONNEMENT', max_length=20)),
                ('montant_prevu', models.DecimalField(decimal_places=2, default=0, max_digits=16)),
                ('montant_engage', models.DecimalField(decimal_places=2, default=0, max_digits=16)),
                ('montant_realise', models.DecimalField(decimal_places=2, default=0, max_digits=16)),
                ('nombre_revisions', models.PositiveIntegerField(default=0)),
                ('date_derniere_revision', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('direction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='budgets', to='core.direction')),
            ],
            options={
                'ordering': ['-annee'],
            },
        ),
        migrations.CreateModel(
            name='EcritureComptable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('date_ecriture', models.DateField()),
                ('montant', models.DecimalField(decimal_places=2, max_digits=14)),
                ('type', models.CharField(choices=[('DEBIT', 'Débit'), ('CREDIT', 'Crédit')], max_length=10)),
                ('piece_justificative', models.CharField(blank=True, max_length=100)),
                ('erreur', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-date_ecriture'],
            },
        ),
        migrations.CreateModel(
            name='Recette',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('type_prestation', models.CharField(blank=True, max_length=255)),
                ('client_nom', models.CharField(blank=True, max_length=255)),
                ('montant', models.DecimalField(decimal_places=2, max_digits=14)),
                ('date_emission', models.DateField()),
                ('date_encaissement', models.DateField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('EMISE', 'Émise'), ('ENCAISSEE', 'Encaissée'), ('IMPAYEE', 'Impayée')], default='EMISE', max_length=20)),
                ('direction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recettes', to='core.direction')),
            ],
            options={
                'ordering': ['-date_emission'],
            },
        ),
        migrations.CreateModel(
            name='Depense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('categorie', models.CharField(choices=[('FONCTIONNEMENT', 'Fonctionnement'), ('INVESTISSEMENT', 'Investissement'), ('MAINTENANCE', 'Maintenance'), ('CARBURANT', 'Carburant'), ('ELECTRICITE_EAU', 'Électricité et eau'), ('TELECOM', 'Télécommunications'), ('AUTRE', 'Autre')], default='FONCTIONNEMENT', max_length=20)),
                ('prestation_associee', models.CharField(blank=True, max_length=255)),
                ('fournisseur_nom', models.CharField(blank=True, max_length=255)),
                ('montant', models.DecimalField(decimal_places=2, max_digits=14)),
                ('date_engagement', models.DateField()),
                ('date_paiement', models.DateField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('ENGAGEE', 'Engagée'), ('PAYEE', 'Payée'), ('IMPAYEE', 'Impayée')], default='ENGAGEE', max_length=20)),
                ('direction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='depenses', to='core.direction')),
                ('site', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='depenses', to='core.site')),
            ],
            options={
                'ordering': ['-date_engagement'],
            },
        ),
    ]
