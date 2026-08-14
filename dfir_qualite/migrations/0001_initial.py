from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dfir_participants', '0001_initial'),
        ('dfir_formations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReclamationDFIR',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('date_reception', models.DateField(auto_now_add=True)),
                ('date_traitement', models.DateField(blank=True, null=True)),
                ('statut', models.CharField(choices=[('OUVERTE', 'Ouverte'), ('TRAITEE', 'Traitée')], default='OUVERTE', max_length=20)),
                ('entreprise', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reclamations_dfir', to='dfir_participants.entreprisedfir')),
                ('participant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reclamations_dfir', to='dfir_participants.participantdfir')),
            ],
            options={
                'ordering': ['-date_reception'],
            },
        ),
        migrations.CreateModel(
            name='AmeliorationProgramme',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('date_mise_en_oeuvre', models.DateTimeField(auto_now_add=True)),
                ('formation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ameliorations', to='dfir_formations.formation')),
            ],
            options={
                'ordering': ['-date_mise_en_oeuvre'],
            },
        ),
        migrations.CreateModel(
            name='AuditDFIR',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('type_audit', models.CharField(blank=True, max_length=100)),
                ('date_audit', models.DateField()),
                ('resultat', models.CharField(choices=[('CONFORME', 'Conforme'), ('NON_CONFORME', 'Non conforme'), ('CONFORME_AVEC_RESERVES', 'Conforme avec réserves')], default='CONFORME', max_length=25)),
            ],
            options={
                'ordering': ['-date_audit'],
            },
        ),
    ]
