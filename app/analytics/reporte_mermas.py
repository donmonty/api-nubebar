from django.db.models import F, Q, QuerySet, Avg, Count, Sum, Subquery, OuterRef, Exists, Func, ExpressionWrapper, DecimalField, Case, When
from core import models
from decimal import Decimal

import datetime
from django.utils.timezone import make_aware
from django.core.exceptions import ObjectDoesNotExist


def calcular_consumos(inspeccion, fecha_inicial, fecha_final):

    # Tomamos el almacen
    almacen = inspeccion.almacen

    # Tomamos los ItemsInspeccion de la Inspeccion actual
    items_inspeccion = inspeccion.items_inspeccionados.all()

    # Excluimos las Botellas cuyo ItemInspecion.peso_botella = 'None'
    items_inspeccion_peso_none = items_inspeccion.filter(peso_botella=None)
    items_inspeccion.exclude(peso_botella=None)

    # Generamos un Queryset con los 'botella__id'
    items_inspeccion = items_inspeccion.values('botella__id')

    # Seleccionamos todas las botellas del almacén
    botellas = models.Botella.objects.filter(almacen=almacen)

    """
    -------------------------------------------------------------------------
    Snippets útiles

    -------------------------------------------------------------------------
    """
    # Subquery: Selección de 'peso_botella' de la penúltima inspeccion
    sq_peso_penultima_inspeccion = Subquery(models.ItemInspeccion.objects
                                        .filter(botella=OuterRef('pk'))
                                        .order_by('-timestamp_inspeccion')
                                        .values('peso_botella')[1:2]
                                    )
    # Subquery: Selección de 'peso_botella' de la última inspeccion
    sq_peso_ultima_inspeccion = Subquery(models.ItemInspeccion.objects
                                    .filter(botella=OuterRef('pk'))
                                    .order_by('-timestamp_inspeccion')
                                    .values('peso_botella')[:1]
                                )

    # Lista de ingredientes presentes en la Inspeccion
    items_inspeccion_2 = inspeccion.items_inspeccionados.all()
    items_inspeccion_2 = items_inspeccion_2.values('botella__producto__ingrediente__id')
    ingredientes_inspeccion = models.Ingrediente.objects.filter(id__in=items_inspeccion_2)

    #----------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------

    # Seleccionamos todas las botellas cuyo ingrediente sea parte de la lista de ingredientes a inspeccionar
    botellas = botellas.filter(producto__ingrediente__in=ingredientes_inspeccion)

    # Agregamos 'num_inspecciones'
    botellas_num_inspecciones = botellas.annotate(num_inspecciones=Count('inspecciones_botella'))

    #print('::: BOTELLAS CON INGREDIENTES A INSPECCIONAR :::')
    #print(botellas_num_inspecciones.values())


    #----------------------------------------------------------------------
    # Agregamos 'peso_anterior'
    botellas_peso_anterior = botellas_num_inspecciones.annotate(
        peso_anterior=Case(
            # Botellas presentas en la la inspección y con múltiples inspecciones
            When(Q(id__in=items_inspeccion) & Q(num_inspecciones__gt=1), then=sq_peso_penultima_inspeccion),
            # Botellas presentes en la Inspección con 1 inspección
            When(Q(id__in=items_inspeccion) & Q(num_inspecciones=1), then=F('peso_inicial')),
            # Botellas VACIAS pero cuyo ingrediente es parte de los ingredientes a inspeccionar
            # y que se ingresaron y consumieron entre la inspección previa y la actual
            When(Q(estado='0') & Q(fecha_registro__gte=fecha_inicial, fecha_registro__lte=fecha_final), then=F('peso_inicial')),
            # Botellas VACIAS cuyo ingrediente es parte de los ingredientes a inspeccionar,
            # que se consumieron entre ambas inspecciones, pero que ya estaban registradas desde antes y tienen minimo 1 inspeccion
            When(Q(estado='0') & Q(fecha_baja__gte=fecha_inicial, fecha_baja__lte=fecha_final, fecha_registro__lte=fecha_inicial) & Q(num_inspecciones__gt=0), then=sq_peso_ultima_inspeccion),
            # Botellas VACIAS cuyo ingrediente es parte de los ingredientes a inspeccionar,
            # que se consumieron entre ambas inspecciones, pero que ya estaban registradas desde antes y tienen cero inspecciones
            When(Q(estado='0') & Q(fecha_baja__gte=fecha_inicial, fecha_baja__lte=fecha_final, fecha_registro__lte=fecha_inicial) & Q(num_inspecciones=0), then=F('peso_inicial'))
        )
    )

    #print('::: BOTELLAS - PESO ANTERIOR :::')
    #print(botellas_peso_anterior.values('peso_inicial', 'peso_actual', 'peso_anterior'))


    #----------------------------------------------------------------------
    # Seleccionamos unicamente las botellas cuyo 'peso_anterior' no sea None
    # O lo que es lo mismo, excluimos del queryset todas aquellas botellas cuyo 'peso_anterior' sea None
    botellas_peso_anterior_ok = botellas_peso_anterior.exclude(peso_anterior=None)

    #print('::: PESO ANTERIOR OK :::')
    #print(botellas_peso_anterior_ok.values('folio', 'ingrediente', 'num_inspecciones', 'peso_inicial', 'peso_actual', 'peso_anterior'))


    #----------------------------------------------------------------------
    # Agregamos un campo 'dif_peso'
    dif_peso_botellas = botellas_peso_anterior_ok.annotate(
        dif_peso=F('peso_anterior') - F('peso_actual')
    )

    #print('::: DIF PESO :::')
    #print(dif_peso_botellas.values('folio', 'ingrediente', 'num_inspecciones', 'peso_inicial', 'peso_anterior', 'peso_actual', 'dif_peso'))


    #----------------------------------------------------------------------
    # Agregamos campo "densidad"
    densidad_botellas = dif_peso_botellas.annotate(
        densidad=ExpressionWrapper(
            2 - F('producto__ingrediente__factor_peso'),
            output_field=DecimalField()
        )
    )

    #print('::: DENSIDAD :::')
    #print(densidad_botellas.values('folio', 'ingrediente', 'num_inspecciones', 'peso_inicial', 'peso_anterior', 'peso_actual', 'dif_peso', 'densidad'))


    #----------------------------------------------------------------------
    # Agregamos un campo con el consumo en mililitros
    consumo_botellas = densidad_botellas.annotate(
        consumo_ml=ExpressionWrapper(
            (F('dif_peso') * F('densidad')),
            output_field=DecimalField()
        )
    )

    #print('::: CONSUMO :::')
    #print(consumo_botellas.values('folio', 'ingrediente', 'num_inspecciones', 'peso_inicial', 'peso_anterior', 'peso_actual', 'dif_peso', 'densidad', 'consumo_ml'))

    """
    -----------------------------------------------------------------
    Calculamos el CONSUMO DE VENTAS y CONSUMO REAL por ingrediente
    -----------------------------------------------------------------
    """
    consumos = []
    for ingrediente in ingredientes_inspeccion:
        # Sumamos el consumo real por ingrediente
        botellas_ingrediente = consumo_botellas.filter(producto__ingrediente__id=ingrediente.id)
        consumo_real = botellas_ingrediente.aggregate(consumo_real=Sum('consumo_ml'))

        # Sumamos el consumo de ventas por ingrediente
        consumos_recetas = models.ConsumoRecetaVendida.objects.filter(
            ingrediente=ingrediente,
            fecha__gte=fecha_inicial,
            fecha__lte=fecha_final,
            venta__caja__almacen=almacen
        )
        consumo_ventas = consumos_recetas.aggregate(consumo_ventas=Sum('volumen'))

        # Consolidamos los ingredientes, su consumo de ventas y consumo real en una lista
        ingrediente_consumo = (ingrediente, consumo_ventas, consumo_real)
        consumos.append(ingrediente_consumo)


    #print('::: CONSUMO INGREDIENTES :::')
    #print(consumos)

    return consumos


"""
-----------------------------------------------------------------------------------
Esta funcion retorna el las ventas asociadas a una merma y su detalle
-----------------------------------------------------------------------------------
"""
def get_ventas_merma(merma_id):

    # Tomamos el ingrediente a analizar de la merma
    try:
        merma = models.MermaIngrediente.objects.get(id=merma_id)

    # Si la merma no existe, retornamos un status de error
    except ObjectDoesNotExist:
        data = {
            'status': '0',
            'mensaje': 'La merma solicitada no existe.'
        }
        return data

    else: 
        ingrediente = merma.ingrediente

        # Tomamos las ventas asociadas al ingrediente de la MermaIngrediente
        consumos = models.ConsumoRecetaVendida.objects.filter(
            ingrediente=ingrediente,
            fecha__gte=merma.fecha_inicial,
            fecha__lte=merma.fecha_final,
            venta__caja__almacen=merma.almacen
        )

        consumos = consumos.values('venta')

        ventas = models.Venta.objects.filter(id__in=consumos)

        # Agregamos el volumen del ingrediente especificado en la receta del trago
        sq_volumen_receta = Subquery(models.IngredienteReceta.objects.filter(receta=OuterRef('receta'), ingrediente=ingrediente).values('volumen'))
        ventas_volumen_receta = ventas.annotate(volumen_receta=sq_volumen_receta)

        # Agregamos el volumen vendido total
        ventas_volumen_vendido = ventas_volumen_receta.annotate(volumen_vendido=F('unidades') * F('volumen_receta'))

        # Convertimos el queryset en una lista de objectos
        lista_ventas = list(ventas_volumen_vendido.values('id', 'receta__nombre', 'unidades', 'receta__codigo_pos', 'fecha', 'caja__nombre', 'importe', 'volumen_receta', 'volumen_vendido'))

        # Convertimos las fechas a formato legible
        for venta in lista_ventas:
            venta['fecha'] = venta['fecha'].strftime("%d/%m/%Y")

        # Guardamos la info en un objecto, incluyendo el nombre del ingrediente y el status de exito
        data = {
            'status': '1',
            'ingrediente': merma.ingrediente.nombre,
            'detalle_ventas': lista_ventas
        }

        return data