from unittest.mock import patch

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import TestCase
from django.utils.six import StringIO

import pandas as pd
import json
from core import models
from core.management.commands import productos_google_sheet as pg
from core.management.commands.add_products import Command



"""
-------------------------------------------------------------------
VARIABLES PARA SETUP
-------------------------------------------------------------------
"""

nombres_sheets = ['LICOR', 'LICOR-BOTELLAS']
url = 'http://urldummy.com'

productos = {
	'LICOR':
		{
			'codigo_pos': ['CPLICO001', 'CPLICO002'],
			'nombre_producto': ['Licor 43', 'Baileys'],
			'codigo_ingrediente': ['LICO001', 'LICO002'],
			'volumen': [60, 60]
		},
	'LICOR-BOTELLAS': 
		{
			'codigo_pos': ['BTLICO001', 'BTLICO002'],
			'nombre_producto': ['Licor 43 750', 'Baileys 750'],
			'codigo_ingrediente': ['LICO001', 'LICO002'],
			'volumen': [750, 750]	
		},
}


licores = {
    'codigo_pos': ['CPLICO001', 'CPLICO002'],
    'nombre_producto': ['Licor 43', 'Baileys'],
    'codigo_ingrediente': ['LICO001', 'LICO002'],
    'volumen': [60, 60]
}
botellas = {
    'codigo_pos': ['BTLICO001', 'BTLICO002'],
    'nombre_producto': ['Licor 43 750', 'Baileys 750'],
    'codigo_ingrediente': ['LICO001', 'LICO002'],
    'volumen': [750, 750]	
}
licores_error = {
    'codigo_pos': ['CPLICO001', 'CPLICO002', 'CPLICO003'],
    'nombre_producto': ['Licor 43', 'Baileys', 'APEROL'],
    'codigo_ingrediente': ['LICO001', 'LICO002', 'LICO003'],
    'volumen': [60, 60, 60]
}

# Creamos un dataframe con los items a registrar. Todos los ingredientes existen
dataframe_licores = pd.DataFrame(licores)
dataframe_botellas = pd.DataFrame(botellas)
df_licores_botellas = pd.concat([dataframe_licores, dataframe_botellas], axis=0)
df_licores_botellas['nombre_producto'] = df_licores_botellas['nombre_producto'].str.upper()
df_licores_botellas.reset_index(drop=True, inplace=True)

# Creamos otro dataframe que tiene un item cuyo ingrediente no existe
dataframe_licores_error = pd.DataFrame(licores_error)
df_licores_botellas_error = pd.concat([dataframe_licores_error, dataframe_botellas], axis=0)
df_licores_botellas_error['nombre_producto'] = df_licores_botellas['nombre_producto'].str.upper()
df_licores_botellas_error.reset_index(drop=True, inplace=True)


# Esta clase funciona como una especie de mock object para simular
# la conexión al API de Google
class Client():

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @classmethod
    def open_by_url(cls, url):
        nuevo_client = cls(productos=productos, url=url)
        return nuevo_client

    @classmethod
    def crear_hoja(cls, hoja):
        nueva_hoja = cls(hoja=hoja)
        return nueva_hoja

    def worksheet(self, nombre_worksheet):
        hoja = self.productos[nombre_worksheet]
        return self.crear_hoja(hoja)

    def get_all_records(self):
        records = self.hoja
        return records

client = Client(productos=productos)

"""
-------------------------------------------------------------------
AQUI COMIENZAN LOS TESTS
------------------------------------------------------------------- 
"""

class CommandTests(TestCase):

    maxDiff = None

    def setUp(self):

        # Cliente
        self.operadora_magno = models.Cliente.objects.create(nombre='MAGNO BRASSERIE')
        # Sucursal
        self.magno_brasserie = models.Sucursal.objects.create(nombre='MAGNO-BRASSERIE', cliente=self.operadora_magno)
        #Categorías
        self.categoria_licor = models.Categoria.objects.create(nombre='LICOR')

        # Ingredientes
        self.licor_43 = models.Ingrediente.objects.create(
            codigo='LICO001',
            nombre='LICOR 43',
            categoria=self.categoria_licor,
            factor_peso=1.05
        )
        self.baileys = models.Ingrediente.objects.create(
            codigo='LICO002',
            nombre='BAILEYS',
            categoria=self.categoria_licor,
            factor_peso=1.05
        )


    def test_wait_for_db_ready(self):
        """Test waiting for db when db is available"""
        with patch('django.db.utils.ConnectionHandler.__getitem__') as gi:
            gi.return_value = True
            call_command('wait_for_db')
            self.assertEqual(gi.call_count, 1)


    @patch('time.sleep', return_value=True)
    def test_wait_for_db(self, ts):
        """Test waiting for db"""
        with patch('django.db.utils.ConnectionHandler.__getitem__') as gi:
            gi.side_effect = [OperationalError] * 5 + [True]
            call_command('wait_for_db')
            self.assertEqual(gi.call_count, 6)


    
    def test_crear_dataframe_productos_ok(self):
        """ Testear que  se crea el dataframe con los items del Google sheet de forma correcta"""

        json_df = df_licores_botellas.to_json(orient='records')
        output_esperado = json.loads(json_df)

        # Ejecutamos el módulo y guardamos el output
        respuesta = pg.crear_dataframe_productos(url, client, nombres_sheets)
        json_respuesta = respuesta.to_json(orient='records')
        output_real = json.loads(json_respuesta)

        # Comparamos el output real con el esperado
        self.assertEqual(output_esperado, output_real)

    
    def test_crear_recetas_ok(self):
        """ Testear que se crean las recetas del setup con éxito """

        sucursal_id = self.magno_brasserie.id

        # Ejecutamos el módulo y guardamos el output
        respuesta = pg.crear_recetas(df_licores_botellas, sucursal_id)

        # Tomamos las recetas registradas
        recetas_registradas = models.Receta.objects.all()

        # Comparamos la respuesta esperada con la real
        self.assertEqual(respuesta['items_registrados'], 4)
        self.assertEqual(recetas_registradas.count(), 4)
        self.assertEqual(respuesta['errores']['cantidad'], 0)


    def test_crear_recetas_error(self):
        """ Testear que se manejan los items sin ingrediente de forma correcta """

        sucursal_id = self.magno_brasserie.id

        # Ejecutamos el módulo y guardamos el output
        respuesta = pg.crear_recetas(df_licores_botellas_error, sucursal_id)

        # Tomamos las recetas registradas
        recetas_registradas = models.Receta.objects.all()
        #print(recetas_registradas)
        #print(respuesta['items_registrados'])

        # Comparamos la respuesta esperada con la real
        self.assertEqual(respuesta['items_registrados'], 4)
        self.assertEqual(recetas_registradas.count(), 4)
        self.assertEqual(respuesta['errores']['cantidad'], 1)


    # @patch('add_products.oauth2client.service_account.ServiceAccountCredentials.from_json_keyfile_name')
    # @patch('add_products.gspread.authorize')
    # @patch('add_productos.SHEETS_RECETAS')
    # def test_add_productos_ok(self, mock_sheets, mock_client, mock_creds):
    #     """ Testear que se toman los items del API de Google y se registran de forma correcta """

 #@patch('core.management.commands.add_products.pg.crear_recetas')
    @patch('core.management.commands.add_products.pg.crear_dataframe_productos')
    @patch('core.management.commands.add_products.ServiceAccountCredentials.from_json_keyfile_name')
   # @patch.object(Command, 'handle.gspread.authorize', return_value=client)
    @patch('core.management.commands.add_products.gspread.authorize')
    @patch('core.management.commands.add_products.SHEETS_RECETAS')
    def test_add_productos_ok(self, mock_sheets, mock_client, mock_creds, mock_df_items):
        """ Testear que se toman los items del API de Google y se registran de forma correcta """
        
        sucursal_id = self.magno_brasserie.id
        client_2 = Client(productos=productos)
        mock_sheets.return_value = nombres_sheets #SHEETS_RECETAS
        mock_creds.return_value = productos #ServiceAccountCredentials.from_json_keyfile_name
        #print(mock_creds.return_value)
        mock_client.return_value = client_2 # gspread.authorize
        mock_df_items.return_value = df_licores_botellas
        #mock_registros.return_value = {'items_registrados': 4, 'errores': {'cantidad': 0, 'items': []}}
        #print(mock_client.return_value)
        #mock_df_items.return_value = df_licores_botellas # Command.handle.df_items
        #respuesta = pg.crear_recetas(df_licores_botellas, sucursal_id)
        #mock_registros.side_effect = respuesta # Command.handle.registros

        out = StringIO()
        

        # Ejecutamos el comando utilizando variables dummy/mockeadas
        call_command('add_products', url, sucursal_id, stdout=out)

        self.assertIn("Recetas creadas con éxito!", out.getvalue())
        




    







