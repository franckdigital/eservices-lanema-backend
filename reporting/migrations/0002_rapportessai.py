from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reporting', '0001_initial'),
        ('qualite', '0002_dea_kpis'),
    ]

    operations = [
        migrations.CreateModel(
            name='RapportEssai',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('statut', models.CharField(choices=[('BROUILLON', 'Brouillon'), ('EN_ATTENTE_VALIDATION', 'En attente de validation'), ('VALIDE', 'Validé'), ('CORRIGE', 'Corrigé'), ('SIGNE', 'Signé')], default='BROUILLON', max_length=30)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_soumission', models.DateField(blank=True, null=True)),
                ('date_validation', models.DateField(blank=True, null=True)),
                ('signe_electroniquement', models.BooleanField(default=False)),
                ('date_signature', models.DateField(blank=True, null=True)),
                ('delai_reglementaire_jours', models.PositiveIntegerField(blank=True, help_text="Delai reglementaire de remise, en jours, a compter de la fin de l'essai", null=True)),
                ('essai', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rapports_essai', to='qualite.essai')),
                ('valide_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='rapports_essai_valides', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_creation'],
            },
        ),
    ]
