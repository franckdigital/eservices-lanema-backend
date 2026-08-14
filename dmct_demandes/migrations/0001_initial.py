from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dmct_clients', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DemandeDMCT',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('type_demande', models.CharField(choices=[('VERIFICATION', 'Vérification'), ('ETALONNAGE', 'Étalonnage')], default='VERIFICATION', max_length=20)),
                ('date_demande', models.DateTimeField(auto_now_add=True)),
                ('date_enregistrement', models.DateTimeField(blank=True, null=True)),
                ('date_prise_charge', models.DateTimeField(blank=True, null=True)),
                ('date_limite_prise_charge', models.DateTimeField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('EN_ATTENTE', 'En attente'), ('ENREGISTREE', 'Enregistrée'), ('EN_COURS', 'En cours'), ('TERMINEE', 'Terminée'), ('ANNULEE', 'Annulée')], default='EN_ATTENTE', max_length=20)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='demandes', to='dmct_clients.clientdmct')),
            ],
            options={
                'ordering': ['-date_demande'],
            },
        ),
    ]
