from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0113_absence_prolongee_tracking'),
    ]

    operations = [
        migrations.AddField(
            model_name='ficheagent',
            name='date_depart',
            field=models.DateField(blank=True, help_text="Date de depart de l'agent (demission, retraite, fin de contrat)", null=True),
        ),
        migrations.AddField(
            model_name='ficheagent',
            name='motif_depart',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
