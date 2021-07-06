import pandas as pd
#import numpy as np
from decimal import Decimal
import os
from core import models
from django.core.exceptions import ObjectDoesNotExist


def crear_productos():

    # Creamos un path para el archivo CSV
    path_csv = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'BLUEPRINTS.csv')

    # Construimos un dataframe con los datos del CSV e importamos todo como string
    df_blueprints = pd.read_csv(path_csv, dtype=str)

    # Creamos una lista para guardar todos los errores que ocirran durante el proceso
    lista_ingredientes_error = []

    contador = 0

    # Iteramos por las filas del dataframe
    for (codigo_barras, nombre_marca, codigo_ingrediente, capacidad, precio_unitario, peso_cristal, peso_nueva) in df_blueprints.itertuples(index=False, name=None):

        # Checamos que el Ingrediente exista
        try:
            ingrediente = models.Ingrediente.objects.get(codigo=codigo_ingrediente)

        # Si el ingrediente no existe, notificamos al usuario y lo guardamos en una lista
        except ObjectDoesNotExist:
            print('El ingrediente {} no existe en la base de datos!'.format(codigo_ingrediente))

        # Si el ingrediente existe, creamos el blueprint
        else:

            # Convertimos 'precio_unitario' a Decimal
            precio_unitario = Decimal(float(precio_unitario))

            # Convertimos 'capacidad' a int
            capacidad = int(capacidad)

            """
            Si 'peso_cristal' y 'peso_nueva' son igual a cero:

            - Declaramos 'peso_cristal' = None
            - Declaramos 'peso_nueva' = None
            """
            if int(peso_cristal) == 0:

                peso_cristal = None
                peso_nueva = None

            # Si no son cero, convertimos a número entero
            else:
                peso_cristal = int(peso_cristal)
                peso_nueva = int(peso_nueva)

            # Creamos el Blueprint
            producto = models.Producto.objects.create(

                folio='',
                ingrediente=ingrediente,
                codigo_barras=codigo_barras,

                tipo_marbete='',
                fecha_elaboracion_marbete='',
                lote_produccion_marbete='',
                url='',

                nombre_marca=nombre_marca,
                tipo_producto='',
                graduacion_alcoholica='',
                capacidad=capacidad,
                origen_del_producto='',
                fecha_envasado='',
                fecha_importacion='',
                lote_produccion='',
                numero_pedimento='',
                nombre_fabricante='',
                rfc_fabricante='',

                peso_nueva=peso_nueva,
                peso_cristal=peso_cristal,
                precio_unitario=precio_unitario,
            )

            contador = contador + 1

            print('---------------------------------------------------')
            print('::: ALTA DE BLUEPRINTS TERMINADA :::')
            print('---------------------------------------------------')
            print('Se crearon un total de {} Productos con exito!'.format(contador))
            print('Se generaron {} errores causados por ingredientes no registrados.'.format(len(lista_ingredientes_error)))

            # SI hubo errores por ingredientes no registrados, lisar los blueprints afectados
            if len(lista_ingredientes_error) > 0:

                print('---------------------------------------------------')
                print('---------------------------------------------------')
                print('::: LISTA DE BLUEPRINTS CON ERRORES :::')
                print('---------------------------------------------------')
                print('---------------------------------------------------')

                for item in lista_ingredientes_error:

                    print(item)


            