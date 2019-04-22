import pandas as pd
from core import models
import gspread



"""
------------------------------------------------------------------------
METODO QUE CONSTRUYE UN DATAFRAME CON LOS PRODUCTOS DEL GOOGLE SHEET

Inputs:
- url_sheet: El URL del Google sheet
- client: Una instancia de Client que se comunica con el Google API (creada vía gspread.authorize)
- nombres_sheets: Una lista con los nombres de las worksheets del Google sheet
------------------------------------------------------------------------
"""
def crear_dataframe_productos(url_sheet, client, nombres_sheets):

    # Intentamos abrir la spreadsheet
    try:
        #sheet = client.open_by_url(url_sheet)
        #print(sheet)
        client.open_by_url(url_sheet)

    # Si hay un error con el URL de la spreadsheet, retornamos la excepción:
    except gspread.SpreadsheetNotFound as error:
        return error

    except Exception as error:
        return error 

    else:
        sheet = client.open_by_url(url_sheet) 
        lista_dataframes = []

        # Guardamos los items de cada worksheet en un dataframe
        for worksheet in nombres_sheets:
            hoja = sheet.worksheet(worksheet)
            items = hoja.get_all_records()
            df_items = pd.DataFrame(items)
            lista_dataframes.append(df_items)

        # Concatenamos los dataframes
        df_items_todo = pd.concat(lista_dataframes, axis=0)

        # Convertimos los nombres de los productos a mayúsculas
        df_items_todo['nombre_producto'] = df_items_todo['nombre_producto'].str.upper()
        df_items_todo.reset_index(drop=True, inplace=True)

        return df_items_todo


"""
--------------------------------------------------------------------------------------------------
FUNCION QUE CONSTRUYE UN CATALOGO DE RECETAS (TRAGOS DERECHOS Y BOTELLAS) A PARTIR DE UN DATAFRAME

Inputs:
- dataframe_items: un dataframe de los items a registrar (generado con la función anterior)
- sucursal: la instancia de la sucursal  
--------------------------------------------------------------------------------------------------
"""
def crear_recetas(dataframe_items, sucursal_id):

    sucursal = models.Sucursal.objects.get(id=sucursal_id)
    items_sin_registro = []
    numero_registros = 0
    numero_sin_registro = 0

    for (codigo_pos, nombre_producto, codigo_ingrediente, volumen) in dataframe_items.itertuples(name=None, index=False):

        # Si el Ingrediente existe, creamos la receta
        if models.Ingrediente.objects.filter(codigo=codigo_ingrediente).exists():
            ingrediente = models.Ingrediente.objects.get(codigo=codigo_ingrediente)
            receta = models.Receta.objects.create(codigo_pos=codigo_pos, nombre=nombre_producto, sucursal=sucursal)
            ingrediente_receta = models.IngredienteReceta.objects.create(receta=receta, ingrediente=ingrediente, volumen=volumen)
            numero_registros += 1

        # Si no existe, lo agregamos a la lista de items sin registro
        else:
            sin_registro = (codigo_pos, nombre_producto)
            numero_sin_registro += 1
            items_sin_registro.append(sin_registro)

    return {'items_registrados': numero_registros,
            'errores': {'cantidad': numero_sin_registro, 'items': items_sin_registro}}

      