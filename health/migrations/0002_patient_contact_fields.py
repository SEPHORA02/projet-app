from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('health', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='phone_number',
            field=models.CharField(blank=True, max_length=20, verbose_name='Numéro'),
        ),
        migrations.AddField(
            model_name='patient',
            name='sex',
            field=models.CharField(
                blank=True,
                choices=[('H', 'Homme'), ('F', 'Femme'), ('A', 'Autre')],
                max_length=1,
                verbose_name='Sexe',
            ),
        ),
        migrations.AlterField(
            model_name='patient',
            name='age',
            field=models.IntegerField(default=18, verbose_name='Âge'),
        ),
        migrations.AlterField(
            model_name='patient',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Créé le'),
        ),
        migrations.AlterField(
            model_name='patient',
            name='location',
            field=models.CharField(default="Abidjan, Côte d'Ivoire", max_length=200, verbose_name='Localisation'),
        ),
        migrations.AlterField(
            model_name='patient',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Mis à jour le'),
        ),
        migrations.AlterField(
            model_name='patient',
            name='user',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='profil_patient',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Compte utilisateur',
            ),
        ),
    ]

