from django.test import TestCase, Client
from django.urls import reverse

from ventas.parsers import parser_magno_brasserie
import os
import json
import pandas as pd



class ParserMagnoTests(TestCase):

        def test_output_ok(self):
            """ Testear que el output del parser es correcto """

            # Definimos un diccionario con el output esperado del parser
            output_esperado = [
                {
                    'sucursal_id': 1,
                    'caja_id': 1,
                    'codigo_pos': '00050',
                    'nombre': 'CARAJILLO',
                    'unidades': 3,
                    'importe': 285
                },
                {
                    'sucursal_id': 1,
                    'caja_id': 1,
                    'codigo_pos': '00126',
                    'nombre': 'CT HERRADURA BLANCO',
                    'unidades': 1,
                    'importe': 112
                },
                {
                    'sucursal_id': 1,
                    'caja_id': 1,
                    'codigo_pos': '00167',
                    'nombre': 'CW JOHNNIE WALKER ETIQUETA NEGR A',
                    'unidades': 2,
                    'importe': 340
                },
                {
                    'sucursal_id': 1,
                    'caja_id': 1,
                    'codigo_pos': '00081',
                    'nombre': 'LICOR 43',
                    'unidades': 2,
                    'importe': 170
                }
            ]

            # Definimos el path absoluto del reporte de ventas
            path_reporte_ventas = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ventas_magno_brasserie.csv')

            # Procesamos el reporte de ventas con el parser y guardamos el output en una variable
            output_parser = parser_magno_brasserie.parser(path_reporte_ventas)
            #print(output_parser)
            # Convertimos el dataframe del output en un json
            dataframe_output = output_parser['df_ventas']
            output_parser = dataframe_output.to_json(orient='records')
            # Convertimos el json en un objeto de python
            output_parser = json.loads(output_parser)
            # Comparamos el output esperado contra el real
            self.assertEqual(output_esperado, output_parser)


        def test_output_error(self):
            """ Testea que el parser maneja los errores de forma correcta """

            # Definimos el output esperado cuando hay un error en el parseo
            output_esperado = {'df_ventas': {}, 'procesado': False}

            # Definimos el path absoluto del reporte de ventas defectuoso
            path_reporte_ventas = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'reporte_defectuoso.csv')

            # Procesamos el reporte de ventas con el parser y guardamos el output en una variable
            output_parser = parser_magno_brasserie.parser(path_reporte_ventas)
            print(output_parser)

            # Comparamos el output esperado contra el real
            self.assertEqual(output_esperado, output_parser)
