from django.db.models import F, Q, QuerySet, Avg, Count, Sum, Subquery, OuterRef, Exists, Func, ExpressionWrapper, DecimalField, IntegerField, Case, When
from core import models
from decimal import Decimal
import decimal
import datetime
from decimal import Decimal, ROUND_UP
from django.core.exceptions import ObjectDoesNotExist


"""
----------------------------------------------------------------
CODIGO POS          NOMBRE PRODUCTO                         >
----------------------------------------------------------------
00583               CARAJILLO 60
................................................................
Fecha Venta         Unidades
----------------------------------------------------------------
01/11/2019          2
02/11/2019          1
04/11/2019          4

"""

def get_productos_sin_registro(sucursal):

    # Tomamos todos los ProductoSinRegistro de la sucursal
    productos = models.ProductoSinRegistro.objects.filter(sucursal=sucursal)

    # Si no hay ProductoSinRegistro, notificamos al cliente
    if productos.count() == 0:

        response = {
            'status': 'success',
            'message': 'No hay productos sin registro en esta sucursal.'
        }
        return response

    # Tomamos solo los distintos
    productos = productos.distinct('codigo_pos')
    print('::: PRODUCTOS - DISTINCT :::')
    print(productos.values())

    # Convertimos el queryset en una lista de diccionarios
    productos = productos.values('codigo_pos', 'nombre')

    """
    Guardamos los productos que continuan sin registrarse en una lista
    """
    lista_sin_registrar = []

    for item in productos:

        codigo_pos = item['codigo_pos']

        try:
            receta = models.Receta.objects.get(codigo_pos=codigo_pos, sucursal=sucursal)

        except ObjectDoesNotExist:
            lista_sin_registrar.append(item)

        else:
            continue

    print('::: LISTA SIN REGISTRAR :::')
    print(lista_sin_registrar)

    # Construimos el response
    response = {
        'status': 'success',
        'data': lista_sin_registrar
    }

    return response


def get_detalle_sin_registro(codigo_pos, sucursal_id):


    try:

        # Tomamos la Sucursal
        sucursal = models.Sucursal.objects.get(id=sucursal_id)

        # Tomamos todas las instancias del producto sin registro
        productos = models.ProductoSinRegistro.objects.filter(codigo_pos=codigo_pos, sucursal=sucursal)

    except ObjectDoesNotExist:

        response = {
            'status': 'error',
            'message': 'Este Producto Sin Registro no existe.'
        }
        return response

    else:

        # Convertimos el queryset en una lista de diccionarios
        productos = productos.values('fecha', 'unidades', 'importe')

        # Formateamos las fechas para que sean legibles
        for item in productos:
            item['fecha'] = item['fecha'].strftime("%d/%m/%Y")

        # Construimos el response
        response = {
            'status': 'success',
            'data': list(productos)
        }

        return response


