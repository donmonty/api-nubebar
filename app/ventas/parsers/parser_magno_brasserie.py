import pandas as pd
import os
import xlrd
import datetime
from core.models import Sucursal, Almacen, Caja


def parser(ventas_csv, sucursal):

   # Tomamos los ids de la sucursal y la caja
    almacen = sucursal.almacenes.all()[0]
    caja = almacen.cajas.all()[0]

    SUCURSAL_ID = sucursal.id
    CAJA_ID = caja.id

    try:

        wb = xlrd.open_workbook(ventas_csv, logfile=open(os.devnull, 'w'))
        df_ventas = pd.read_excel(wb, header=None, skiprows=9, skipfooter=5, engine='xlrd')

        # Eliminamos columnas innecesarias
        to_drop = [0, 4, 6]
        df_ventas = df_ventas.drop(to_drop, axis=1)

        # Renombramos las columnas
        nombres_columnas_ok = ['codigo_pos', 'nombre', 'unidades', 'importe']
        df_ventas.columns = nombres_columnas_ok

        # Eliminamos Platillos Fuertes
        filtro_platillo_fuerte = df_ventas.loc[:,'codigo_pos'].str.contains('PF', na=False, regex=True)
        df_ventas = df_ventas[~filtro_platillo_fuerte]

        # Eliminamos Entradas
        filtro_entrada = df_ventas.loc[:,'codigo_pos'].str.contains('ENT', na=False, regex=True)
        df_ventas = df_ventas[~filtro_entrada]

        # Eliminamos Bebidas Sin Alcohol
        filtro_sin_alcohol = df_ventas.loc[:,'codigo_pos'].str.contains('BEB', na=False, regex=True)
        df_ventas = df_ventas[~filtro_sin_alcohol]

        # Eliminamos Postres
        filtro_postre = df_ventas.loc[:,'codigo_pos'].str.contains('POS', na=False, regex=True)
        df_ventas = df_ventas[~filtro_postre]

        # Eliminamos Charcuteria
        filtro_charcuteria = df_ventas.loc[:,'codigo_pos'].str.contains('CHA', na=False, regex=True)
        df_ventas = df_ventas[~filtro_charcuteria]

        # Eliminamos Refrescos
        filtro_refresco = df_ventas.loc[:,'codigo_pos'].str.contains('REF', na=False, regex=True)
        df_ventas = df_ventas[~filtro_refresco]

        # Eliminamos Cervezas
        filtro_cerveza = df_ventas.loc[:,'codigo_pos'].str.contains('CVZ', na=False, regex=True)
        df_ventas = df_ventas[~filtro_cerveza]

        # Eliminamos Pastas
        filtro_pasta = df_ventas.loc[:,'codigo_pos'].str.contains('PAS', na=False, regex=True)
        df_ventas = df_ventas[~filtro_pasta]

        # Eliminamos Cortesias
        filtro_cortesia = df_ventas.loc[:,'codigo_pos'].str.contains('COR', na=False, regex=True)
        df_ventas = df_ventas[~filtro_cortesia]

        # Eliminamos Menus
        filtro_menu = df_ventas.loc[:,'codigo_pos'].str.contains('MEN', na=False, regex=True)
        df_ventas = df_ventas[~filtro_menu]

        # Eliminamos PC
        filtro_pc = df_ventas.loc[:,'codigo_pos'].str.contains('PC', na=False, regex=True)
        df_ventas = df_ventas[~filtro_pc]

        # Eliminamos Botellas de Vino Tinto
        filtro_vino_tinto = df_ventas.loc[:,'codigo_pos'].str.contains('BVT', na=False, regex=True)
        df_ventas = df_ventas[~filtro_vino_tinto]

        # Eliminamos Botellas de Vino Blanco
        filtro_vino_blanco = df_ventas.loc[:,'codigo_pos'].str.contains('BVB', na=False, regex=True)
        df_ventas = df_ventas[~filtro_vino_blanco]

        # Eliminamos Botellas de Vino Rosado
        filtro_vino_rosado = df_ventas.loc[:,'codigo_pos'].str.contains('BVR', na=False, regex=True)
        df_ventas = df_ventas[~filtro_vino_rosado]

        # Eliminamos Botellas de Vino Espumoso
        filtro_vino_espumoso = df_ventas.loc[:,'codigo_pos'].str.contains('BVE', na=False, regex=True)
        df_ventas = df_ventas[~filtro_vino_espumoso]

        # Eliminamos Copas de Vino Tinto
        filtro_copa_vino_tinto = df_ventas.loc[:,'codigo_pos'].str.contains('CVT', na=False, regex=True)
        df_ventas = df_ventas[~filtro_copa_vino_tinto]

        # Eliminamos Copas de Vino Blanco
        filtro_copa_vino_blanco = df_ventas.loc[:,'codigo_pos'].str.contains('CVB', na=False, regex=True)
        df_ventas = df_ventas[~filtro_copa_vino_blanco]

        # Eliminamos Copas de Vino Rosado
        filtro_copa_vino_rosado = df_ventas.loc[:,'codigo_pos'].str.contains('CVR', na=False, regex=True)
        df_ventas = df_ventas[~filtro_copa_vino_rosado]

        # Eliminamos Copas de Vino Espumoso
        filtro_copa_vino_espumoso = df_ventas.loc[:,'codigo_pos'].str.contains('CVE', na=False, regex=True)
        df_ventas = df_ventas[~filtro_copa_vino_espumoso]

        # Eliminamos Copas de Vino Dulce
        filtro_copa_vino_dulce = df_ventas.loc[:,'codigo_pos'].str.contains('CVD', na=False, regex=True)
        df_ventas = df_ventas[~filtro_copa_vino_dulce]

        # Eliminamos EXT
        filtro_ext = df_ventas.loc[:,'codigo_pos'].str.contains('EXT', na=False, regex=True)
        df_ventas = df_ventas[~filtro_ext]

        # Eliminamos Cigarros
        filtro_cigarros = df_ventas.loc[:,'codigo_pos'].str.contains('CIG', na=False, regex=True)
        df_ventas = df_ventas[~filtro_cigarros]

        # Eliminamos Descorche
        filtro_descorche = df_ventas.loc[:,'codigo_pos'].str.contains('DES', na=False, regex=True)
        df_ventas = df_ventas[~filtro_descorche]

        # Convertimos columna 'importe' a INT
        columna_importe = df_ventas.loc[:,'importe'].astype(int)
        df_ventas.loc[:, 'importe'] = columna_importe

        # Agregar columnas de 'Sucursal' y 'Caja'
        df_ventas = df_ventas.reindex(columns=[*df_ventas.columns.tolist(), 'sucursal_id'], fill_value=SUCURSAL_ID)
        df_ventas = df_ventas.reindex(columns=[*df_ventas.columns.tolist(), 'caja_id'], fill_value=CAJA_ID)

        # Ordenamos las columnas
        columnas_ordenadas = ['sucursal_id', 'caja_id', 'codigo_pos', 'nombre', 'unidades', 'importe']
        df_ventas = df_ventas.reindex(columns=columnas_ordenadas)


    except Exception as e:
        return({'df_ventas': {}, 'procesado': False})


    return({'df_ventas': df_ventas, 'procesado': True})



# def parser(ventas_csv, sucursal):

#     # Tomamos los ids de la sucursal y la caja
#     almacen = sucursal.almacenes.all()[0]
#     caja = almacen.cajas.all()[0]

#     SUCURSAL_ID = sucursal.id
#     CAJA_ID = caja.id 

#     try:
    
#         df_ventas_raw = pd.read_csv(ventas_csv, dtype={'Código':str})

#         # Renombramos las Columnas
#         nombres_columnas_ok = ['codigo_pos', 'nombre', 'eliminar_1', 'eliminar_2', 'unidades', 'importe']
#         df_ventas_raw.columns = nombres_columnas_ok

#         # Eliminamos columnas innecesarias
#         to_drop = ['eliminar_1', 'eliminar_2']
#         df_ventas_raw = df_ventas_raw.drop(to_drop, axis=1)

#         # Convertimos columna 'unidades' a int
#         columna_unidades = df_ventas_raw.loc[:,'unidades'].fillna(0.0).astype(int)
#         df_ventas_raw['unidades'] = columna_unidades

#         # Convertimos columna 'importe' a int
#         columna_importe = df_ventas_raw.loc[:,'importe'].str.replace('$','')
#         df_ventas_raw['importe'] = columna_importe
#         columna_importe = df_ventas_raw.loc[:,'importe'].str.replace(',','')
#         df_ventas_raw['importe'] = columna_importe
#         columna_importe = df_ventas_raw.loc[:,'importe'].fillna(0.0).astype(float)
#         df_ventas_raw['importe'] = columna_importe
#         columna_importe = df_ventas_raw.loc[:,'importe'].fillna(0.0).astype(int)
#         df_ventas_raw['importe'] = columna_importe

#         # Agregamos columna de Sucursal
#         df_copy_01 = df_ventas_raw.copy()
#         df_ventas_sucursal = df_copy_01.reindex(columns = [*df_copy_01.columns.tolist(), 'sucursal_id'], fill_value=SUCURSAL_ID)

#         # Agregamos columna de Caja
#         df_copy_02 = df_ventas_sucursal.copy()
#         df_ventas_caja = df_copy_02.reindex(columns = [*df_copy_02.columns.tolist(), 'caja_id'], fill_value=CAJA_ID)

#         # Cambiamos el orden de las columnas del dataframe
#         df_ventas = df_ventas_caja[['sucursal_id', 'caja_id', 'codigo_pos', 'nombre', 'unidades', 'importe']]

#         # # Agregar columna de fecha
#         # ayer = datetime.date.today() - datetime.timedelta(days=1)
#         # df_ventas = df_ventas_raw.reindex(columns = [*df_ventas_raw.columns.tolist(), 'fecha'], fill_value=ayer)

#     except Exception as e:
#         return({'df_ventas': {}, 'procesado': False})


#     return({'df_ventas': df_ventas, 'procesado': True})