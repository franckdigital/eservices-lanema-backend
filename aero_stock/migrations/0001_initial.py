from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='PieceRechange',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=50, unique=True)),
                ('designation', models.CharField(max_length=255)),
                ('categorie', models.CharField(blank=True, max_length=100)),
                ('quantite_stock', models.PositiveIntegerField(default=0)),
                ('seuil_alerte', models.PositiveIntegerField(default=0)),
                ('prix_unitaire', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('est_critique', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['designation'],
            },
        ),
        migrations.CreateModel(
            name='MouvementPieceRechange',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_mouvement', models.CharField(choices=[('ENTREE', 'Entrée'), ('SORTIE', 'Sortie')], max_length=10)),
                ('quantite', models.PositiveIntegerField()),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('piece', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mouvements', to='aero_stock.piecerechange')),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
    ]
