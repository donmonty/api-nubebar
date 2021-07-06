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
from analytics import reporte_mermas_tiempo as rm


class AnalyticsTests(TestCase):
    """ Testear acceso autenticado al API """
    maxDiff = None

    def setUp(self):

        # API Client
        self.client = APIClient()

        #Fechas
        self.hoy = datetime.date.today()
        self.ayer = self.hoy - datetime.timedelta(days=1)
        self.fecha_inicial = '2020-02-01'
        self.fecha_final = '2020-02-07'

        # Proveedores
        self.vinos_america = models.Proveedor.objects.create(nombre='Vinos America')

        # Cliente
        self.operadora_magno = models.Cliente.objects.create(nombre='MAGNO BRASSERIE')

        # Sucursal
        self.magno_brasserie = models.Sucursal.objects.create(nombre='MAGNO-BRASSERIE', cliente=self.operadora_magno)

        # Almacenes
        self.barra_1 = models.Almacen.objects.create(nombre='BARRA 1', numero=1, sucursal=self.magno_brasserie)
        
        # Cajas
        self.caja_1 = models.Caja.objects.create(numero=1, nombre='CAJA 1', almacen=self.barra_1)

        # Usuarios
        self.usuario = get_user_model().objects.create(email='test@foodstack.mx', password='password123')
        self.usuario.sucursales.add(self.magno_brasserie)

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

        """
        ------------------------------
        Creamos la Inspeccion 1 
        ------------------------------
        """
        with freeze_time("2020-02-01"):
            
            # Inspeccion 1
            self.inspeccion_1 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1' # CERRADA
                )

            # Reporte de mermas 1
            self.reporte_mermas_1 = models.ReporteMermas.objects.create(
                fecha_inicial=datetime.date(2020, 1, 31),
                fecha_final=datetime.date(2020, 2, 1),
                inspeccion=self.inspeccion_1,
                almacen=self.barra_1
            )

            # Merma HERRADURA BLANCO 1
            self.merma_herradura_1 = models.MermaIngrediente.objects.create(
                ingrediente=self.herradura_blanco,
                reporte=self.reporte_mermas_1,
                almacen=self.barra_1,
                fecha_inicial=self.reporte_mermas_1.fecha_inicial,
                fecha_final=self.reporte_mermas_1.fecha_final,
                consumo_ventas=2000,
                consumo_real=2100,
            )

            # Merma MAESTRO DOBEL 1
            self.merma_dobel_1 = models.MermaIngrediente.objects.create(
                ingrediente=self.maestro_dobel,
                reporte=self.reporte_mermas_1,
                almacen=self.barra_1,
                fecha_inicial=self.reporte_mermas_1.fecha_inicial,
                fecha_final=self.reporte_mermas_1.fecha_final,
                consumo_ventas=2000,
                consumo_real=2200,
            )

            # Merma LICOR 43 1
            self.merma_licor43_1 = models.MermaIngrediente.objects.create(
                ingrediente=self.licor_43,
                reporte=self.reporte_mermas_1,
                almacen=self.barra_1,
                fecha_inicial=self.reporte_mermas_1.fecha_inicial,
                fecha_final=self.reporte_mermas_1.fecha_final,
                consumo_ventas=2000,
                consumo_real=2300,
            )

        """
        ------------------------------
        Creamos la Inspeccion 2 
        ------------------------------
        """
        with freeze_time("2020-02-02"):
            
            # Inspeccion 1
            self.inspeccion_2 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1' # CERRADA
                )

            # Reporte de mermas 2
            self.reporte_mermas_2 = models.ReporteMermas.objects.create(
                fecha_inicial=datetime.date(2020, 2, 1),
                fecha_final=datetime.date(2020, 2, 2),
                inspeccion=self.inspeccion_2,
                almacen=self.barra_1
            )

            # Merma HERRADURA BLANCO 2
            self.merma_herradura_2 = models.MermaIngrediente.objects.create(
                ingrediente=self.herradura_blanco,
                reporte=self.reporte_mermas_2,
                almacen=self.barra_1,
                fecha_inicial=self.reporte_mermas_2.fecha_inicial,
                fecha_final=self.reporte_mermas_2.fecha_final,
                consumo_ventas=1000,
                consumo_real=1100,
            )

            # Merma MAESTRO DOBEL 2
            self.merma_dobel_2 = models.MermaIngrediente.objects.create(
                ingrediente=self.maestro_dobel,
                reporte=self.reporte_mermas_2,
                almacen=self.barra_1,
                fecha_inicial=self.reporte_mermas_2.fecha_inicial,
                fecha_final=self.reporte_mermas_2.fecha_final,
                consumo_ventas=1000,
                consumo_real=1200,
            )

            # Merma LICOR 43 2
            self.merma_licor43_2 = models.MermaIngrediente.objects.create(
                ingrediente=self.licor_43,
                reporte=self.reporte_mermas_2,
                almacen=self.barra_1,
                fecha_inicial=self.reporte_mermas_2.fecha_inicial,
                fecha_final=self.reporte_mermas_2.fecha_final,
                consumo_ventas=1000,
                consumo_real=1300,
            )

    #-----------------------------------------------------------------------------
    def test_script_reporte_ok(self):

        """
        -----------------------------------------------------------------------
        Testeamos que el script del reporte funcione OK
        -----------------------------------------------------------------------
        """

        reporte = rm.get_mermas_tiempo(self.barra_1.id, self.fecha_inicial, self.fecha_final)
        json_reporte = json.dumps(reporte)
        print('::: REPORTE - JSON :::')
        print(json_reporte)

        self.assertEqual(reporte['status'], 'success')

    #-----------------------------------------------------------------------------
    def test_reporte_ok(self):

        """
        -----------------------------------------------------------------------
        Test para el endpoint 'get_reporte_mermas_tiempo'
        Testear que el endpoint funciona OK
        -----------------------------------------------------------------------
        """

        # Construimos el request
        parametros = {
            'almacen_id': self.barra_1.id,
            'fecha_inicial': self.fecha_inicial,
            'fecha_final': self.fecha_final
        }
        url = reverse('analytics:get-reporte-mermas-tiempo', kwargs=parametros)
        response = self.client.get(url)
        #json_response = json.dumps(response.data)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        #print('::: RESPONSE DATA - JSON :::')
        #print(json_response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    #-----------------------------------------------------------------------------
    @patch('analytics.reporte_mermas_tiempo.get_mermas_tiempo')
    def test_reporte_error(self, mock_reporte):

        """
        -----------------------------------------------------------------------
        Test para el endpoint 'get_reporte_mermas_tiempo'
        Testear cuando ocurre un error
        -----------------------------------------------------------------------
        """

        mock_reporte.return_value = {'status': 'error',}

        # Construimos el request
        parametros = {
            'almacen_id': self.barra_1.id,
            'fecha_inicial': self.fecha_inicial,
            'fecha_final': self.fecha_final
        }
        url = reverse('analytics:get-reporte-mermas-tiempo', kwargs=parametros)
        response = self.client.get(url)
        #json_response = json.dumps(response.data)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        #print('::: RESPONSE DATA - JSON :::')
        #print(json_response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'error')
