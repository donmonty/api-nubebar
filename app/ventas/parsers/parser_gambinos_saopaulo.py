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

    # Intentamos procesar el archivo de Excel de las ventas
    try:

        df_ventas = pd.read_excel(ventas_csv, header=None, skiprows=1, dtype=object, engine='xlrd')

        # Eliminamos las columnas innecesarias
        to_drop = [0, 1, 2, 4, 9, 11]
        df_ventas = df_ventas.drop(to_drop, axis=1)
        
        # Renombramos las columnas
        nombres_columnas_ok = ['nombre', 'codigo_pos','categoria', 'subcat', 'unidades', 'importe']
        df_ventas.columns = nombres_columnas_ok

        # Eliminamos items de comida
        filtro_comida = df_ventas.loc[:,'categoria'].str.contains('Comida', na=False, regex=True)
        df_ventas = df_ventas[~filtro_comida]

        # Eliminamos items sin categoría (NaN)
        filtro_nan = (df_ventas.categoria).isnull()
        df_ventas = df_ventas[~filtro_nan]

        # Eliminamos items sin 'codigo_pos'
        filtro_nan = (df_ventas.codigo_pos).isnull()
        df_ventas = df_ventas[~filtro_nan]

        # Eliminamos bebidas sin alcohol y cervezas
        filtro_sin_alcohol = df_ventas.loc[:, 'subcat'].str.contains('NO Alcoholico', na=False, regex=True)
        df_ventas = df_ventas[~filtro_sin_alcohol]

        filtro_cervezas = df_ventas.loc[:, 'subcat'].str.contains('Cervezas', na=False, regex=True)
        df_ventas = df_ventas[~filtro_cervezas]

        # Añadimos columnas 'sucursal_id' y 'caja_id'
        df_ventas = df_ventas.reindex(columns=[*df_ventas.columns.tolist(), 'sucursal_id'], fill_value=SUCURSAL_ID)
        df_ventas = df_ventas.reindex(columns=[*df_ventas.columns.tolist(), 'caja_id'], fill_value=CAJA_ID)

        # Eliminamos la columna 'categoria'
        df_ventas = df_ventas.drop('categoria', axis=1)

        # Eliminamos la columna 'subcat'
        df_ventas = df_ventas.drop('subcat', axis=1)

        # Ordenamos las columnas
        columnas_ordenadas = ['sucursal_id', 'caja_id', 'codigo_pos', 'nombre', 'unidades', 'importe']
        df_ventas = df_ventas.reindex(columns=columnas_ordenadas)

        # Convertimos las columnas 'unidades' e 'importe' a tipo INT
        columna_int = df_ventas.loc[:, 'unidades'].astype(int)
        df_ventas['unidades'] = columna_int

        columna_int = df_ventas.loc[:, 'importe'].astype(int)
        df_ventas['importe'] = columna_int

    # Si hay algún error con el Excel, arrojamos una excepción
    except Exception as e:
        #print('::: EXCEPCION :::')
        #print(e)
        return({'df_ventas': {}, 'procesado': False})

    # Si todo sale OK, retornamos el dataframe con los datos parseados
    return({'df_ventas': df_ventas, 'procesado': True})

