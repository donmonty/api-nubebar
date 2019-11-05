from django.test import TestCase, Client
from django.urls import reverse

from ventas.parsers import parser_magno_brasserie
from ventas.parsers import parser_gambinos_saopaulo
from ventas.parsers import parser_pecos
from ventas.parsers import parser_kinkin

from core import models
import os
import json
import pandas as pd



class ParserMagnoTests(TestCase):

    def setUp(self):

        # Cliente
        self.operadora_magno = models.Cliente.objects.create(nombre='MAGNO BRASSERIE')
        # Sucursal
        self.magno_brasserie = models.Sucursal.objects.create(nombre='MAGNO-BRASSERIE', cliente=self.operadora_magno)
        # Almacen
        self.barra_1 = models.Almacen.objects.create(nombre='BARRA 1', numero=1, sucursal=self.magno_brasserie)
        # Caja
        self.caja_1 = models.Caja.objects.create(numero=1, nombre='CAJA 1', almacen=self.barra_1)


    def test_output_ok(self):
        """ Testear que el output del parser es correcto """

        # Definimos un diccionario con el output esperado del parser
        output_esperado = [
            {
                'sucursal_id': self.magno_brasserie.id,
                'caja_id': self.caja_1.id,
                'codigo_pos': '00050',
                'nombre': 'CARAJILLO',
                'unidades': 3,
                'importe': 285
            },
            {
                'sucursal_id': self.magno_brasserie.id,
                'caja_id': self.caja_1.id,
                'codigo_pos': '00126',
                'nombre': 'CT HERRADURA BLANCO',
                'unidades': 1,
                'importe': 112
            },
            {
                'sucursal_id': self.magno_brasserie.id,
                'caja_id': self.caja_1.id,
                'codigo_pos': '00167',
                'nombre': 'CW JOHNNIE WALKER ETIQUETA NEGR A',
                'unidades': 2,
                'importe': 340
            },
            {
                'sucursal_id': self.magno_brasserie.id,
                'caja_id': self.caja_1.id,
                'codigo_pos': '00081',
                'nombre': 'LICOR 43',
                'unidades': 2,
                'importe': 170
            }
        ]

        # Definimos el path absoluto del reporte de ventas
        path_reporte_ventas = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ventas_magno_brasserie.csv')

        # Procesamos el reporte de ventas con el parser y guardamos el output en una variable
        output_parser = parser_magno_brasserie.parser(path_reporte_ventas, self.magno_brasserie)
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
        output_parser = parser_magno_brasserie.parser(path_reporte_ventas, self.magno_brasserie)
        #print(output_parser)

        # Comparamos el output esperado contra el real
        self.assertEqual(output_esperado, output_parser)


class ParserGambinosSaoPauloTests(TestCase):

    maxDiff = None

    def setUp(self):

        # Cliente
        self.operadora_gambinos = models.Cliente.objects.create(nombre='GAMBINOS')
        # Sucursal
        self.gambinos_saopaulo = models.Sucursal.objects.create(nombre='GAMBINOS-SAOPAULO', cliente=self.operadora_gambinos)
        # Almacen
        self.barra_1 = models.Almacen.objects.create(nombre='BARRA 1', numero=1, sucursal=self.gambinos_saopaulo)
        # Caja
        self.caja_1 = models.Caja.objects.create(numero=1, nombre='CAJA 1', almacen=self.barra_1)

    
    def test_output_ok(self):
        """ 
        ----------------------------------------------------------------------
        Testear que el output del parser es correcto
        ----------------------------------------------------------------------
        """

        # Definimos un diccionario con el output esperado del parser
        output_esperado = [
            {
                'sucursal_id': self.gambinos_saopaulo.id,
                'caja_id': self.caja_1.id,
                'codigo_pos': '100000000847',
                'nombre': '7 Leguas Bco',
                'unidades': 8,
                'importe': 840
            },
            {
                'sucursal_id': self.gambinos_saopaulo.id,
                'caja_id': self.caja_1.id,
                'codigo_pos': '100000001400',
                'nombre': 'Absolute Blue',
                'unidades': 2,
                'importe': 120
            },
            {
                'sucursal_id': self.gambinos_saopaulo.id,
                'caja_id': self.caja_1.id,
                'codigo_pos': '100000001868',
                'nombre': 'Americano',
                'unidades': 4,
                'importe': 188
            },
            {
                'sucursal_id': self.gambinos_saopaulo.id,
                'caja_id': self.caja_1.id,
                'codigo_pos': '100000004050',
                'nombre': 'Aperol Spritz',
                'unidades': 7,
                'importe': 735
            }
        ]

        # Definimos el path absoluto del reporte de ventas
        path_reporte_ventas = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ventas_gambinos_saopaulo.xlsx')

        # Procesamos el reporte de ventas con el parser y guardamos el output en una variable
        output_parser = parser_gambinos_saopaulo.parser(path_reporte_ventas, self.gambinos_saopaulo)
        #print(output_parser)

        # Convertimos el dataframe del output en un json
        dataframe_output = output_parser['df_ventas']

        # Tomamos las primeras 4 filas del dataframe
        dataframe_output = dataframe_output.head(4)
        #print('::: DATAFRAME OUTPUT :::')
        #print(dataframe_output)

        output_parser = dataframe_output.to_json(orient='records')
        # Convertimos el json en un objeto de python
        output_parser = json.loads(output_parser)
        # Comparamos el output esperado contra el real
        self.assertEqual(output_esperado, output_parser)


    def test_output_error(self):
        """
        ----------------------------------------------------------------------
        Testear que el parser maneja los errores de forma correcta
        ----------------------------------------------------------------------
        """

        # Definimos el output esperado cuando hay un error en el parseo
        output_esperado = {'df_ventas': {}, 'procesado': False}

        # Definimos el path absoluto del reporte de ventas defectuoso
        path_reporte_ventas = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'reporte_defectuoso.csv')

        # Procesamos el reporte de ventas con el parser y guardamos el output en una variable
        output_parser = parser_gambinos_saopaulo.parser(path_reporte_ventas, self.gambinos_saopaulo)
        #print(output_parser)

        # Comparamos el output esperado contra el real
        self.assertEqual(output_esperado, output_parser)


class ParserPecosTests(TestCase):

    maxDiff = None

    def setUp(self):

        # Cliente
        self.operadora_pecos = models.Cliente.objects.create(nombre='OPERADORA GAMA')
        # Sucursal
        self.pecos = models.Sucursal.objects.create(nombre='LA CABAÑA DE PECOS', cliente=self.operadora_pecos)
        # Almacen
        self.barra_1 = models.Almacen.objects.create(nombre='BARRA 1', numero=1, sucursal=self.pecos)
        # Caja
        self.caja_1 = models.Caja.objects.create(numero=1, nombre='CAJA 1', almacen=self.barra_1)

    
    def test_output_ok(self):
        """ 
        ----------------------------------------------------------------------
        Testear que el output del parser es correcto
        ----------------------------------------------------------------------
        """

        # Definimos un diccionario con el output esperado del parser
        output_esperado = [
            {
                'sucursal_id': self.pecos.id,
                'caja_id': self.caja_1.id,
                'codigo_pos': '14001',
                'nombre': 'COPA AZTECA DE ORO',
                'unidades': 1,
                'importe': 75
            },
            {
                'sucursal_id': self.pecos.id,
                'caja_id': self.caja_1.id,
                'codigo_pos': '14007',
                'nombre': 'COPA TORRES V',
                'unidades': 9,
                'importe': 675
            },
            {
                'sucursal_id': self.pecos.id,
                'caja_id': self.caja_1.id,
                'codigo_pos': '14008',
                'nombre': 'COPA TORRES X',
                'unidades': 7,
                'importe': 595
            },
            {
                'sucursal_id': self.pecos.id,
                'caja_id': self.caja_1.id,
                'codigo_pos': '43028',
                'nombre': 'CARAJILLO LATUFF',
                'unidades': 4,
                'importe': 560
            }
        ]

        # Definimos el path absoluto del reporte de ventas
        path_reporte_ventas = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ventas_pecos.XLS')

        # Procesamos el reporte de ventas con el parser y guardamos el output en una variable
        output_parser = parser_pecos.parser(path_reporte_ventas, self.pecos)
        #print(output_parser)

        # Convertimos el dataframe del output en un json
        dataframe_output = output_parser['df_ventas']

        # Tomamos las primeras 4 filas del dataframe
        dataframe_output = dataframe_output.head(4)
        #print('::: DATAFRAME OUTPUT :::')
        #print(dataframe_output)

        output_parser = dataframe_output.to_json(orient='records')
        # Convertimos el json en un objeto de python
        output_parser = json.loads(output_parser)
        # Comparamos el output esperado contra el real
        self.assertEqual(output_esperado, output_parser)


    def test_output_error(self):
        """
        ----------------------------------------------------------------------
        Testear que el parser maneja los errores de forma correcta
        ----------------------------------------------------------------------
        """

        # Definimos el output esperado cuando hay un error en el parseo
        output_esperado = {'df_ventas': {}, 'procesado': False}

        # Definimos el path absoluto del reporte de ventas defectuoso
        path_reporte_ventas = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'reporte_defectuoso.csv')

        # Procesamos el reporte de ventas con el parser y guardamos el output en una variable
        output_parser = parser_pecos.parser(path_reporte_ventas, self.pecos)
        #print(output_parser)

        # Comparamos el output esperado contra el real
        self.assertEqual(output_esperado, output_parser)


class ParserKinkinTests(TestCase):

    maxDiff = None

    def setUp(self):

        # Cliente
        self.operadora_kinkin = models.Cliente.objects.create(nombre='OPERADORA KINKIN')
        # Sucursal
        self.kinkin = models.Sucursal.objects.create(nombre='KINKIN', cliente=self.operadora_kinkin)
        # Almacen
        self.barra_1 = models.Almacen.objects.create(nombre='BARRA 1', numero=1, sucursal=self.kinkin)
        # Caja
        self.caja_1 = models.Caja.objects.create(numero=1, nombre='CAJA 1', almacen=self.barra_1)

    
    def test_output_ok(self):
        """ 
        ----------------------------------------------------------------------
        Testear que el output del parser es correcto
        ----------------------------------------------------------------------
        """

        # Definimos un diccionario con el output esperado del parser
        output_esperado = [
            {
                'sucursal_id': self.kinkin.id,
                'caja_id': self.caja_1.id,
                'codigo_pos': 'Hendricks 750 ml',
                'nombre': 'Hendricks 750 ml',
                'unidades': 3,
                'importe': 5400
            },
            {
                'sucursal_id': self.kinkin.id,
                'caja_id': self.caja_1.id,
                'codigo_pos': 'Altos Blanco 750ml',
                'nombre': 'Altos Blanco 750ml',
                'unidades': 1,
                'importe': 0
            },
            {
                'sucursal_id': self.kinkin.id,
                'caja_id': self.caja_1.id,
                'codigo_pos': 'Don Julio 70 750ml',
                'nombre': 'Don Julio 70 750ml',
                'unidades': 1,
                'importe': 1950
            },
            {
                'sucursal_id': self.kinkin.id,
                'caja_id': self.caja_1.id,
                'codigo_pos': 'Absolut Azul 750ml',
                'nombre': 'Absolut Azul 750ml',
                'unidades': 1,
                'importe': 1200
            }
        ]

        # Definimos el path absoluto del reporte de ventas
        path_reporte_ventas = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ventas_kinkin.csv')

        # Procesamos el reporte de ventas con el parser y guardamos el output en una variable
        output_parser = parser_kinkin.parser(path_reporte_ventas, self.kinkin)
        #print(output_parser)

        # Convertimos el dataframe del output en un json
        dataframe_output = output_parser['df_ventas']

        # Tomamos las primeras 4 filas del dataframe
        dataframe_output = dataframe_output.head(4)
        #print('::: DATAFRAME OUTPUT :::')
        #print(dataframe_output)

        output_parser = dataframe_output.to_json(orient='records')
        # Convertimos el json en un objeto de python
        output_parser = json.loads(output_parser)
        # Comparamos el output esperado contra el real
        self.assertEqual(output_esperado, output_parser)


    def test_output_error(self):
        """
        ----------------------------------------------------------------------
        Testear que el parser maneja los errores de forma correcta
        ----------------------------------------------------------------------
        """

        # Definimos el output esperado cuando hay un error en el parseo
        output_esperado = {'df_ventas': {}, 'procesado': False}

        # Definimos el path absoluto del reporte de ventas defectuoso
        path_reporte_ventas = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'reporte_defectuoso.csv')

        # Procesamos el reporte de ventas con el parser y guardamos el output en una variable
        output_parser = parser_kinkin.parser(path_reporte_ventas, self.kinkin)
        #print(output_parser)

        # Comparamos el output esperado contra el real
        self.assertEqual(output_esperado, output_parser)
