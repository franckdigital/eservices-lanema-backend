from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dmct_clients', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InspectionDMCT',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('categorie', models.CharField(choices=[('INSPECTION', 'Inspection'), ('CONTROLE_TECHNIQUE', 'Contrôle technique')], default='INSPECTION', max_length=25)),
                ('type_controle', models.CharField(choices=[('PROGRAMME', 'Programmé'), ('INOPINE', 'Inopiné')], default='PROGRAMME', max_length=15)),
                ('date_inspection', models.DateField(auto_now_add=True)),
                ('date_cloture', models.DateField(blank=True, null=True)),
                ('conforme', models.BooleanField(blank=True, null=True)),
                ('sanction_emise', models.BooleanField(default=False)),
                ('observations', models.TextField(blank=True)),
                ('etablissement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inspections', to='dmct_clients.clientdmct')),
            ],
            options={
                'ordering': ['-date_inspection'],
            },
        ),
        migrations.CreateModel(
            name='ContreVisiteDMCT',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_contre_visite', models.DateField()),
                ('resultat', models.CharField(choices=[('CONFORME', 'Conforme'), ('NON_CONFORME', 'Non conforme')], default='CONFORME', max_length=15)),
                ('inspection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contre_visites', to='dmct_inspections.inspectiondmct')),
            ],
            options={
                'ordering': ['-date_contre_visite'],
            },
        ),
    ]
