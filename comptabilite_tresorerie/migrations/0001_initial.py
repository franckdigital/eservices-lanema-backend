from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='CompteBancaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_banque', models.CharField(max_length=255)),
                ('numero_compte', models.CharField(max_length=100, unique=True)),
                ('intitule', models.CharField(blank=True, max_length=255)),
                ('solde_initial', models.DecimalField(decimal_places=2, default=0, max_digits=16)),
                ('actif', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['nom_banque'],
            },
        ),
        migrations.CreateModel(
            name='MouvementBancaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_mouvement', models.CharField(choices=[('CREDIT', 'Crédit'), ('DEBIT', 'Débit')], max_length=10)),
                ('montant', models.DecimalField(decimal_places=2, default=0, max_digits=16)),
                ('date_mouvement', models.DateField()),
                ('libelle', models.CharField(blank=True, max_length=255)),
                ('rapproche', models.BooleanField(default=False)),
                ('compte', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mouvements', to='comptabilite_tresorerie.comptebancaire')),
            ],
            options={
                'ordering': ['-date_mouvement'],
            },
        ),
        migrations.CreateModel(
            name='RapprochementBancaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_rapprochement', models.DateField(auto_now_add=True)),
                ('solde_releve', models.DecimalField(decimal_places=2, default=0, max_digits=16)),
                ('solde_comptable', models.DecimalField(decimal_places=2, default=0, max_digits=16)),
                ('ecart', models.DecimalField(decimal_places=2, default=0, max_digits=16)),
                ('valide', models.BooleanField(default=False)),
                ('compte', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rapprochements', to='comptabilite_tresorerie.comptebancaire')),
            ],
            options={
                'ordering': ['-date_rapprochement'],
            },
        ),
    ]
