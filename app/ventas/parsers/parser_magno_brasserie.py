import pandas as pd
import datetime
from core.models import Sucursal, Almacen, Caja


# def parser(ventas_csv):
#     df_ventas = {}
#     procesado = True
    
#     return({'df_ventas': df_ventas, 'procesado': procesado})



def parser(ventas_csv, sucursal):

    # Tomamos los ids de la sucursal y la caja
    almacen = sucursal.almacenes.all()[0]
    caja = almacen.cajas.all()[0]

    SUCURSAL_ID = sucursal.id
    CAJA_ID = caja.id 

    try:
    
        df_ventas_raw = pd.read_csv(ventas_csv, dtype={'Código':str})

        # Renombramos las Columnas
        nombres_columnas_ok = ['codigo_pos', 'nombre', 'eliminar_1', 'eliminar_2', 'unidades', 'importe']
        df_ventas_raw.columns = nombres_columnas_ok

        # Eliminamos columnas innecesarias
        to_drop = ['eliminar_1', 'eliminar_2']
        df_ventas_raw = df_ventas_raw.drop(to_drop, axis=1)

        # Convertimos columna 'unidades' a int
        columna_unidades = df_ventas_raw.loc[:,'unidades'].fillna(0.0).astype(int)
        df_ventas_raw['unidades'] = columna_unidades

        # Convertimos columna 'importe' a int
        columna_importe = df_ventas_raw.loc[:,'importe'].str.replace('$','')
        df_ventas_raw['importe'] = columna_importe
        columna_importe = df_ventas_raw.loc[:,'importe'].str.replace(',','')
        df_ventas_raw['importe'] = columna_importe
        columna_importe = df_ventas_raw.loc[:,'importe'].fillna(0.0).astype(float)
        df_ventas_raw['importe'] = columna_importe
        columna_importe = df_ventas_raw.loc[:,'importe'].fillna(0.0).astype(int)
        df_ventas_raw['importe'] = columna_importe

        # Agregamos columna de Sucursal
        df_copy_01 = df_ventas_raw.copy()
        df_ventas_sucursal = df_copy_01.reindex(columns = [*df_copy_01.columns.tolist(), 'sucursal_id'], fill_value=SUCURSAL_ID)

        # Agregamos columna de Caja
        df_copy_02 = df_ventas_sucursal.copy()
        df_ventas_caja = df_copy_02.reindex(columns = [*df_copy_02.columns.tolist(), 'caja_id'], fill_value=CAJA_ID)

        # Cambiamos el orden de las columnas del dataframe
        df_ventas = df_ventas_caja[['sucursal_id', 'caja_id', 'codigo_pos', 'nombre', 'unidades', 'importe']]

        # # Agregar columna de fecha
        # ayer = datetime.date.today() - datetime.timedelta(days=1)
        # df_ventas = df_ventas_raw.reindex(columns = [*df_ventas_raw.columns.tolist(), 'fecha'], fill_value=ayer)

    except Exception as e:
        return({'df_ventas': {}, 'procesado': False})


    return({'df_ventas': df_ventas, 'procesado': True})