from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dfir_participants', '0001_initial'),
        ('dfir_formations', '0001_initial'),
        ('dfir_assistance', '0001_initial'),
        ('dfir_recherche', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FactureDFIR',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('type_prestation', models.CharField(choices=[('FORMATION', 'Formation'), ('ASSISTANCE', 'Assistance technique'), ('RECHERCHE', 'Recherche')], default='FORMATION', max_length=15)),
                ('montant_ht', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('montant_ttc', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('statut', models.CharField(choices=[('EMISE', 'Émise'), ('PAYEE', 'Payée'), ('IMPAYEE', 'Impayée')], default='EMISE', max_length=10)),
                ('date_emission', models.DateField(auto_now_add=True)),
                ('date_paiement', models.DateField(blank=True, null=True)),
                ('entreprise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='factures_dfir', to='dfir_participants.entreprisedfir')),
                ('mission', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='factures', to='dfir_assistance.missionassistance')),
                ('projet_recherche', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='factures', to='dfir_recherche.projetrecherche')),
                ('session', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='factures', to='dfir_formations.sessionformation')),
            ],
            options={
                'ordering': ['-date_emission'],
            },
        ),
    ]
