from django.db.models import F, Q, QuerySet, Avg, Count, Sum, Subquery, OuterRef, Exists, Func, ExpressionWrapper, DecimalField, IntegerField, Case, When
from core import models
from decimal import Decimal, ROUND_UP

import datetime
import math
import json
import pandas as pd
import numpy as np

from django.utils.timezone import make_aware
from django.core.exceptions import ObjectDoesNotExist


def calcular_restock(sucursal_id):

    """
    ------------------------------------------------------------
    Calcula el restock por producto para una sucursal. Utiliza
    subqueries avanzados para optimizar el desempeño.
    ------------------------------------------------------------
    """

    # Tomamos la sucursal
    sucursal = models.Sucursal.objects.get(id=sucursal_id)

    # Definimos las fechas del reporte
    fecha_final = datetime.date.today()
    fecha_inicial = fecha_final - datetime.timedelta(days=7)

    # Tomamos los Productos asociados a la sucursal
    botellas_sucursal = models.Botella.objects.filter(sucursal=sucursal).values('producto').distinct()
    productos_sucursal = models.Producto.objects.filter(id__in=botellas_sucursal).order_by('nombre_marca')

    """
    --------------------------------------------------------------------
    Tomamos las botellas relevantes para el periodo del análisis:

    - Las que ya estaban antes y no han salido
    - Las que ya estaban antes y salieron
    - Las que entraron y salieron en el periodo
    - Las que entraron en el periodo y no han salido

    --------------------------------------------------------------------
    """
    
    botellas_periodo = botellas_sucursal.filter(

        Q(fecha_registro__lte=fecha_inicial, fecha_baja=None) |
        Q(fecha_registro__lte=fecha_inicial, fecha_baja__gte=fecha_inicial, fecha_baja__lte=fecha_final) |
        Q(fecha_registro__gte=fecha_inicial, fecha_baja__lte=fecha_final) |
        Q(fecha_registro__gte=fecha_inicial, fecha_baja=None)
    )

    """
    --------------------------------------------------------
    SUBQUERIES UTILES
    --------------------------------------------------------
    """

    # Subquery: Selección de 'peso_botella' de la primera inspeccion del periodo analizado
    query_peso_primera_inspeccion = (
        
        models.ItemInspeccion.objects
            .filter(botella=OuterRef('pk'), timestamp_inspeccion__gte=fecha_inicial, timestamp_inspeccion__lte=fecha_final)
            .order_by('timestamp_inspeccion')
            #.exclude(peso_botella=None)
            .values('peso_botella')[:1]
    )
    #-------------------------------------------------------------------------------------------

    # Query: El peso de la botella en la primera inspeccion del intervalo analizado, pero se excluyen inspecciones con 'peso_botella' = None
    query_peso_inspeccion_inicial = (

        models.ItemInspeccion.objects
            .filter(botella=OuterRef('pk'), timestamp_inspeccion__gte=fecha_inicial, timestamp_inspeccion__lte=fecha_final)
            .order_by('timestamp_inspeccion')
            .exclude(peso_botella=None)
            .values('peso_botella')[:1]

    )
    #-------------------------------------------------------------------------------------------

    # Subquery: La cantidad de inspecciones cuyo 'peso_botella' está OK (es decir, distinto a None)
    query_peso_ok_count = (

        models.ItemInspeccion.objects
            .filter(botella=OuterRef('pk'), timestamp_inspeccion__gte=fecha_inicial, timestamp_inspeccion__lte=fecha_final)
            .exclude(peso_botella=None)
            .values('botella__pk')
            .annotate(inspecciones_peso_ok_count=Count('id'))
            .values('inspecciones_peso_ok_count')

    )
    #-------------------------------------------------------------------------------------------

    # Subquery: Cantidad de inspecciones por botella que caen dentro del periodo de análisis
    query_inspecciones_periodo = (

        models.ItemInspeccion.objects
            .filter(botella=OuterRef('pk'), timestamp_inspeccion__gte=fecha_inicial, timestamp_inspeccion__lte=fecha_final)
            .values('botella__pk')
            .annotate(inspecciones_periodo=Count('id'))
            .values('inspecciones_periodo')
    )
    #-------------------------------------------------------------------------------------------

    #----------------------------------------------------------------------
    # Agregamos el 'nombre_marca' del Producto
    botellas_periodo = botellas_periodo.annotate(nombre_producto=F('producto__nombre_marca'))
    #print('::: BOTELLAS - NOMBRE PRODUCTO :::')
    #print(botellas_periodo.values('folio', 'nombre_producto'))
   
    #----------------------------------------------------------------------
    # Agregamos el numero de inspecciones por botella
    botellas_periodo = botellas_periodo.annotate(num_inspecciones=Count('inspecciones_botella'))
    #print('::: BOTELLAS - NUMERO DE INSPECCIONES :::')
    #print(botellas_periodo.values('folio', 'num_inspecciones'))

    #----------------------------------------------------------------------
    # Agregamos el peso_inicio_7
    #botellas_peso_inicio_7 = botellas_periodo.annotate(peso_inicio_7=ExpressionWrapper(sq_peso_inspeccion_inicial, output_field=IntegerField()))
    botellas_peso_inicio_7 = botellas_periodo.annotate(peso_inicio_7=Subquery(query_peso_inspeccion_inicial, output_field=IntegerField()))
    #print('::: BOTELLAS - PESO INICIO 7 :::')
    #print(botellas_peso_inicio_7.values('folio', 'peso_inicio_7'))

    #----------------------------------------------------------------------
    # Agregamos 'inspecciones_periodo': El numero de inspecciones que que son parte del periodo de análisis
    #botellas_inspecciones_ok = botellas_periodo.annotate(inspecciones_ok_count=ExpressionWrapper(sq_inspeccion_inside, output_field=IntegerField()))
    botellas_inspecciones_periodo = botellas_peso_inicio_7.annotate(inspecciones_periodo=Subquery(query_inspecciones_periodo, output_field=IntegerField()))

    #print('::: BOTELLAS - INSPECCIONES PERIODO :::')
    #print(botellas_inspecciones_periodo.values('folio', 'producto__ingrediente__nombre', 'inspecciones_periodo'))

    #----------------------------------------------------------------------
    # Agregamos 'inspecciones_peso_ok_count': El numero de inspecciones con 'peso_botella' != None
    botellas_inspecciones_peso_ok = botellas_inspecciones_periodo.annotate(inspecciones_peso_ok_count=Subquery(query_peso_ok_count, output_field=IntegerField()))

    #print('::: BOTELLAS - PESO OK COUNT :::')
    #print(botellas_inspecciones_peso_ok.values('folio', 'producto__ingrediente__nombre', 'inspecciones_peso_ok_count'))

    #----------------------------------------------------------------------
    # Agregamos el peso de la última inspección para más adelante checar si es None
    botellas_peso_primera_inspeccion = botellas_inspecciones_peso_ok.annotate(peso_primera_inspeccion=Subquery(query_peso_primera_inspeccion, output_field=IntegerField()))

    #print('::: BOTELLAS - PESO PRIMERA INSPECCION :::')
    #print(botellas_peso_primera_inspeccion.values('folio', 'producto__ingrediente__nombre', 'peso_primera_inspeccion'))

    #----------------------------------------------------------------------
    # Agregamos el 'peso_inspeccion_inicial'
    botellas_peso_inspeccion_inicial = botellas_peso_primera_inspeccion.annotate(
        peso_inspeccion_inicial=Case(

            # CASO 1: La botella tiene más de 1 inspeccion, pero ninguna ocurrió en el periodo de análisis
            When(Q(num_inspecciones__gt=1) & Q(inspecciones_periodo=None), then=F('peso_actual')),

            # CASO 1A: La botella tiene más de una inspeccion, al menos 2 ocurrieron en el periodo analizado, al menos 1 tiene 'peso_botella' != None, pero la primera tiene 'peso_botella' = None
            When(Q(num_inspecciones__gt=1) & Q(inspecciones_periodo__gt=1) & Q(inspecciones_peso_ok_count__gt=0) & Q(peso_primera_inspeccion=None), then=F('peso_inicio_7')),

            # CASO 1B: La botella tiene más de una inspección, al menos una ocurrió en el periodo analizado, y al menos una tiene 'peso_botella' != None
            When(Q(num_inspecciones__gt=1) & Q(inspecciones_periodo__gt=0) & Q(inspecciones_peso_ok_count__gt=0), then=F('peso_inicio_7')),

            # CASO 1C: La botella tiene más de una inspección, al menos una ocurrió en el periodo analizado, pero ninguna tiene 'peso_botella' != None
            When(Q(num_inspecciones__gt=1) & Q(inspecciones_periodo__gt=0) & Q(inspecciones_peso_ok_count=None), then=F('peso_actual')),

            # CASO 1D: La botella tiene más de 1 inspección, al menos una ocurrió en el periodo analizado
            When(Q(num_inspecciones__gt=1) & Q(inspecciones_periodo__gt=0), then=F('peso_inicio_7')),

            # CASO 2: La botella tiene solo 1 inspeccion, pero esta ocurrió fuera del periodo analizado
            When(Q(num_inspecciones=1) & Q(inspecciones_periodo=None), then=F('peso_actual')),

            # CASO 2A: la botella tiene solo 1 inspeccion, esta ocurrio dentro del periodo analizado y su 'peso_botella' != None
            When(Q(num_inspecciones=1) & Q(inspecciones_periodo=1) & Q(inspecciones_peso_ok_count__gt=0), then=F('peso_inicial')),

            # CASO 2B: La botella tiene solo 1 inspeccion, ocurrió dentro del periodo analizado, pero su 'peso_botella' es None
            When(Q(num_inspecciones=1) & Q(inspecciones_periodo=1) & Q(inspecciones_peso_ok_count=None), then=F('peso_inicial')),

            # CASO 2C: la botella tiene solo 1 inspeccion, esta ocurrio dentro del periodo analizado 
            When(Q(num_inspecciones=1) & Q(inspecciones_periodo=1), then=F('peso_inicial')),

            # CASO 3: La botella no tiene inspecciones
            When(Q(num_inspecciones=0), then=F('peso_inicial')),

            output_field=IntegerField()
        )
    )

    #print('::: BOTELLAS - PESO INSPECCION INICIAL :::')
    #print(botellas_peso_inspeccion_inicial.values('folio', 'peso_inspeccion_inicial'))


    #----------------------------------------------------------------------
    # Agregamos 'dif_peso'
    botellas_dif_peso = botellas_peso_inspeccion_inicial.annotate(
        dif_peso=(F('peso_inspeccion_inicial') - F('peso_actual'))
    )

    #----------------------------------------------------------------------
    # Agregamos campo "densidad"
    botellas_densidad = botellas_dif_peso.annotate(
        densidad=ExpressionWrapper(
            2 - F('producto__ingrediente__factor_peso'),
            output_field=DecimalField()
        )
    )

    #----------------------------------------------------------------------
    # Agregamos un campo con el consumo en mililitros
    botellas_consumo = botellas_densidad.annotate(
        consumo_ml=ExpressionWrapper(
            (F('dif_peso') * F('densidad')),
            output_field=DecimalField()
        )
    )

    #----------------------------------------------------------------------
    # Agregamos 'volumen_actual'
    botellas_volumen_actual = botellas_consumo.annotate(
        volumen_actual=ExpressionWrapper(
            #((F('peso_actual') - F('peso_cristal')) * F('producto__ingrediente__factor_peso')),
            (F('peso_actual') - F('peso_cristal')) * (2 - F('producto__ingrediente__factor_peso')),
            output_field=DecimalField()
        )
    )

   
    #----------------------------------------------------------------------
    #----------------------------------------------------------------------
    #----------------------------------------------------------------------

    """
    -----------------------------------------------------------------------

    Utilizamos Pandas para optimizar el desempeño de la app:

    - Django tiene un bug que impide hacer operaciones del tipo 'aggregate'
    para atributos generados con Case(). Esto nos impide completar el reporte
    utilizando solo subqueries.

    -----------------------------------------------------------------------
    """

    botellas = botellas_volumen_actual.values(
        'nombre_producto',
        'capacidad',
        'precio_unitario',
        'consumo_ml',
        'volumen_actual'
    )

    #print('::: BOTELLAS - VALORES :::')
    #print(botellas.values('nombre_producto', 'consumo_ml', 'volumen_actual', 'precio_unitario'))


    def construir_lista_botellas(queryset):
        """
        Esta función construye una lista de diccionarios con los datos del queryset de las botellas
        """

        lista_registros = []

        for item in queryset:

            registro = {}

            precio_unitario = float(item['precio_unitario'].quantize(Decimal('.01'), rounding=ROUND_UP))
            consumo_ml = float(item['consumo_ml'].quantize(Decimal('.01'), rounding=ROUND_UP))
            volumen_actual = float(item['volumen_actual'].quantize(Decimal('.01'), rounding=ROUND_UP))
            
            registro['Producto'] = item['nombre_producto']
            registro['Capacidad'] = item['capacidad']
            registro['Precio'] = precio_unitario
            registro['Demanda'] = consumo_ml
            registro['Stock'] = volumen_actual

            lista_registros.append(registro)

        return lista_registros

    
    json_botellas = construir_lista_botellas(botellas)
    #print('::: LISTA DE BOTELLAS :::')
    #print(json_botellas)

    """
    ---------------------------------------------
    Construimos un dataframe con las botellas y
    calculamos la compra sugerida por Producto
    ---------------------------------------------
    """

    df = pd.DataFrame(json_botellas)
    #print('::: DATAFRAME :::')
    #print(df)

    df['Diferencia'] = (df['Stock'] - df['Demanda']) * (-1)
    df['Faltante'] = np.where((df['Diferencia'] > 0), df['Diferencia'], 0)

    df_precio = df.groupby(['Producto', 'Capacidad']).mean()
    df_precio = df_precio.loc[:, 'Precio']

    df_sum = df.groupby(['Producto', 'Capacidad']).sum()
    df_sum.drop('Precio', axis=1, inplace=True)

    df_ok = pd.concat([df_precio, df_sum], axis=1)
    df_ok.reset_index(inplace=True)
    df_ok['Compra'] = (df_ok['Faltante'] / df_ok['Capacidad'])
    df_ok['Compra'] = df_ok['Compra'].round()
    df_ok.drop('Diferencia', axis=1, inplace=True)

    df_ok['Subtotal'] = df_ok['Precio'] * df_ok['Compra']
    df_ok['IVA'] = df_ok['Subtotal'] * 0.16
    df_ok['Total'] = df_ok['Subtotal'] + df_ok['IVA']

    df_ok = df_ok.loc[df_ok.Compra > 0, :]

    # Si no hay botellas con Compra > 0, notificamos al cliente
    if df_ok.empty == True:

        response = {'status': 'error', 'message': 'No es necesario surtir ningún producto.'}
        return response

    df_ok = df_ok.sort_values('Compra', ascending=False)

    costo_total = df_ok['Total'].sum()

    """
    -----------------------------------------------------
    Convertimos el dataframe en una lista de diccionarios
    -----------------------------------------------------
    """
    diccionarios_botellas = df_ok.to_dict(orient='records')
    #print('::: DICCIONARIOS BOTELLAS :::')
    #print(diccionarios_botellas)

    # Tomamos la fecha para el reporte
    fecha_reporte = datetime.date.today()
    fecha_reporte = fecha_reporte.strftime("%d/%m/%Y")

    # Construimos el reporte
    reporte = {
        'status': 'success',
        'sucursal': sucursal.nombre,
        'fecha': fecha_reporte,
        'costo_total': costo_total,
        'data': diccionarios_botellas
    }


    return reporte

