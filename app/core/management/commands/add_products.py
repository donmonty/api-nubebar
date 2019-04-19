from django.core.management.base import BaseCommand
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials
from  . import productos_google_sheet as pg


 # Definimos los nombres de las worksheets que contienen los items a registrar
SHEETS_RECETAS = [
'BRANDY',
'COGNAC',
'LICOR',
'MEZCAL',
'RON',
'TEQUILA',
'VODKA',
'WHISKY',
'BRANDY-BOTELLAS',
'COGNAC-BOTELLAS',
'LICOR-BOTELLAS',
'MEZCAL-BOTELLAS',
'RON-BOTELLAS',
'TEQUILA-BOTELLAS',
'VODKA-BOTELLAS',
'WHISKY-BOTELLAS'
]

class Command(BaseCommand):
    
    help = 'Alta inicial de recetas (tragos derechos y botellas)'

    def add_arguments(self, parser):
        parser.add_argument('url', type=str, help="El URL del Google sheet")
        parser.add_argument('sucursal', type=int, help="El id de la sucursal")

    
    def handle(self, *args, **kwargs):
        url_sheet = kwargs['url']
        sucursal_id = kwargs['sucursal']
        secret_abs_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'alta-productos-secreto.json')

        # Nos conectamos al API de Google
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(secret_abs_path, scope)
        #print(creds)
        client = gspread.authorize(creds)
        #print(client.productos)

        # Creamos un dataframe con los items del Google sheet
        df_items = pg.crear_dataframe_productos(url_sheet, client, SHEETS_RECETAS)

        # Registramos las recetas
        registros = pg.crear_recetas(df_items, sucursal_id)

        # Publicamos mensaje de confirmación
        self.stdout.write(self.style.SUCCESS("Recetas creadas con éxito!"))

        # Si hubo items que no se pudieron registrar, notificarlo
        if registros['errores']['cantidad'] != 0:
            errores = registros['errores']['items']
            self.stdout.write(self.style.WARNING('Los siguientes items no se registraron: %s' % errores ))
        

