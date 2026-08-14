from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dmct_clients', '0001_initial'),
        ('dmct_prestations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FactureDMCT',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('montant_ht', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('montant_ttc', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('statut', models.CharField(choices=[('EMISE', 'Émise'), ('PAYEE', 'Payée'), ('IMPAYEE', 'Impayée')], default='EMISE', max_length=10)),
                ('date_emission', models.DateField(auto_now_add=True)),
                ('date_paiement', models.DateField(blank=True, null=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='factures', to='dmct_clients.clientdmct')),
                ('prestation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='factures', to='dmct_prestations.prestationdmct')),
            ],
            options={
                'ordering': ['-date_emission'],
            },
        ),
    ]
