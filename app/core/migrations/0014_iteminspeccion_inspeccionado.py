# Generated by Django 2.1.8 on 2019-05-15 16:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_auto_20190506_1552'),
    ]

    operations = [
        migrations.AddField(
            model_name='iteminspeccion',
            name='inspeccionado',
            field=models.BooleanField(default=False),
        ),
    ]