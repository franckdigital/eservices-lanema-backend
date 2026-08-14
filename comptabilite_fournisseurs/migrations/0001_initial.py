from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='FournisseurComptable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raison_sociale', models.CharField(max_length=255, unique=True)),
                ('rccm', models.CharField(blank=True, max_length=100)),
                ('adresse', models.CharField(blank=True, max_length=255)),
                ('telephone', models.CharField(blank=True, max_length=50)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('rib', models.CharField(blank=True, help_text='Coordonnées bancaires du fournisseur', max_length=100)),
                ('contact_nom', models.CharField(blank=True, max_length=255)),
                ('actif', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['raison_sociale'],
            },
        ),
        migrations.CreateModel(
            name='FactureFournisseur',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('objet', models.CharField(blank=True, max_length=255)),
                ('montant_ht', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('montant_ttc', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('date_reception', models.DateField(auto_now_add=True)),
                ('date_echeance', models.DateField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('RECUE', 'Reçue'), ('VALIDEE', 'Validée'), ('PAYEE', 'Payée'), ('LITIGE', 'En litige')], default='RECUE', max_length=10)),
                ('piece_jointe', models.FileField(blank=True, null=True, upload_to='comptabilite/factures_fournisseurs/')),
                ('fournisseur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='factures', to='comptabilite_fournisseurs.fournisseurcomptable')),
            ],
            options={
                'ordering': ['-date_reception'],
            },
        ),
        migrations.CreateModel(
            name='PaiementFournisseur',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('montant', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('date_paiement', models.DateField(auto_now_add=True)),
                ('mode_paiement', models.CharField(choices=[('VIREMENT', 'Virement'), ('CHEQUE', 'Chèque'), ('ESPECES', 'Espèces')], default='VIREMENT', max_length=15)),
                ('reference_paiement', models.CharField(blank=True, max_length=100)),
                ('facture_fournisseur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='paiements', to='comptabilite_fournisseurs.facturefournisseur')),
            ],
            options={
                'ordering': ['-date_paiement'],
            },
        ),
    ]
