from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dfir_participants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MissionAssistance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('date_demande', models.DateTimeField(auto_now_add=True)),
                ('date_debut', models.DateTimeField(blank=True, null=True)),
                ('date_fin', models.DateTimeField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('EN_COURS', 'En cours'), ('TERMINEE', 'Terminée')], default='EN_COURS', max_length=20)),
                ('diagnostic_realise', models.BooleanField(default=False)),
                ('plan_amelioration_elabore', models.BooleanField(default=False)),
                ('satisfaction', models.PositiveSmallIntegerField(blank=True, help_text='Note sur 5', null=True)),
                ('entreprise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='missions_assistance', to='dfir_participants.entreprisedfir')),
            ],
            options={
                'ordering': ['-date_demande'],
            },
        ),
    ]
