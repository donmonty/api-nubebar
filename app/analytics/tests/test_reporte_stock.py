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
from analytics import reporte_stock as gs


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

        # Productos
        self.producto_licor43 = models.Producto.objects.create(
            #folio='Ii0000000001',
            nombre_marca='LICOR 43 750',
            ingrediente=self.licor_43,
            #peso_cristal = 500,
            capacidad=750,
        )

        self.producto_herradura_blanco = models.Producto.objects.create(
            #folio='Nn0000000001',
            nombre_marca='HERRADURA BLANCO 700',
            ingrediente=self.herradura_blanco,
            #peso_cristal = 500,
            capacidad=700,
        )

        self.producto_jw_black = models.Producto.objects.create(
            #folio='Ii0814634647',
            nombre_marca='JOHNNIE WALKER BLACK 750',
            ingrediente=self.jw_black,
            #peso_cristal=500,
            capacidad=750,
        )

        self.producto_maestro_dobel = models.Producto.objects.create(
            #folio='Nn1647414423',
            nombre_marca='MAESTRO DOBEL DIAMANTE 750',
            ingrediente=self.maestro_dobel,
            #peso_cristal=500,
            capacidad=750,
        )

        # Botellas
        self.botella_licor43 = models.Botella.objects.create(
            folio='Ii0000000001',
            producto=self.producto_licor43,
            #url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0765216599',
            capacidad=750,
            usuario_alta=self.usuario,
            sucursal=self.magno_brasserie,
            almacen=self.barra_1,
            proveedor=self.vinos_america,
            peso_cristal=500,
            peso_nueva=1212,
            peso_inicial=1212,
            peso_actual=1000,
            precio_unitario=347.50
        )

        self.botella_licor43_2 = models.Botella.objects.create(
            folio='Ii0000000002',
            producto=self.producto_licor43,
            #url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0765216599',
            capacidad=750,
            usuario_alta=self.usuario,
            sucursal=self.magno_brasserie,
            almacen=self.barra_1,
            proveedor=self.vinos_america,
            peso_cristal=500,
            peso_nueva=1212,
            peso_inicial=1212,
            peso_actual=1000,
            precio_unitario=347.50
        )

        self.botella_herradura_blanco = models.Botella.objects.create(
            folio='Nn0000000001',
            producto=self.producto_herradura_blanco,
            #url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Nn1727494182',
            capacidad=700,
            usuario_alta=self.usuario,
            sucursal=self.magno_brasserie,
            almacen=self.barra_1,
            proveedor=self.vinos_america,
            peso_cristal=500,
            peso_nueva=1165,
            peso_inicial=1165,
            peso_actual=1000,
            precio_unitario=296.00
        )

        self.botella_jw_black = models.Botella.objects.create(
            folio='Ii0814634647',
            producto=self.producto_jw_black,
            #url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0814634647',
            capacidad=750,
            usuario_alta=self.usuario,
            sucursal=self.magno_brasserie,
            almacen=self.barra_1,
            proveedor=self.vinos_america,
            peso_cristal=500,
            peso_nueva=1212,
            peso_inicial=1212,
            peso_actual=1000,
            precio_unitario=565.50
        )

        self.botella_maestro_dobel = models.Botella.objects.create(
            folio='Nn1647414423',
            producto=self.producto_maestro_dobel,
            capacidad=750,
            usuario_alta=self.usuario,
            sucursal=self.magno_brasserie,
            almacen=self.barra_3,
            proveedor=self.vinos_america,
            peso_cristal=500,
            peso_inicial=1212,
            peso_actual=800,
            precio_unitario=460.00,
            estado='0'
        )


    #-----------------------------------------------------------------------------
    def test_script_reporte_ok(self):

        """
        -----------------------------------------------------------------------
        Testeamos que el script del reporte funcione OK
        -----------------------------------------------------------------------
        """

        # Ejecutamos el reporte
        reporte = gs.get_stock(self.magno_brasserie)

        #print('::: TEST - COSTO STOCK :::')
        #print(reporte)
      
        # Checamos que el status del reporte sea 'success'
        self.assertEqual(reporte['status'], 'success')
        # Checamos que el primer producto del response sea una botella de LICOR 43 750
        self.assertEqual(reporte['data']['botellas'][0]['nombre_marca'], self.producto_licor43.nombre_marca)
        # Checamos que el segundo producto del response sea una botella de HERRADURA BLANCO 700
        self.assertEqual(reporte['data']['botellas'][1]['nombre_marca'], self.producto_herradura_blanco.nombre_marca)
        # Checamos que el tercer producto del response sea una botella de JOHNIE WALKER BLACK 750
        self.assertEqual(reporte['data']['botellas'][2]['nombre_marca'], self.producto_jw_black.nombre_marca)
        # Checamos las unidades de LICOR 43 750 
        self.assertEqual(reporte['data']['botellas'][0]['unidades'], models.Botella.objects.filter(producto=self.producto_licor43).count())


    #-----------------------------------------------------------------------------
    def test_reporte_ok(self):

        """
        -----------------------------------------------------------------------
        Test para el endpoint 'get_reporte_stock'
        Testear que el endpoint funciona OK
        -----------------------------------------------------------------------
        """

        # Construimos el request
        url = reverse('analytics:get-reporte-stock', args=[self.magno_brasserie.id])
        response = self.client.get(url)
        json_response = json.dumps(response.data)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        #print('::: RESPONSE DATA - JSON :::')
        #print(json_response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        

    #-----------------------------------------------------------------------------
    @patch('analytics.reporte_stock.get_stock')
    def test_reporte_error(self, mock_reporte):

        """
        -----------------------------------------------------------------------
        Test para el endpoint 'get_reporte_stock'
        Testear que el endpoint funciona OK cuando hay un error
        -----------------------------------------------------------------------
        """

        mock_reporte.return_value = {'status': 'error', 'message': 'Esta sucursal no tiene botellas registradas.'}

        # Construimos el request
        url = reverse('analytics:get-reporte-stock', args=[self.magno_brasserie.id])
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
        Testeamos que el script 'get_stock_detalle' del reporte funcione OK
        ----------------------------------------------------------------------------------
        """

        # Creamos otra botella de LICOR 43 750 para este test
        botella_licor43_3 = models.Botella.objects.create(
            folio='Ii0000000003',
            producto=self.producto_licor43,
            capacidad=750,
            usuario_alta=self.usuario,
            sucursal=self.magno_brasserie,
            almacen=self.barra_1,
            proveedor=self.vinos_america,
            peso_cristal=500,
            peso_nueva=1212,
            peso_inicial=1212,
            peso_actual=800,
            precio_unitario=347.50
        )

        # Ejecutamos el reporte
        reporte = gs.get_stock_detalle(self.producto_licor43.id, self.magno_brasserie.id)

        #print('::: TEST - COSTO STOCK :::')
        #print(reporte)
      
        # Checamos que el status del reporte sea 'success'
        self.assertEqual(reporte['status'], 'success')
        # Checamos que el orden de las botellas sea correcto (de menor a mayor volumen_ml)
        botella_con_menos_liquido = models.Botella.objects.filter(producto=self.producto_licor43).order_by('peso_actual')[0]
        self.assertEqual(reporte['data'][0]['folio'], botella_con_menos_liquido.folio)


    #-----------------------------------------------------------------------------
    def test_reporte_detalle_ok(self):

        """
        -----------------------------------------------------------------------
        Test para el endpoint 'get_detalle_stock'
        Testear que el endpoint funciona OK
        -----------------------------------------------------------------------
        """

        # Construimos el request
        parametros = {
            'producto_id': self.producto_licor43.id,
            'sucursal_id': self.magno_brasserie.id
        }
        url = reverse('analytics:get-detalle-stock', kwargs=parametros)
        response = self.client.get(url)
        json_response = json.dumps(response.data)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        #print('::: RESPONSE DATA - JSON :::')
        #print(json_response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)



    #-----------------------------------------------------------------------------
    @patch('analytics.reporte_stock.get_stock_detalle')
    def test_reporte_detalle_error(self, mock_reporte):

        """
        -----------------------------------------------------------------------
        Test para el endpoint 'get_detalle_stock'
        Testear que el endpoint funciona OK cuando hay un error
        -----------------------------------------------------------------------
        """

        mock_reporte.return_value = {'status': 'error', 'message': 'No hay botellas asociadas a este producto.'}

        # Construimos el request
        parametros = {
            'producto_id': self.producto_maestro_dobel.id,
            'sucursal_id': self.magno_brasserie.id
        }
        url = reverse('analytics:get-detalle-stock', kwargs=parametros)
        response = self.client.get(url)
        json_response = json.dumps(response.data)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        #print('::: RESPONSE DATA - JSON :::')
        #print(json_response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


