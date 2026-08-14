from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='prix_unitaire',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
    ]
