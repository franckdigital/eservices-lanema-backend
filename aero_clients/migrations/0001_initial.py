from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ClientAeronautique',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255, unique=True)),
                ('contact', models.CharField(blank=True, max_length=255)),
                ('actif', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='Aeronef',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('immatriculation', models.CharField(max_length=50, unique=True)),
                ('type_aeronef', models.CharField(blank=True, max_length=255)),
                ('statut', models.CharField(choices=[('EN_SERVICE', 'En service'), ('EN_MAINTENANCE', 'En maintenance'), ('HORS_SERVICE', 'Hors service')], default='EN_SERVICE', max_length=20)),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='aeronefs', to='aero_clients.clientaeronautique')),
            ],
            options={
                'ordering': ['immatriculation'],
            },
        ),
        migrations.CreateModel(
            name='ReclamationClientDAE',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('date_reception', models.DateField(auto_now_add=True)),
                ('date_traitement', models.DateField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('OUVERTE', 'Ouverte'), ('TRAITEE', 'Traitée')], default='OUVERTE', max_length=20)),
                ('note_satisfaction', models.PositiveSmallIntegerField(blank=True, help_text='Note sur 5', null=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reclamations', to='aero_clients.clientaeronautique')),
            ],
            options={
                'ordering': ['-date_reception'],
            },
        ),
    ]
