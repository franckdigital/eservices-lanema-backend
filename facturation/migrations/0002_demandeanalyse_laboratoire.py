from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('facturation', '0001_initial'),
        ('laboratoires', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='demandeanalyse',
            name='laboratoire',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='demandes_analyses', to='laboratoires.laboratoire'),
        ),
    ]
