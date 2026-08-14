from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('qualite', '0001_initial'),
        ('laboratoires', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='echantillon',
            name='statut',
            field=models.CharField(choices=[('RECEPTIONNE', 'Réceptionné'), ('EN_ATTENTE', 'En attente'), ('EN_ANALYSE', 'En analyse'), ('TERMINE', 'Terminé'), ('REJETE', 'Rejeté'), ('ARCHIVE', 'Archivé')], default='RECEPTIONNE', max_length=20),
        ),
        migrations.AddField(
            model_name='echantillon',
            name='conforme',
            field=models.BooleanField(blank=True, help_text="Conformite de l'echantillon suite a analyse (null = pas encore evalue)", null=True),
        ),
        migrations.AddField(
            model_name='essai',
            name='laboratoire',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='essais', to='laboratoires.laboratoire'),
        ),
        migrations.AddField(
            model_name='essai',
            name='date_fin',
            field=models.DateField(blank=True, help_text="Date reelle de fin de l'essai", null=True),
        ),
        migrations.AddField(
            model_name='essai',
            name='technicien_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='essais_technicien', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='essai',
            name='urgent',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='essai',
            name='est_reprise',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='essai',
            name='essai_origine',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reprises', to='qualite.essai'),
        ),
        migrations.AddField(
            model_name='essai',
            name='erreur_detectee',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='essai',
            name='cout_revient',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='nonconformite',
            name='essai',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='non_conformites', to='qualite.essai'),
        ),
        migrations.CreateModel(
            name='ActionQualite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('CORRECTIVE', 'Corrective'), ('PREVENTIVE', 'Préventive')], max_length=20)),
                ('description', models.TextField()),
                ('statut', models.CharField(choices=[('PLANIFIEE', 'Planifiée'), ('EN_COURS', 'En cours'), ('CLOTUREE', 'Clôturée')], default='PLANIFIEE', max_length=20)),
                ('date_planification', models.DateField(auto_now_add=True)),
                ('date_cloture', models.DateField(blank=True, null=True)),
                ('non_conformite', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actions', to='qualite.nonconformite')),
                ('responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actions_qualite_labo', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_planification'],
            },
        ),
        migrations.CreateModel(
            name='RecommandationAudit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('appliquee', models.BooleanField(default=False)),
                ('date_echeance', models.DateField(blank=True, null=True)),
                ('audit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommandations', to='qualite.audit')),
            ],
        ),
    ]
