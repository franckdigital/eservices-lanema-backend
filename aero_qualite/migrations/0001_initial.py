from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('aero_maintenance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NonConformiteDAE',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('gravite', models.CharField(choices=[('MINEURE', 'Mineure'), ('MAJEURE', 'Majeure'), ('CRITIQUE', 'Critique')], default='MINEURE', max_length=10)),
                ('description', models.TextField()),
                ('statut', models.CharField(choices=[('OUVERTE', 'Ouverte'), ('EN_COURS', 'En cours de traitement'), ('CLOTUREE', 'Clôturée')], default='OUVERTE', max_length=10)),
                ('date_creation', models.DateField(auto_now_add=True)),
                ('ordre_travail', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='non_conformites', to='aero_maintenance.ordretravail')),
                ('responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='non_conformites_dae', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_creation'],
            },
        ),
        migrations.CreateModel(
            name='ActionCorrectiveDAE',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('statut', models.CharField(choices=[('PLANIFIEE', 'Planifiée'), ('EN_COURS', 'En cours'), ('REALISEE', 'Réalisée')], default='PLANIFIEE', max_length=10)),
                ('date_prevue', models.DateField(blank=True, null=True)),
                ('date_realisation', models.DateField(blank=True, null=True)),
                ('non_conformite', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actions_correctives', to='aero_qualite.nonconformitedae')),
                ('responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actions_correctives_dae', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_prevue'],
            },
        ),
        migrations.CreateModel(
            name='AuditQualiteDAE',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('type_audit', models.CharField(blank=True, max_length=100)),
                ('date_audit', models.DateField()),
                ('resultat', models.CharField(choices=[('CONFORME', 'Conforme'), ('NON_CONFORME', 'Non conforme'), ('CONFORME_AVEC_RESERVES', 'Conforme avec réserves')], default='CONFORME', max_length=25)),
            ],
            options={
                'ordering': ['-date_audit'],
            },
        ),
    ]
