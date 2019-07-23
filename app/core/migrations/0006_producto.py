# Generated by Django 2.1.7 on 2019-03-26 23:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_consumorecetavendida'),
    ]

    operations = [
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('folio', models.CharField(max_length=12)),
                ('tipo_marbete', models.CharField(blank=True, max_length=255)),
                ('fecha_elaboracion_marbete', models.CharField(blank=True, max_length=255)),
                ('lote_produccion_marbete', models.CharField(blank=True, max_length=255)),
                ('url', models.URLField(blank=True, max_length=255)),
                ('nombre_marca', models.CharField(blank=True, max_length=255)),
                ('tipo_producto', models.CharField(blank=True, max_length=255)),
                ('graduacion_alcoholica', models.CharField(blank=True, max_length=255)),
                ('capacidad', models.IntegerField(blank=True, null=True)),
                ('origen_del_producto', models.CharField(blank=True, max_length=255)),
                ('fecha_importacion', models.CharField(blank=True, max_length=255)),
                ('nombre_fabricante', models.CharField(blank=True, max_length=255)),
                ('rfc_fabricante', models.CharField(blank=True, max_length=255)),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('peso_cristal', models.IntegerField(blank=True, null=True)),
                ('precio_unitario', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('ingrediente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='productos', to='core.Ingrediente')),
            ],
        ),
    ]