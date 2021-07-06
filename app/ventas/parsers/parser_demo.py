import pandas as pd
from core.models import Sucursal, Almacen, Caja

def parser(ventas_csv, sucursal):

    # Seleccionamos la Barra Principal y su caja
    almacenes = sucursal.almacenes.all()
    barra = almacenes.filter(nombre='BARRA DEMO')[0]
    caja = barra.cajas.all()[0]

    # Tomamos los IDs de la Sucursal y la Caja
    SUCURSAL_ID = sucursal.id
    CAJA_ID = caja.id

    try:
        df_ventas = pd.read_csv(ventas_csv)

        # Añadimos columnas 'sucursal_id' y 'caja_id'
        df_ventas = df_ventas.reindex(columns=[*df_ventas.columns.tolist(), 'sucursal_id'], fill_value=SUCURSAL_ID)
        df_ventas = df_ventas.reindex(columns=[*df_ventas.columns.tolist(), 'caja_id'], fill_value=CAJA_ID)

        # Ordenamos las columnas
        columnas_ordenadas = ['sucursal_id', 'caja_id', 'codigo_pos', 'nombre', 'unidades', 'importe']
        df_ventas = df_ventas.reindex(columns=columnas_ordenadas)


    # Si hay algún error con el archivo CSV, arrojamos una excepción
    except Exception as e:
        #print('::: EXCEPCION :::')
        #print(e)
        return({'df_ventas': {}, 'procesado': False})

    # Si todo sale OK, retornamos el dataframe con los datos parseados
    return({'df_ventas': df_ventas, 'procesado': True})