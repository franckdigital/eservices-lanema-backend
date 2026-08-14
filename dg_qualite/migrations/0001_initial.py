from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0113_absence_prolongee_tracking'),
    ]

    operations = [
        migrations.CreateModel(
            name='NonConformiteQualite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField()),
                ('gravite', models.CharField(choices=[('MINEURE', 'Mineure'), ('MAJEURE', 'Majeure'), ('CRITIQUE', 'Critique')], default='MINEURE', max_length=20)),
                ('statut', models.CharField(choices=[('OUVERTE', 'Ouverte'), ('EN_TRAITEMENT', 'En traitement'), ('CLOTUREE', 'Clôturée')], default='OUVERTE', max_length=20)),
                ('date_detection', models.DateField(auto_now_add=True)),
                ('date_cloture', models.DateField(blank=True, null=True)),
                ('service_concerne', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='non_conformites_qualite', to='core.service')),
            ],
            options={
                'ordering': ['-date_detection'],
            },
        ),
        migrations.CreateModel(
            name='AuditQualite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('type_audit', models.CharField(choices=[('INTERNE', 'Interne'), ('EXTERNE', 'Externe'), ('ISO', 'Audit ISO')], default='INTERNE', max_length=20)),
                ('organisme', models.CharField(blank=True, max_length=255)),
                ('date_audit', models.DateField()),
                ('resultat', models.CharField(blank=True, choices=[('CONFORME', 'Conforme'), ('NON_CONFORME', 'Non conforme')], max_length=20)),
                ('observations', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['-date_audit'],
            },
        ),
        migrations.CreateModel(
            name='ReclamationClient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_nom', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('date_reception', models.DateField(auto_now_add=True)),
                ('date_traitement', models.DateField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('OUVERTE', 'Ouverte'), ('TRAITEE', 'Traitée')], default='OUVERTE', max_length=20)),
                ('note_satisfaction', models.PositiveSmallIntegerField(blank=True, help_text='Note sur 5, apres resolution', null=True)),
            ],
            options={
                'ordering': ['-date_reception'],
            },
        ),
        migrations.CreateModel(
            name='RevueDirection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_revue', models.DateField()),
                ('participants', models.TextField(blank=True)),
                ('decisions', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-date_revue'],
            },
        ),
        migrations.CreateModel(
            name='IndicateurQualite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255)),
                ('cible', models.DecimalField(decimal_places=2, max_digits=10)),
                ('valeur_actuelle', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('periode', models.CharField(blank=True, help_text='Ex: 2026-T1', max_length=50)),
            ],
            options={
                'ordering': ['nom'],
            },
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
                ('non_conformite', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actions', to='dg_qualite.nonconformitequalite')),
                ('responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='actions_qualite', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_planification'],
            },
        ),
    ]
