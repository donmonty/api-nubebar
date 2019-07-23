from django.contrib.auth import get_user_model
from rest_framework import serializers
from core import models
from analytics import reporte_mermas as rm
import datetime
from django.utils.timezone import make_aware


"""
------------------------------------------------------------------------
Serializer para crear Reportes de Mermas
------------------------------------------------------------------------
"""
class ReporteMermasCreateSerializer(serializers.ModelSerializer):

    inspeccion = serializers.PrimaryKeyRelatedField(read_only=False, queryset=models.Inspeccion.objects.all())
    almacen = serializers.PrimaryKeyRelatedField(read_only=False, queryset=models.Almacen.objects.all())

    class Meta:
        model = models.ReporteMermas
        fields = (
            'id',
            'inspeccion',
            'almacen',
            'fecha_inicial',
            'fecha_final',
        )

    def create(self, validated_data):

        inspeccion = validated_data.get('inspeccion')
        #inspeccion_id = inspeccion.id

        # Primero checamos si la Inspeccion ya cuenta con un reporte de mermas
        # Si ya existe, notificamos al usuario
        if models.ReporteMermas.objects.filter(inspeccion=inspeccion).exists():
            raise serializers.ValidationError('Esta inspeccion ya cuenta con un reporte de mermas.')

        # Si no existe un reporte de mermas, lo creamos
        else:
            almacen = inspeccion.almacen
            inspecciones = models.Inspeccion.objects.filter(almacen=almacen).count()

            # Si hay mas de 1 inspeccion, tomamos las fechas de alta de las ultimas dos inspecciones
            if inspecciones > 1:
                inspeccion_previa = models.Inspeccion.objects.filter(almacen=almacen).order_by('-fecha_alta')[1:2]
                fecha_inicial = inspeccion_previa[0].fecha_alta
                fecha_final = inspeccion.fecha_alta

            # Si solo hay una inspeccion, entonces tomamos como fecha_inicial la fecha de registro de la primera botella registrada en el almacen
            else:
                # Checamos que el almacen tenga botellas registradas
                if models.Botella.objects.filter(almacen=almacen).exists():
                    primera_botella = models.Botella.objects.filter(almacen=almacen).order_by('fecha_registro')[:1]
                    fecha_inicial = primera_botella[0].fecha_registro.date()
                    fecha_final = inspeccion.fecha_alta

                else:
                    raise serializers.ValidationError('Este almacen no cuenta con botellas registradas.')

            # Ejecutamos el script del Reporte de Mermas
            consumos = rm.calcular_consumos(inspeccion, fecha_inicial, fecha_final)

            # Creamos la instancia de ReporteMermas
            reporte_mermas = models.ReporteMermas.objects.create(
                inspeccion=inspeccion,
                almacen=almacen,
                fecha_inicial=fecha_inicial,
                fecha_final=fecha_final
            )

            # Creamos las mermas del reporte
            for (ingrediente, consumo_ventas, consumo_real) in consumos:
                models.MermaIngrediente.objects.create(
                    ingrediente=ingrediente,
                    reporte=reporte_mermas,
                    fecha_inicial=fecha_inicial,
                    fecha_final=fecha_final,
                    consumo_ventas=consumo_ventas['consumo_ventas'],
                    consumo_real=consumo_real['consumo_real'],
                    almacen=almacen
                )

            # Retornamos la instancia de ReporteMermas
            return reporte_mermas 


"""
------------------------------------------------------------------------
Serializer para consultar el detalle de un MermaIngrediente
------------------------------------------------------------------------
"""
class MermaIngredienteReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.MermaIngrediente
        fields = (
            'id',
            'ingrediente',
            'consumo_ventas',
            'consumo_real',
            'merma',
            'porcentaje',
        )
        depth = 1


"""
------------------------------------------------------------------------
Serializer para consultar el detalle de un Reportes de Mermas, 
incluyendo sus mermas asociadas
------------------------------------------------------------------------
"""
class ReporteMermasDetalleSerializer(serializers.ModelSerializer):

    mermas_reporte = MermaIngredienteReadSerializer(many=True)

    class Meta:
        model = models.ReporteMermas
        fields = '__all__'
        depth = 1


"""
------------------------------------------------------------------------
Serializer para consultar la lista de reportes de mermas de un almacen
------------------------------------------------------------------------
"""
class ReporteMermasListSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ReporteMermas
        fields = (
            'id',
            'fecha_registro',
            'fecha_inicial',
            'fecha_final',
        )