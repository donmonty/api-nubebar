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


def get_mermas_tiempo(almacen_id, fecha_inicial, fecha_final):

    # Tomamos el almacen
    almacen = models.Almacen.objects.get(id=almacen_id)

    # Convertimos las fechas a date
    fecha_inicial = datetime.datetime.strptime(fecha_inicial, '%Y-%m-%d').date()
    fecha_final = datetime.datetime.strptime(fecha_final, '%Y-%m-%d').date()

    # Tomamos las mermas de todos los ingredientes para el periodo indicado
    mermas = models.MermaIngrediente.objects.filter(almacen=almacen, fecha_final__gte=fecha_inicial, fecha_final__lte=fecha_final)

    # Si el queryset está vacío, notificamos al usuario
    if not mermas.exists():
        return {'status': 'error', 'message': 'No hay mermas registradas en el periodo seleccionado.'}

    # Añadimos el nombre del ingrediente
    mermas = mermas.annotate(nombre_ingrediente=F('ingrediente__nombre'))

    # Añadimos la categoría
    mermas = mermas.annotate(categoria=F('ingrediente__categoria__nombre'))

    # Seleccionamos los campos deseados
    mermas = mermas.values(
        'nombre_ingrediente',
        'categoria',
        'fecha_final',
        'consumo_ventas',
        'consumo_real',
        'merma',
        'porcentaje'
    ).order_by('nombre_ingrediente', 'fecha_final')
    #print('::: MERMAS VALUES :::')
    #print(mermas)

    def construir_lista_mermas(queryset):
        """
        Esta función construye una lista de diccionarios con las mermas del queryset
        """

        lista_registros = []

        for item in queryset:

            registro = {}

            merma = float(item['merma'].quantize(Decimal('.01'), rounding=ROUND_UP))
            porcentaje = float(item['porcentaje'].quantize(Decimal('.01'), rounding=ROUND_UP))
            consumo_facturado = 0 if item['consumo_ventas'] is None else float(item['consumo_ventas'].quantize(Decimal('.01'), rounding=ROUND_UP))
            consumo_real = 0 if item['consumo_real'] is None else float(item['consumo_real'].quantize(Decimal('.01'), rounding=ROUND_UP))
            fecha_final = item['fecha_final'].strftime('%Y-%m-%d')
            
            registro['Ingrediente'] = item['nombre_ingrediente']
            registro['Categoria'] = item['categoria']
            registro['Fecha'] = fecha_final
            registro['Consumo Facturado'] = consumo_facturado
            registro['Consumo Real'] = consumo_real
            registro['Merma'] = merma
            registro['Porcentaje'] = porcentaje

            lista_registros.append(registro)

        return lista_registros

    # Convertimos el queryset de las mermas en una lista
    lista_mermas = construir_lista_mermas(mermas)

    """
    -----------------------------------------------------
    Construimos el response
    -----------------------------------------------------
    """

    df = pd.DataFrame(lista_mermas)
    #print('::: DATAFRAME MERMAS :::')
    #print(df)

    # Agregamos la columna de tragos y redondeamos las decimales
    df['Tragos'] = (df['Merma']/60)*-1
    df = df.round({'Tragos': 1})

    # Convertimos la columna 'Fecha' a datetime
    #df['Fecha'] = pd.to_datetime(df['Fecha'])

    """
    Dividimos el dataframe en varios dataframes, uno para cada ingrediente
    """
    lista_dataframes = []

    for ingrediente in list(df.Ingrediente.unique()):
        df_ingrediente = df.loc[df.Ingrediente == ingrediente, :]
        lista_dataframes.append(df_ingrediente)

    """
    Construimos las series de los ingredientes
    """
    series = []

    for dframe in lista_dataframes:
        dframe.set_index(['Ingrediente','Categoria'], inplace=True)
        serie_producto = {
            'Ingrediente': dframe.index[0][0],
            'Categoria': dframe.index[0][1]
        }
        data = []
        registro = dframe.to_dict(orient='records')
        #data.append(registro)
        serie_producto['data'] = registro
        series.append(serie_producto)
    
    #print('::: SERIES :::')
    #print(series)

    """
    Construimos un objeto con los datos para la tabla del reporte
    - La tabla muestra el acumulado de las mermas por ingrediente
    """
    df_tabla = df
    #print('::: DF TABLA :::')
    #print(df_tabla)

    df_tabla = df_tabla.groupby(['Ingrediente', 'Categoria']).sum()
    #print('::: DF TABLA - GROUPBY :::')
    #print(df_tabla)

    df_tabla['Porcentaje'] = (df_tabla['Merma'] / df_tabla['Consumo Facturado']) * 100
    df_tabla['Tragos'] = (df_tabla['Merma'] / 60) * -1
    df_tabla = df_tabla.round({'Consumo Facturado': 1, 'Consumo Real': 1, 'Merma': 1, 'Porcentaje': 1, 'Tragos': 1})
    df_tabla.reset_index(inplace=True)
    tabla = df_tabla.to_dict(orient='records')


    """
    Retornamos el response
    """
    response = {
        'status': 'success',
        'sucursal': almacen.sucursal.nombre,
        'almacen': almacen.nombre,
        'fecha_inicial': fecha_inicial.strftime('%Y-%m-%d'),
        'fecha_final': fecha_final.strftime('%Y-%m-%d'),
        'data':{
            'series': series,
            'tabla': tabla
        }
    }

    return response


