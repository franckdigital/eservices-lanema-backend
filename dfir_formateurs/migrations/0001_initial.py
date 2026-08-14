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
            name='FormateurDFIR',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('specialite', models.CharField(blank=True, max_length=255)),
                ('date_qualification', models.DateField()),
                ('disponible', models.BooleanField(default=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='formateur_dfir', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date_qualification'],
            },
        ),
    ]
