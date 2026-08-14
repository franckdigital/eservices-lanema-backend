from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projet', '0002_reunionprojet'),
    ]

    operations = [
        migrations.AddField(
            model_name='projet',
            name='est_strategique',
            field=models.BooleanField(default=False, help_text='Suivi dans le pilotage stratégique du tableau de bord DG', verbose_name='Projet stratégique'),
        ),
    ]
