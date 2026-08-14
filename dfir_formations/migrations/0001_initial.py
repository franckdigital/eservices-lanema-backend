from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dfir_formateurs', '0001_initial'),
        ('dfir_participants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Formation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('titre', models.CharField(max_length=255)),
                ('type_formation', models.CharField(choices=[('INTER_ENTREPRISE', 'Inter-entreprises'), ('INTRA_ENTREPRISE', 'Intra-entreprise'), ('SUR_MESURE', 'Sur mesure')], default='INTER_ENTREPRISE', max_length=20)),
                ('modalite', models.CharField(choices=[('PRESENTIEL', 'Présentiel'), ('EN_LIGNE', 'En ligne'), ('HYBRIDE', 'Hybride')], default='PRESENTIEL', max_length=15)),
                ('certifiante', models.BooleanField(default=False)),
                ('duree_heures', models.DecimalField(decimal_places=1, default=0, max_digits=6)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['titre'],
            },
        ),
        migrations.CreateModel(
            name='SessionFormation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_debut', models.DateTimeField()),
                ('date_fin_prevue', models.DateTimeField(blank=True, null=True)),
                ('date_fin_reelle', models.DateTimeField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('PLANIFIEE', 'Planifiée'), ('EN_COURS', 'En cours'), ('TERMINEE', 'Terminée'), ('ANNULEE', 'Annulée')], default='PLANIFIEE', max_length=20)),
                ('capacite_max', models.PositiveIntegerField(default=0)),
                ('evaluation_formateur', models.PositiveSmallIntegerField(blank=True, help_text='Note sur 5', null=True)),
                ('evaluation_session', models.PositiveSmallIntegerField(blank=True, help_text='Satisfaction sur 5', null=True)),
                ('cout_revient', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('entreprise', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sessions_formation', to='dfir_participants.entreprisedfir')),
                ('formateur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sessions', to='dfir_formateurs.formateurdfir')),
                ('formation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='dfir_formations.formation')),
            ],
            options={
                'ordering': ['-date_debut'],
            },
        ),
        migrations.CreateModel(
            name='InscriptionParticipant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('present', models.BooleanField(blank=True, null=True)),
                ('reussite', models.BooleanField(blank=True, null=True)),
                ('certifie', models.BooleanField(default=False)),
                ('abandon', models.BooleanField(default=False)),
                ('participant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inscriptions', to='dfir_participants.participantdfir')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inscriptions', to='dfir_formations.sessionformation')),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='SupportPedagogique',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(max_length=255)),
                ('type_contenu', models.CharField(choices=[('DOCUMENT', 'Document'), ('VIDEO', 'Vidéo'), ('QUIZ', 'Quiz'), ('AUTRE', 'Autre')], default='DOCUMENT', max_length=20)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_derniere_maj', models.DateTimeField(blank=True, null=True)),
                ('nombre_telechargements', models.PositiveIntegerField(default=0)),
                ('formation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supports', to='dfir_formations.formation')),
            ],
            options={
                'ordering': ['-date_creation'],
            },
        ),
    ]
