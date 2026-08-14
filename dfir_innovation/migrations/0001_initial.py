from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ProjetInnovation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('titre', models.CharField(max_length=255)),
                ('date_lancement', models.DateTimeField(auto_now_add=True)),
                ('date_fin_prevue', models.DateField(blank=True, null=True)),
                ('date_fin_reelle', models.DateField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('EN_COURS', 'En cours'), ('ACHEVE', 'Achevé'), ('ABANDONNE', 'Abandonné')], default='EN_COURS', max_length=20)),
                ('methode_developpee', models.BooleanField(default=False)),
                ('prototype_realise', models.BooleanField(default=False)),
                ('mis_en_oeuvre', models.BooleanField(default=False)),
                ('partenariat', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-date_lancement'],
            },
        ),
    ]
