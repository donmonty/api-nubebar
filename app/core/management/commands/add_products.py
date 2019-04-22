from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials
from  . import productos_google_sheet as pg
from core import models


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

creds = None

class Command(BaseCommand):
    
    help = 'Alta inicial de recetas (tragos derechos y botellas)'

    def add_arguments(self, parser):
        parser.add_argument('url', type=str, help="El URL del Google sheet")
        parser.add_argument('sucursal', type=int, help="El id de la sucursal")

    
    def handle(self, *args, **kwargs):
        url_sheet = kwargs['url']
        sucursal_id = kwargs['sucursal']
        secret_abs_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'alta-productos-secreto.json')

        # Checamos que la Sucursal capturada por el usuario existe en la base de datos
        try:
            models.Sucursal.objects.get(id=sucursal_id)

        except ObjectDoesNotExist:
            raise CommandError('La sucursal con el id "%d" no existe.' % sucursal_id)

        else:

            # Nos preparamos para conectarnos al API de Google Sheets
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            global creds
            creds = ServiceAccountCredentials.from_json_keyfile_name(secret_abs_path, scope)
            #print('Este es el valor de creds:')
            #print(creds)
            #client = gspread.authorize(creds)
            #print(client.productos)

            self.stdout.write('Conectando con Google Sheets...')
            
            # Intentamos conectarnos al API
            try:
                #client = gspread.authorize(creds)
                gspread.authorize(creds)
                #print(client)
            
            # Si hay un error, notificar al usuario
            except Exception:
            #except ((gspread.exceptions.APIError, Exception, gspread.exceptions.GSpreadException)):
                self.stdout.write(self.style.ERROR('Hubo un error al conectarse con Google Sheets. Intenta de nuevo más tarde.'))

            # Si la conexión es exitosa, registrar las recetas
            else:
                
                client = gspread.authorize(creds)
                # Creamos un dataframe con los items del Google sheet
                df_items = pg.crear_dataframe_productos(url_sheet, client, SHEETS_RECETAS)

                if isinstance(df_items, gspread.exceptions.SpreadsheetNotFound):
                    print(df_items)
                    #self.stdout.write(self.style.ERROR(error))
                    raise CommandError('La URL proporiconada no está asociada a ninguna spreadsheet.')

                else:

                    # Registramos las recetas
                    registros = pg.crear_recetas(df_items, sucursal_id)

                    # Publicamos mensaje de confirmación
                    self.stdout.write(self.style.SUCCESS("Recetas creadas con éxito!"))

                    # Si hubo items que no se pudieron registrar, notificarle al usuario
                    if registros['errores']['cantidad'] != 0:
                        errores = registros['errores']['items']
                        self.stdout.write(self.style.WARNING('Los siguientes items no se registraron: %s' % errores ))
        

