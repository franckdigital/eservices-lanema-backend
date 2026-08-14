from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dfir_participants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjetRecherche',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('titre', models.CharField(max_length=255)),
                ('type_projet', models.CharField(choices=[('ETUDE_TECHNIQUE', 'Étude technique'), ('ETUDE_ENTREPRISE', 'Étude pour entreprise'), ('RECHERCHE', 'Recherche')], default='ETUDE_TECHNIQUE', max_length=20)),
                ('date_debut', models.DateTimeField(auto_now_add=True)),
                ('date_fin_prevue', models.DateField(blank=True, null=True)),
                ('date_fin_reelle', models.DateField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('EN_COURS', 'En cours'), ('ACHEVE', 'Achevé'), ('ABANDONNE', 'Abandonné')], default='EN_COURS', max_length=20)),
                ('entreprise', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='projets_recherche', to='dfir_participants.entreprisedfir')),
            ],
            options={
                'ordering': ['-date_debut'],
            },
        ),
        migrations.CreateModel(
            name='PublicationScientifique',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(max_length=255)),
                ('date_publication', models.DateField()),
                ('projet', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='publications', to='dfir_recherche.projetrecherche')),
            ],
            options={
                'ordering': ['-date_publication'],
            },
        ),
        migrations.CreateModel(
            name='RapportRecherche',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(max_length=255)),
                ('date_creation', models.DateField(auto_now_add=True)),
                ('valide', models.BooleanField(default=False)),
                ('date_validation', models.DateField(blank=True, null=True)),
                ('projet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rapports', to='dfir_recherche.projetrecherche')),
            ],
            options={
                'ordering': ['-date_creation'],
            },
        ),
        migrations.CreateModel(
            name='RecommandationRecherche',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('appliquee', models.BooleanField(default=False)),
                ('rapport', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommandations', to='dfir_recherche.rapportrecherche')),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='CollaborationRecherche',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_partenaire', models.CharField(max_length=255)),
                ('type_partenaire', models.CharField(choices=[('UNIVERSITE', 'Université'), ('CENTRE_RECHERCHE', 'Centre de recherche'), ('AUTRE', 'Autre')], default='UNIVERSITE', max_length=20)),
                ('date_debut', models.DateField()),
            ],
            options={
                'ordering': ['-date_debut'],
            },
        ),
    ]
