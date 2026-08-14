from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('comptabilite_pieces', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompteComptable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(help_text='Ex: 512000', max_length=20, unique=True)),
                ('intitule', models.CharField(max_length=255)),
                ('type_compte', models.CharField(choices=[('ACTIF', 'Actif'), ('PASSIF', 'Passif'), ('CHARGE', 'Charge'), ('PRODUIT', 'Produit')], default='ACTIF', max_length=10)),
            ],
            options={
                'ordering': ['numero'],
            },
        ),
        migrations.CreateModel(
            name='JournalComptable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='Ex: BQ, CA, VE, AC, OD', max_length=10, unique=True)),
                ('libelle', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='EcritureComptable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.CharField(max_length=50, unique=True)),
                ('date_ecriture', models.DateField(auto_now_add=True)),
                ('montant', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('libelle', models.CharField(blank=True, max_length=255)),
                ('valide', models.BooleanField(default=False)),
                ('compte_credit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ecritures_credit', to='comptabilite_ecritures.comptecomptable')),
                ('compte_debit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ecritures_debit', to='comptabilite_ecritures.comptecomptable')),
                ('journal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ecritures', to='comptabilite_ecritures.journalcomptable')),
                ('piece', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ecritures', to='comptabilite_pieces.piececomptable')),
            ],
            options={
                'ordering': ['-date_ecriture'],
            },
        ),
    ]
