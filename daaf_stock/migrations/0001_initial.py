from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ArticleStock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(max_length=100, unique=True)),
                ('designation', models.CharField(max_length=255)),
                ('categorie', models.CharField(blank=True, max_length=100)),
                ('unite', models.CharField(default='UNITE', max_length=50)),
                ('quantite_stock', models.FloatField(default=0)),
                ('seuil_alerte', models.FloatField(default=0)),
                ('prix_unitaire', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
            ],
            options={
                'ordering': ['designation'],
            },
        ),
        migrations.CreateModel(
            name='LotStock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_lot', models.CharField(blank=True, max_length=100)),
                ('quantite', models.FloatField(default=0)),
                ('date_peremption', models.DateField(blank=True, null=True)),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lots', to='daaf_stock.articlestock')),
            ],
            options={
                'ordering': ['date_peremption'],
            },
        ),
        migrations.CreateModel(
            name='MouvementStockAdmin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('ENTREE', 'Entrée'), ('SORTIE', 'Sortie')], max_length=10)),
                ('quantite', models.FloatField(default=0)),
                ('date_mouvement', models.DateTimeField(auto_now_add=True)),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mouvements', to='daaf_stock.articlestock')),
            ],
            options={
                'ordering': ['-date_mouvement'],
            },
        ),
    ]
