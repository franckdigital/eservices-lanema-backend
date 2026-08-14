from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('demandes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Proforma',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=50, unique=True)),
                ('montant_ht', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('montant_ttc', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('devise', models.CharField(default='EUR', max_length=10)),
                ('statut', models.CharField(choices=[('BROUILLON', 'Brouillon'), ('ENVOYEE', 'Envoyée'), ('VALIDEE', 'Validée'), ('ACCEPTEE', 'Acceptée'), ('REFUSEE', 'Refusée'), ('ANNULEE', 'Annulée')], default='BROUILLON', max_length=20)),
                ('date_emission', models.DateField(auto_now_add=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='proformas', to=settings.AUTH_USER_MODEL)),
                ('demande_devis', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='proformas', to='demandes.demandedevis')),
            ],
            options={
                'ordering': ['-date_emission', '-id'],
            },
        ),
        migrations.CreateModel(
            name='Facture',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=50, unique=True)),
                ('montant_ht', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('montant_ttc', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('devise', models.CharField(default='EUR', max_length=10)),
                ('statut', models.CharField(choices=[('EN_ATTENTE', 'En attente'), ('EN_ATTENTE_VALIDATION', 'En attente de validation comptable'), ('PAYEE', 'Payée'), ('ANNULEE', 'Annulée')], default='EN_ATTENTE', max_length=30)),
                ('date_emission', models.DateField(auto_now_add=True)),
                ('date_echeance', models.DateField(blank=True, null=True)),
                ('date_paiement', models.DateField(blank=True, null=True)),
                ('mode_paiement', models.CharField(blank=True, choices=[('CHEQUE', 'Chèque'), ('COMPTANT', 'Comptant')], max_length=20)),
                ('justificatif_paiement', models.FileField(blank=True, null=True, upload_to='factures/paiements/')),
                ('paiement_valide', models.BooleanField(default=False)),
                ('visible_client', models.BooleanField(default=False, help_text="Quand vrai, la facture apparaît dans l'espace client")),
                ('reference_paiement', models.CharField(blank=True, max_length=100)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='factures', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_emission', '-id'],
            },
        ),
        migrations.CreateModel(
            name='DemandeAnalyse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=50, unique=True)),
                ('statut', models.CharField(choices=[('EN_ATTENTE_ECHANTILLONS', "En attente d'échantillons"), ('ECHANTILLONS_RECUS', 'Échantillons reçus'), ('EN_COURS', "En cours d'analyse"), ('TERMINEE', 'Terminée'), ('RESULTATS_ENVOYES', 'Résultats envoyés')], default='EN_ATTENTE_ECHANTILLONS', max_length=40)),
                ('montant_ht', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('montant_ttc', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_depot_echantillons', models.DateField(blank=True, null=True)),
                ('date_debut_analyse', models.DateField(blank=True, null=True)),
                ('date_fin_analyse', models.DateField(blank=True, null=True)),
                ('observations', models.TextField(blank=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='demandes_analyses', to=settings.AUTH_USER_MODEL)),
                ('demande_devis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='demandes_analyses', to='demandes.demandedevis')),
                ('proforma', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='demandes_analyses', to='facturation.proforma')),
            ],
            options={
                'ordering': ['-date_creation'],
            },
        ),
    ]
