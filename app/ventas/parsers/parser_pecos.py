import pandas as pd
from core.models import Sucursal, Almacen, Caja

def parser(ventas_csv, sucursal):

    # Seleccionamos la Barra Principal y su caja
    almacenes = sucursal.almacenes.all()
    barra = almacenes.filter(nombre='BARRA 1')[0]
    caja = barra.cajas.all()[0]

    # Tomamos los IDs de la Sucursal y la Caja
    SUCURSAL_ID = sucursal.id
    CAJA_ID = caja.id

    try:
        
        df_ventas = pd.read_excel(ventas_csv, header=4, skipfooter=1, dtype={'CLAVE': str, 'VENTA_TOTAL': str}, engine='xlrd')

        # Eliminamos las columnas innecesarias
        to_drop = [
            'PRECIO',
            'COSTO',
            'COSTO_TOTAL',
            'VENTA_COSTO',
            'PRECIO_DE_VENTA',
            'PRECIO_DE_CATALOGO',
            'VENTA_TOTAL_PRECIO_CATALOGO',
            'TASA_IVA'
            ]
        
        df_ventas = df_ventas.drop(to_drop, axis=1)

        # Renombramos las columnas
        nombres_columnas_ok = ['codigo_pos', 'nombre', 'categoria', 'unidades', 'importe']
        df_ventas.columns = nombres_columnas_ok

        # Creamos una función para eliminar los decimales de un string
        def drop_decimals(numero):
            numero = str(numero)
            numero = numero.split('.')[0]
            return numero

        # Aplicamos la funcion a la columna 'importe'
        df_ventas['importe'] = df_ventas.importe.apply(drop_decimals)

        # Convertimos la columna 'importe' a INT
        columna_int = df_ventas.loc[:, 'importe'].astype(int)
        df_ventas['importe'] = columna_int

        # Eliminamos REFRESCOS y CERVEZAS
        filtro_refrescos = df_ventas.loc[:,'categoria'].str.contains('REFRESCOS', na=False, regex=True)
        df_ventas = df_ventas[~filtro_refrescos]

        filtro_cervezas = df_ventas.loc[:,'categoria'].str.contains('CERVEZAS', na=False, regex=True)
        df_ventas = df_ventas[~filtro_cervezas]

        # Eliminamos items donde 'unidades' = 0
        df_ventas = df_ventas.loc[df_ventas.unidades!=0, :]

        # Eliminamos la columna 'categoria'
        df_ventas = df_ventas.drop('categoria', axis=1)

        # Añadimos columnas 'sucursal_id' y 'caja_id'
        df_ventas = df_ventas.reindex(columns=[*df_ventas.columns.tolist(), 'sucursal_id'], fill_value=SUCURSAL_ID)
        df_ventas = df_ventas.reindex(columns=[*df_ventas.columns.tolist(), 'caja_id'], fill_value=CAJA_ID)

        # Ordenamos las columnas
        columnas_ordenadas = ['sucursal_id', 'caja_id', 'codigo_pos', 'nombre', 'unidades', 'importe']
        df_ventas = df_ventas.reindex(columns=columnas_ordenadas)

    # Si hay algún error con el Excel, arrojamos una excepción
    except Exception as e:
        #print('::: EXCEPCION :::')
        #print(e)
        return({'df_ventas': {}, 'procesado': False})

    # Si todo sale OK, retornamos el dataframe con los datos parseados
    return({'df_ventas': df_ventas, 'procesado': True})
