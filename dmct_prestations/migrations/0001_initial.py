from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dmct_demandes', '0001_initial'),
        ('dmct_instruments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrestationDMCT',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('type_prestation', models.CharField(choices=[('CONTROLE', 'Contrôle'), ('ETALONNAGE', 'Étalonnage'), ('VERIFICATION', 'Vérification'), ('CERTIFICATION', 'Certification')], default='CONTROLE', max_length=20)),
                ('lieu', models.CharField(choices=[('SUR_SITE', 'Sur site'), ('LABORATOIRE', 'Laboratoire')], default='LABORATOIRE', max_length=20)),
                ('conforme', models.BooleanField(blank=True, null=True)),
                ('urgent', models.BooleanField(default=False)),
                ('date_debut', models.DateTimeField(blank=True, null=True)),
                ('date_fin', models.DateTimeField(blank=True, null=True)),
                ('date_fin_prevue', models.DateTimeField(blank=True, null=True)),
                ('date_livraison_certificat', models.DateField(blank=True, null=True)),
                ('cout_revient', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('statut', models.CharField(choices=[('EN_COURS', 'En cours'), ('TERMINEE', 'Terminée'), ('ANNULEE', 'Annulée')], default='EN_COURS', max_length=20)),
                ('agent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='prestations_dmct', to=settings.AUTH_USER_MODEL)),
                ('demande', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='prestations', to='dmct_demandes.demandedmct')),
                ('instrument', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='prestations', to='dmct_instruments.instrumentmesure')),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
    ]
