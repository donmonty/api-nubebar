# Generated by Django 2.1.9 on 2019-08-27 23:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_auto_20190826_2116'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='peso_nueva',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
