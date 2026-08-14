from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('aero_clients', '0001_initial'),
        ('aero_maintenance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FactureDAE',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('montant_ht', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('montant_ttc', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('statut', models.CharField(choices=[('EMISE', 'Émise'), ('PAYEE', 'Payée'), ('IMPAYEE', 'Impayée')], default='EMISE', max_length=10)),
                ('date_emission', models.DateField(auto_now_add=True)),
                ('date_paiement', models.DateField(blank=True, null=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='factures', to='aero_clients.clientaeronautique')),
                ('ordre_travail', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='factures', to='aero_maintenance.ordretravail')),
            ],
            options={
                'ordering': ['-date_emission'],
            },
        ),
    ]
