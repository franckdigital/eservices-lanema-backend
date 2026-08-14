from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clients', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReclamationClient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('date_reception', models.DateField(auto_now_add=True)),
                ('date_traitement', models.DateField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('OUVERTE', 'Ouverte'), ('TRAITEE', 'Traitée')], default='OUVERTE', max_length=20)),
                ('note_satisfaction', models.PositiveSmallIntegerField(blank=True, help_text='Note sur 5, apres resolution', null=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reclamations_labo', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_reception'],
            },
        ),
    ]
