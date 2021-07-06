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

    # Intentamos procesar el archivo CSV de las ventas
    try:

        df_ventas = pd.read_csv(ventas_csv, lineterminator='\r')

        # Eliminamos cervezas
        filtro_cerveza = df_ventas.loc[:,'Division'].str.contains('CERVEZA/Be', na=False, regex=True)
        df_ventas = df_ventas[~filtro_cerveza]

        # Eliminamos bebidas sin alcohol
        filtro_sin_alcohol = df_ventas.loc[:,'Division'].str.contains('SIN ALCOHOL', na=False, regex=True)
        df_ventas = df_ventas[~filtro_sin_alcohol]

        # Eliminamos Energy Drinks
        filtro_energy_drinks = df_ventas.loc[:,'Division'].str.contains('ENERGY DRINKS', na=False, regex=True)
        df_ventas = df_ventas[~filtro_energy_drinks]

        # Eliminamos columnas innecesarias
        to_drop = ['Column1', 'Division']
        df_ventas = df_ventas.drop(to_drop, axis=1)

        # Duplicamos columna 'Producto' y la renombramos 'codigo_pos'
        columna_duplicada = df_ventas['Producto']
        df_ventas['codigo_pos'] = columna_duplicada

        # Cambiamos el nombre de las columnas
        nombres_columnas_ok = ['nombre', 'unidades', 'importe', 'codigo_pos']
        df_ventas.columns = nombres_columnas_ok

        # Eliminamos filas donde 'nombre' == NaN
        filtro_nan = ((df_ventas.nombre).isnull()) & ((df_ventas.codigo_pos).isnull())
        df_ventas = df_ventas[~filtro_nan]

        # Redondeamos los valores de la columna 'unidades'
        df_ventas = df_ventas.round({'unidades': 0})

        # Convertimos columna 'unidades' a INT
        columna_int = df_ventas.loc[:, 'unidades'].astype(int)
        df_ventas['unidades'] = columna_int

        # Convertimos columna 'importe' a INT
        columna_importe = df_ventas.loc[:,'importe'].str.replace('$','')
        df_ventas['importe'] = columna_importe
        columna_importe = df_ventas.loc[:,'importe'].str.replace(',','')
        df_ventas['importe'] = columna_importe

        def eliminar_decimales(numero):
            numero = numero.split('.')[0]
            return numero

        columna_importe = df_ventas['importe'].apply(eliminar_decimales)
        df_ventas['importe'] = columna_importe

        columna_importe = df_ventas.loc[:,'importe'].astype(int)
        df_ventas['importe'] = columna_importe

        # Agregar columnas de 'Sucursal' y 'Caja'
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