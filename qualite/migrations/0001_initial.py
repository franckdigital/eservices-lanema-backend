from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('demandes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TypeEchantillon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('actif', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='Echantillon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code_echantillon', models.CharField(max_length=100, unique=True)),
                ('designation', models.CharField(max_length=255)),
                ('type_echantillon', models.CharField(blank=True, default='', max_length=100)),
                ('quantite', models.CharField(blank=True, max_length=100)),
                ('statut', models.CharField(choices=[('RECEPTIONNE', 'Réceptionné'), ('EN_ATTENTE', 'En attente'), ('EN_ANALYSE', 'En analyse'), ('TERMINE', 'Terminé'), ('ARCHIVE', 'Archivé')], default='RECEPTIONNE', max_length=20)),
                ('date_reception', models.DateField()),
                ('emplacement_stockage', models.CharField(blank=True, max_length=255)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('demande', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='echantillons', to='demandes.demandedevis')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Essai',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=100, unique=True)),
                ('type_essai', models.CharField(blank=True, max_length=100)),
                ('statut', models.CharField(choices=[('EN_ATTENTE', 'En attente'), ('EN_COURS', 'En cours'), ('TERMINE', 'Terminé'), ('VALIDE', 'Validé'), ('ANNULE', 'Annulé')], default='EN_ATTENTE', max_length=20)),
                ('date_debut', models.DateField(blank=True, null=True)),
                ('date_fin_prevue', models.DateField(blank=True, null=True)),
                ('technicien', models.CharField(blank=True, max_length=255)),
                ('norme', models.CharField(blank=True, max_length=255)),
                ('observations', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('echantillon', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='essais', to='qualite.echantillon')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='NonConformite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=50, unique=True)),
                ('type_nc', models.CharField(choices=[('INTERNE', 'Interne'), ('EXTERNE', 'Externe')], default='INTERNE', max_length=20)),
                ('gravite', models.CharField(choices=[('MINEURE', 'Mineure'), ('MAJEURE', 'Majeure'), ('CRITIQUE', 'Critique')], default='MINEURE', max_length=20)),
                ('description', models.TextField()),
                ('date_creation', models.DateField(auto_now_add=True)),
                ('responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='non_conformites', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Audit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=100, unique=True)),
                ('type_audit', models.CharField(choices=[('INTERNE', 'Interne'), ('EXTERNE', 'Externe')], default='INTERNE', max_length=20)),
                ('organisme', models.CharField(blank=True, max_length=255)),
                ('date_audit', models.DateField()),
                ('resultat', models.CharField(blank=True, max_length=100)),
            ],
        ),
    ]
