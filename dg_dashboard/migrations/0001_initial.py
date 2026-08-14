from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0113_absence_prolongee_tracking'),
    ]

    operations = [
        migrations.CreateModel(
            name='ObjectifStrategique',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('OBJECTIF', 'Objectif stratégique'), ('BUDGET', 'Exécution budgétaire'), ('DIGITALISATION', 'Digitalisation des processus')], default='OBJECTIF', max_length=20)),
                ('nom', models.CharField(max_length=255)),
                ('cible', models.DecimalField(decimal_places=2, help_text='Valeur cible (montant, %, nombre...)', max_digits=14)),
                ('valeur_actuelle', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('periode', models.CharField(blank=True, help_text='Ex: 2026, 2026-T1', max_length=50)),
                ('statut', models.CharField(choices=[('EN_COURS', 'En cours'), ('ATTEINT', 'Atteint'), ('NON_ATTEINT', 'Non atteint')], default='EN_COURS', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('direction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='objectifs_strategiques', to='core.direction')),
                ('service', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='objectifs_strategiques', to='core.service')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
