from django.test import TestCase
from django.db.models import F, Q, QuerySet, Avg, Count, Sum, Subquery, OuterRef, Exists, Func, ExpressionWrapper, DecimalField, Case, When
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIClient
from rest_framework import serializers

from core import models

import datetime
from django.utils.timezone import make_aware
from decimal import Decimal, ROUND_DOWN, ROUND_UP
import json
from freezegun import freeze_time
from analytics import reporte_productos_sin_registro as r_sin_registro


class AnalyticsTests(TestCase):
    """ Testear acceso autenticado al API """
    maxDiff = None

    def setUp(self):

        # API Client
        self.client = APIClient()

        #Fechas
        self.hoy = datetime.date.today()
        self.ayer = self.hoy - datetime.timedelta(days=1)

        # Proveedores
        self.vinos_america = models.Proveedor.objects.create(nombre='Vinos America')

        # Cliente
        self.operadora_magno = models.Cliente.objects.create(nombre='MAGNO BRASSERIE')

        # Sucursal
        self.magno_brasserie = models.Sucursal.objects.create(nombre='MAGNO-BRASSERIE', cliente=self.operadora_magno)

        # Almacenes
        self.barra_1 = models.Almacen.objects.create(nombre='BARRA 1', numero=1, sucursal=self.magno_brasserie)
        self.barra_2 = models.Almacen.objects.create(nombre='BARRA 2', numero=2, sucursal=self.magno_brasserie)
        self.barra_3 = models.Almacen.objects.create(nombre='BARRA 3', numero=3, sucursal=self.magno_brasserie)
        
        # Cajas
        self.caja_1 = models.Caja.objects.create(numero=1, nombre='CAJA 1', almacen=self.barra_1)
        self.caja_2 = models.Caja.objects.create(numero=2, nombre='CAJA 2', almacen=self.barra_2)
        self.caja_3 = models.Caja.objects.create(numero=3, nombre='CAJA 3', almacen=self.barra_3)

        # Usuarios
        self.usuario = get_user_model().objects.create(email='test@foodstack.mx', password='password123')
        self.usuario.sucursales.add(self.magno_brasserie)

        self.usuario_2 = get_user_model().objects.create(email='barman@foodstack.mx', password='password123')
        self.usuario_2.sucursales.add(self.magno_brasserie)

        # Autenticación
        self.client.force_authenticate(self.usuario)

        #Categorías
        self.categoria_licor = models.Categoria.objects.create(nombre='LICOR')
        self.categoria_tequila = models.Categoria.objects.create(nombre='TEQUILA')
        self.categoria_whisky = models.Categoria.objects.create(nombre='WHISKY')

        # Ingredientes
        self.licor_43 = models.Ingrediente.objects.create(
            codigo='LICO001',
            nombre='LICOR 43',
            categoria=self.categoria_licor,
            factor_peso=1.05
        )
        self.herradura_blanco = models.Ingrediente.objects.create(
            codigo='TEQU001',
            nombre='HERRADURA BLANCO',
            categoria=self.categoria_tequila,
            factor_peso=0.95
        )
        self.jw_black = models.Ingrediente.objects.create(
            codigo='WHIS001',
            nombre='JOHNNIE WALKER BLACK',
            categoria=self.categoria_whisky,
            factor_peso=0.95
        )
        self.maestro_dobel = models.Ingrediente.objects.create(
            codigo='TEQU002',
            nombre='MAESTRO DOBEL',
            categoria=self.categoria_tequila,
            factor_peso=0.95
        )
        

        # Recetas
        self.trago_licor_43 = models.Receta.objects.create(
            codigo_pos='00081',
            nombre='LICOR 43 DERECHO',
            sucursal=self.magno_brasserie
        )
        self.trago_herradura_blanco = models.Receta.objects.create(
            codigo_pos='00126',
            nombre='HERRADURA BLANCO DERECHO',
            sucursal=self.magno_brasserie
        )
        self.trago_jw_black = models.Receta.objects.create(
            codigo_pos= '00167',
            nombre='JW BLACK DERECHO',
            sucursal=self.magno_brasserie
        )
        self.carajillo = models.Receta.objects.create(
            codigo_pos='00050',
            nombre='CARAJILLO',
            sucursal=self.magno_brasserie
        )
        self.trago_maestro_dobel = models.Receta.objects.create(
            codigo_pos= '00190',
            nombre='MAESTRO DOBEL DERECHO',
            sucursal=self.magno_brasserie
        )

        # Ingredientes-Recetas
        self.ir_licor_43 = models.IngredienteReceta.objects.create(receta=self.trago_licor_43, ingrediente=self.licor_43, volumen=60)
        self.ir_herradura_blanco = models.IngredienteReceta.objects.create(receta=self.trago_herradura_blanco, ingrediente=self.herradura_blanco, volumen=60)
        self.ir_jw_black = models.IngredienteReceta.objects.create(receta=self.trago_jw_black, ingrediente=self.jw_black, volumen=60)
        self.ir_carajillo = models.IngredienteReceta.objects.create(receta=self.carajillo, ingrediente=self.licor_43, volumen=45)
        self.ir_maestro_dobel = models.IngredienteReceta.objects.create(receta=self.trago_maestro_dobel, ingrediente=self.maestro_dobel, volumen=60)

        with freeze_time("2019-11-01"):
            # Manejamos el tema del naive datetime
            naive_datetime = datetime.datetime.now()
            aware_datetime = make_aware(naive_datetime)

            # ProductosSinRegistro 1
            self.chivas_sin_registro_01 = models.ProductoSinRegistro.objects.create(
                sucursal=self.magno_brasserie,
                codigo_pos='0001',
                caja=self.caja_1.numero,
                nombre='CHIVAS 12 60ml',
                fecha=aware_datetime,
                unidades=1,
                importe=180
            )

        with freeze_time("2019-11-02"):
            # Manejamos el tema del naive datetime
            naive_datetime = datetime.datetime.now()
            aware_datetime = make_aware(naive_datetime)

            # ProductosSinRegistro 2
            self.chivas_sin_registro_02 = models.ProductoSinRegistro.objects.create(
                sucursal=self.magno_brasserie,
                codigo_pos='0001',
                caja=self.caja_1.numero,
                nombre='CHIVAS 12 60ml',
                fecha=aware_datetime,
                unidades=2,
                importe=360
            )

        with freeze_time("2019-11-03"):
            # Manejamos el tema del naive datetime
            naive_datetime = datetime.datetime.now()
            aware_datetime = make_aware(naive_datetime)

            # ProductosSinRegistro
            self.baileys_sin_registro_01 = models.ProductoSinRegistro.objects.create(
                sucursal=self.magno_brasserie,
                codigo_pos='0002',
                caja=self.caja_1.numero,
                nombre='BAILEYS 60ml',
                fecha=aware_datetime,
                unidades=1,
                importe=90
            )

    #-----------------------------------------------------------------------------
    def test_script_reporte_ok(self):

        """
        -----------------------------------------------------------------------
        Testeamos que el script del reporte funcione OK
        -----------------------------------------------------------------------
        """

        # Ejecutamos el reporte
        reporte = r_sin_registro.get_productos_sin_registro(self.magno_brasserie)

        #print('::: TEST - COSTO STOCK :::')
        #print(reporte)

        # Checamos que el status del reporte sea 'success'
        self.assertEqual(reporte['status'], 'success')
        # Checamos que el numero de ProductosSinRegistro del response sea correcto
        self.assertEqual(len(reporte['data']), 2)
        # Checamos que los ProductosSinRegistro del response sean los correctos
        self.assertEqual(reporte['data'][0]['codigo_pos'], self.chivas_sin_registro_02.codigo_pos)
        self.assertEqual(reporte['data'][1]['codigo_pos'], self.baileys_sin_registro_01.codigo_pos)


    #-----------------------------------------------------------------------------
    def test_reporte_ok(self):

        """
        -----------------------------------------------------------------------
        Test para el endpoint 'get_productos_sin_registro'
        Testear que el endpoint funciona OK
        -----------------------------------------------------------------------
        """

        # Construimos el request
        url = reverse('analytics:get-reporte-productos-sin-registro', args=[self.magno_brasserie.id])
        response = self.client.get(url)
        json_response = json.dumps(response.data)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        #print('::: RESPONSE DATA - JSON :::')
        #print(json_response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


    #-----------------------------------------------------------------------------
    @patch('analytics.reporte_productos_sin_registro.get_productos_sin_registro')
    def test_reporte_error(self, mock_reporte):

        """
        -----------------------------------------------------------------------
        Test para el endpoint 'get_reporte_productos_sin_registro'
        Testear que el endpoint funciona OK cuando hay un error
        -----------------------------------------------------------------------
        """

        mock_reporte.return_value = {'status': 'error', 'message': 'No hay productos sin registro en esta sucursal.'}

        # Construimos el request
        url = reverse('analytics:get-reporte-productos-sin-registro', args=[self.magno_brasserie.id])
        response = self.client.get(url)
        json_response = json.dumps(response.data)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        #print('::: RESPONSE DATA - JSON :::')
        #print(json_response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


    #-----------------------------------------------------------------------------
    def test_script_reporte_detalle_ok(self):

        """
        ---------------------------------------------------------------------------------
        Testeamos que el script 'get_detalle_sin_registro' del reporte funcione OK
        ----------------------------------------------------------------------------------
        """

        # Ejecutamos el reporte
        reporte = r_sin_registro.get_detalle_sin_registro(self.chivas_sin_registro_01.codigo_pos, self.magno_brasserie.id)

        #print('::: TEST - DETALLE SIN REGISTRO :::')
        #print(reporte)
      
        # Checamos que el status del reporte sea 'success'
        self.assertEqual(reporte['status'], 'success')
        # Checamos que haya dos items en el response
        self.assertEqual(len(reporte['data']), 2)


    #-----------------------------------------------------------------------------
    def test_reporte_detalle_ok(self):

        """
        -----------------------------------------------------------------------
        Test para el endpoint 'get_detalle_sin_registro'
        Testear que el endpoint funciona OK 
        -----------------------------------------------------------------------
        """

        # Construimos el request
        parametros = {
            'codigo_pos': self.baileys_sin_registro_01.codigo_pos,
            'sucursal_id': self.magno_brasserie.id
        }
        url = reverse('analytics:get-detalle-sin-registro', kwargs=parametros)
        response = self.client.get(url)
        json_response = json.dumps(response.data)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        #print('::: RESPONSE DATA - JSON :::')
        #print(json_response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


    #-----------------------------------------------------------------------------
    @patch('analytics.reporte_productos_sin_registro.get_detalle_sin_registro')
    def test_reporte_detalle_error(self, mock_reporte):

        """
        -----------------------------------------------------------------------
        Test para el endpoint 'get_detalle_sin_registro'
        Testear que el endpoint funciona OK cuando hay un error
        -----------------------------------------------------------------------
        """

        mock_reporte.return_value = {'status': 'error', 'message': 'Este Producto Sin Registro no existe.'}

        # Construimos el request
        parametros = {
            'codigo_pos': '999',
            'sucursal_id': 999
        }
        url = reverse('analytics:get-detalle-sin-registro', kwargs=parametros)
        response = self.client.get(url)
        json_response = json.dumps(response.data)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        #print('::: RESPONSE DATA - JSON :::')
        #print(json_response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    

        