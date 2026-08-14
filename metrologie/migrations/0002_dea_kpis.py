from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('metrologie', '0001_initial'),
        ('laboratoires', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipement',
            name='laboratoire',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='equipements', to='laboratoires.laboratoire'),
        ),
        migrations.CreateModel(
            name='PanneEquipement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_panne', models.DateField(auto_now_add=True)),
                ('date_reparation', models.DateField(blank=True, null=True)),
                ('cout', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('description', models.TextField(blank=True)),
                ('equipement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pannes', to='metrologie.equipement')),
            ],
            options={
                'ordering': ['-date_panne'],
            },
        ),
        migrations.CreateModel(
            name='MaintenancePreventive',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_prevue', models.DateField()),
                ('date_realisee', models.DateField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('PLANIFIEE', 'Planifiée'), ('REALISEE', 'Réalisée'), ('REPORTEE', 'Reportée')], default='PLANIFIEE', max_length=20)),
                ('reussie', models.BooleanField(blank=True, null=True)),
                ('observations', models.TextField(blank=True)),
                ('equipement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maintenances_preventives', to='metrologie.equipement')),
            ],
            options={
                'ordering': ['-date_prevue'],
            },
        ),
    ]
