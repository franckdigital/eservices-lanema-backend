from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DossierJuridique',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('type_dossier', models.CharField(choices=[('CONTRAT', 'Contrat'), ('CONTENTIEUX', 'Contentieux'), ('CONSULTATION', 'Consultation'), ('AVIS', 'Avis juridique'), ('DISCIPLINAIRE', 'Procédure disciplinaire')], max_length=20)),
                ('titre', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('statut', models.CharField(choices=[('OUVERT', 'Ouvert'), ('EN_COURS', 'En cours'), ('CLOTURE', 'Clôturé')], default='OUVERT', max_length=20)),
                ('date_ouverture', models.DateField(auto_now_add=True)),
                ('date_cloture', models.DateField(blank=True, null=True)),
                ('responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dossiers_juridiques', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_ouverture'],
            },
        ),
        migrations.CreateModel(
            name='Contrat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('intitule', models.CharField(max_length=255)),
                ('partie_prenante', models.CharField(blank=True, max_length=255)),
                ('statut', models.CharField(choices=[('BROUILLON', 'Brouillon'), ('VALIDE', 'Validé'), ('SIGNE', 'Signé'), ('RENOUVELE', 'Renouvelé'), ('EXPIRE', 'Expiré'), ('RESILIE', 'Résilié')], default='BROUILLON', max_length=20)),
                ('date_redaction', models.DateField(auto_now_add=True)),
                ('date_validation', models.DateField(blank=True, null=True)),
                ('date_signature', models.DateField(blank=True, null=True)),
                ('date_expiration', models.DateField(blank=True, null=True)),
                ('dossier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contrats', to='dg_juridique.dossierjuridique')),
            ],
            options={
                'ordering': ['-date_redaction'],
            },
        ),
        migrations.CreateModel(
            name='Contentieux',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('partie_adverse', models.CharField(blank=True, max_length=255)),
                ('objet', models.TextField(blank=True)),
                ('statut', models.CharField(choices=[('EN_COURS', 'En cours'), ('CLOTURE', 'Clôturé'), ('EVITE', 'Évité')], default='EN_COURS', max_length=20)),
                ('issue', models.CharField(blank=True, help_text='Favorable / défavorable / transaction', max_length=255)),
                ('date_ouverture', models.DateField(auto_now_add=True)),
                ('date_cloture', models.DateField(blank=True, null=True)),
                ('dossier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contentieux', to='dg_juridique.dossierjuridique')),
            ],
            options={
                'ordering': ['-date_ouverture'],
                'verbose_name_plural': 'Contentieux',
            },
        ),
        migrations.CreateModel(
            name='AvisJuridique',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sujet', models.CharField(max_length=255)),
                ('date_demande', models.DateField(auto_now_add=True)),
                ('date_reponse', models.DateField(blank=True, null=True)),
                ('reponse', models.TextField(blank=True)),
                ('demandeur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='avis_demandes', to=settings.AUTH_USER_MODEL)),
                ('dossier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='avis', to='dg_juridique.dossierjuridique')),
            ],
            options={
                'ordering': ['-date_demande'],
            },
        ),
        migrations.CreateModel(
            name='ProcedureDisciplinaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('motif', models.TextField()),
                ('statut', models.CharField(choices=[('OUVERTE', 'Ouverte'), ('EN_COURS', 'En cours'), ('CLOTUREE', 'Clôturée')], default='OUVERTE', max_length=20)),
                ('date_ouverture', models.DateField(auto_now_add=True)),
                ('date_cloture', models.DateField(blank=True, null=True)),
                ('agent_concerne', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='procedures_disciplinaires', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_ouverture'],
            },
        ),
    ]
