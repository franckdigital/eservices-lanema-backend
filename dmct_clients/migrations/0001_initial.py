from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ClientDMCT',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255, unique=True)),
                ('secteur_activite', models.CharField(choices=[('COMMERCE', 'Commerce'), ('INDUSTRIE', 'Industrie'), ('SANTE', 'Santé'), ('LABORATOIRE', 'Laboratoire'), ('AUTRE', 'Autre')], default='AUTRE', max_length=20)),
                ('contact', models.CharField(blank=True, max_length=255)),
                ('actif', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='ReclamationClientDMCT',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('date_reception', models.DateField(auto_now_add=True)),
                ('date_traitement', models.DateField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('OUVERTE', 'Ouverte'), ('TRAITEE', 'Traitée')], default='OUVERTE', max_length=20)),
                ('note_satisfaction', models.PositiveSmallIntegerField(blank=True, help_text='Note sur 5', null=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reclamations', to='dmct_clients.clientdmct')),
            ],
            options={
                'ordering': ['-date_reception'],
            },
        ),
    ]
