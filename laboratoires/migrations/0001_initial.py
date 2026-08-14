from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Laboratoire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=255, unique=True)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('capacite_journaliere', models.PositiveIntegerField(default=0, help_text="Nombre d'essais/jour theorique, pour le calcul de la capacite d'utilisation")),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('responsable', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='laboratoires_diriges', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['nom'],
            },
        ),
    ]
