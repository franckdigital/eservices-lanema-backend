from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('facturation', '0002_demandeanalyse_laboratoire'),
    ]

    operations = [
        # Champs de validation responsable (signature + cachet) sur Proforma
        migrations.AddField(
            model_name='proforma',
            name='valide_par_responsable',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='proforma',
            name='date_validation_responsable',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='proforma',
            name='signature_responsable_appliquee',
            field=models.BooleanField(default=False),
        ),

        # Nouveau modele BonCommande
        migrations.CreateModel(
            name='BonCommande',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valide_par_responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('date_validation_responsable', models.DateField(blank=True, null=True)),
                ('signature_responsable_appliquee', models.BooleanField(default=False)),
                ('numero', models.CharField(max_length=50, unique=True)),
                ('montant_ht', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('montant_ttc', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('devise', models.CharField(default='EUR', max_length=10)),
                ('statut', models.CharField(choices=[('EMIS', 'Émis'), ('SIGNE_CLIENT', 'Signé par le client'), ('ANNULE', 'Annulé')], default='EMIS', max_length=20)),
                ('date_emission', models.DateField(auto_now_add=True)),
                ('signature_client_image', models.ImageField(blank=True, null=True, upload_to='facturation/signatures_client/')),
                ('date_signature_client', models.DateField(blank=True, null=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bons_commande', to=settings.AUTH_USER_MODEL)),
                ('proforma', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bons_commande', to='facturation.proforma')),
            ],
            options={
                'ordering': ['-date_emission', '-id'],
            },
        ),

        # Champs de validation responsable + chainage Proforma/BonCommande sur Facture
        migrations.AddField(
            model_name='facture',
            name='valide_par_responsable',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='facture',
            name='date_validation_responsable',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='facture',
            name='signature_responsable_appliquee',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='facture',
            name='proforma',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='factures', to='facturation.proforma'),
        ),
        migrations.AddField(
            model_name='facture',
            name='bon_commande',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='factures', to='facturation.boncommande'),
        ),

        # Tracabilite directe Facture <-> DemandeAnalyse
        migrations.AddField(
            model_name='demandeanalyse',
            name='facture',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='demandes_analyses', to='facturation.facture'),
        ),
    ]
