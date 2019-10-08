from django.test import TestCase
from django.db.models import F, Q, QuerySet, Avg, Count, Sum, Subquery, OuterRef, Exists
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIClient
from rest_framework import serializers

from core import models
from inventarios.serializers import (
                                        ItemInspeccionPostSerializer,
                                        InspeccionPostSerializer,
                                        InspeccionDetalleSerializer,
                                        InspeccionListSerializer,
                                        ItemInspeccionDetalleSerializer,
                                        BotellaItemInspeccionSerializer,
                                        SucursalSerializer,
                                        SucursalDetalleSerializer,
                                        InspeccionUpdateSerializer,
                                        ProductoIngredienteSerializer,
                                        CategoriaSerializer,
                                        CategoriaIngredientesSerializer,
                                        BotellaPostSerializer,
                                        BotellaConsultaSerializer,
                                        ProveedorSerializer,
                                        BotellaProductoSerializer,
                                    )

import datetime
import json
from freezegun import freeze_time

#-----------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------

class MovimientosTests(TestCase):
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
        # Almacen
        self.barra_1 = models.Almacen.objects.create(nombre='BARRA 1', numero=1, sucursal=self.magno_brasserie)
        # Caja
        self.caja_1 = models.Caja.objects.create(numero=1, nombre='CAJA 1', almacen=self.barra_1)

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
        self.categoria_ginebra = models.Categoria.objects.create(nombre='GINEBRA')
        self.categoria_vino_tinto = models.Categoria.objects.create(nombre='VINO TINTO')

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
        self.siete_leguas_blanco = models.Ingrediente.objects.create(
            codigo='TEQU010',
            nombre='SIETE LEGUAS BLANCO',
            categoria=self.categoria_tequila,
            factor_peso=0.95
        )
        self.siete_leguas_reposado = models.Ingrediente.objects.create(
            codigo='TEQU011',
            nombre='SIETE LEGUAS REPOSADO  ',
            categoria=self.categoria_tequila,
            factor_peso=0.95
        )
        self.larios = models.Ingrediente.objects.create(
            codigo='GINE001',
            nombre='LARIOS',
            categoria=self.categoria_ginebra,
            factor_peso=0.95
        )
        self.balero = models.Ingrediente.objects.create(
            codigo='VTIN001',
            nombre='BALERO',
            categoria=self.categoria_vino_tinto,
            factor_peso=0.98
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

        # Ingredientes-Recetas
        self.ir_licor_43 = models.IngredienteReceta.objects.create(receta=self.trago_licor_43, ingrediente=self.licor_43, volumen=60)
        self.ir_herradura_blanco = models.IngredienteReceta.objects.create(receta=self.trago_herradura_blanco, ingrediente=self.herradura_blanco, volumen=60)
        self.ir_jw_black = models.IngredienteReceta.objects.create(receta=self.trago_jw_black, ingrediente=self.jw_black, volumen=60)
        self.ir_carajillo = models.IngredienteReceta.objects.create(receta=self.carajillo, ingrediente=self.licor_43, volumen=45)


        # Ventas
        self.venta_licor43 = models.Venta.objects.create(
            receta=self.trago_licor_43,
            sucursal=self.magno_brasserie,
            fecha=self.ayer,
            unidades=1,
            importe=120,
            caja=self.caja_1
        )

        self.venta_herradura_blanco = models.Venta.objects.create(
            receta=self.trago_herradura_blanco,
            sucursal=self.magno_brasserie,
            fecha=self.ayer,
            unidades=1,
            importe=90,
            caja=self.caja_1
        )

        # Consumos Recetas Vendidas
        self.cr_licor43 = models.ConsumoRecetaVendida.objects.create(
            ingrediente=self.licor_43,
            receta=self.trago_licor_43,
            venta=self.venta_licor43,
            fecha=self.ayer,
            volumen=60
        ) 

        self.cr_herradura_blanco = models.ConsumoRecetaVendida.objects.create(
            ingrediente=self.herradura_blanco,
            receta=self.trago_herradura_blanco,
            venta=self.venta_herradura_blanco,
            fecha=self.ayer,
            volumen=60
        )

        # Productos
        self.producto_licor43 = models.Producto.objects.create(
            folio='Ii0000000001',
            codigo_barras='8410221110075',
            ingrediente=self.licor_43,
            peso_cristal = 500,
            capacidad=750,
            nombre_marca='LICOR 43',
        )

        self.producto_herradura_blanco = models.Producto.objects.create(
            folio='Nn0000000001',
            ingrediente=self.herradura_blanco,
            peso_cristal = 500,
            capacidad=700,
        )

        self.producto_siete_leguas_blanco_1000_01 = models.Producto.objects.create(
            folio='Nn1831940434',
            ingrediente=self.siete_leguas_blanco,
            peso_nueva=1550,
            peso_cristal=600,
            capacidad=1000,
            nombre_marca='Siete Leguas',
            tipo_producto="Tequila joven o blanco 100{} agave".format('%'),
            fecha_envasado='11-07-2019',
        )

        self.producto_siete_leguas_blanco_1000_02 = models.Producto.objects.create(
            folio='Nn1831731407',
            ingrediente=self.siete_leguas_blanco,
            peso_cristal=600,
            capacidad=1000,
            nombre_marca='Siete Leguas',
            tipo_producto="Tequila joven o blanco 100{} agave".format('%'),
            fecha_envasado='11-07-2019',
        )

        self.producto_siete_leguas_blanco_750_01 = models.Producto.objects.create(
            folio='Nn1831589065',
            ingrediente=self.siete_leguas_blanco,
            peso_cristal=500,
            capacidad=750,
            nombre_marca='Siete Leguas',
            tipo_producto="Tequila joven o blanco 100{} agave".format('%'),
            fecha_envasado='11-04-2019',
        )

        self.producto_siete_leguas_reposado_1000_01 = models.Producto.objects.create(
            folio='Nn1644803750',
            ingrediente=self.siete_leguas_reposado,
            peso_cristal=600,
            capacidad=1000,
            nombre_marca='Siete Leguas',
            tipo_producto="Tequila reposado 100{} agave".format('%'),
            fecha_envasado='11-07-2019',
        )

        self.producto_larios = models.Producto.objects.create(
            folio='Ii0949090697',
            ingrediente=self.larios,
            peso_cristal=500,
            capacidad=700,
            nombre_marca='LARIOS',
            tipo_producto="Ginebra",
            fecha_importacion='08-04-2019',
        )

        self.producto_balero = models.Producto.objects.create(
            ingrediente=self.balero,
            codigo_barras='503011357383',
            peso_nueva=1241,
            capacidad=750,
        )

        # Botellas
        self.botella_licor43 = models.Botella.objects.create(
            folio='Ii0000000001',
            producto=self.producto_licor43,
            url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0765216599',
            capacidad=750,
            usuario_alta=self.usuario,
            sucursal=self.magno_brasserie,
            almacen=self.barra_1,
            proveedor=self.vinos_america
        )

        self.botella_herradura_blanco = models.Botella.objects.create(
            folio='Nn0000000001',
            producto=self.producto_herradura_blanco,
            url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Nn1727494182',
            capacidad=700,
            usuario_alta=self.usuario,
            sucursal=self.magno_brasserie,
            almacen=self.barra_1,
            proveedor=self.vinos_america
        )

        # Creamos una botella de Herradura Blanco VACIA
        self.botella_herradura_blanco_2 = models.Botella.objects.create(
            folio='Nn0000000002',
            producto=self.producto_herradura_blanco,
            url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Nn1727494182',
            capacidad=700,
            usuario_alta=self.usuario,
            sucursal=self.magno_brasserie,
            almacen=self.barra_1,
            proveedor=self.vinos_america,
            estado='0'
        )

        self.botella_siete_leguas_blanco_1000 = models.Botella.objects.create(
            folio='Nn0000000003',
            producto=self.producto_siete_leguas_blanco_1000_01,
            capacidad=1000,
            peso_nueva=1550,
            usuario_alta=self.usuario,
            sucursal=self.magno_brasserie,
            almacen=self.barra_1,
            proveedor=self.vinos_america,
            nombre_marca='Siete Leguas',
            tipo_producto="Tequila joven o blanco 100{} agave".format('%'),
            fecha_envasado='11-07-2019',
        )

        self.botella_larios = models.Botella.objects.create(
            folio='Ii0000000002',
            producto=self.producto_larios,
            capacidad=700,
            peso_nueva=1165,
            usuario_alta=self.usuario,
            sucursal=self.magno_brasserie,
            almacen=self.barra_1,
            proveedor=self.vinos_america,
            nombre_marca='LARIOS',
            tipo_producto="Ginebra",
            fecha_importacion='11-07-2019',
        )

        
    #-----------------------------------------------------------------------------
    #-----------------------------------------------------------------------------
    #-----------------------------------------------------------------------------


    #-----------------------------------------------------------------------------
    @patch('inventarios.scrapper_2.get_data_sat')
    def test_get_marbete_sat_ok_v2(self, mock_scrapper):
        """
        ---------------------------------------------------------------------------
        Test para el endpoint 'get_marbete_sat_v2'
        - Testear que hay un match de Producto correcto

        ---------------------------------------------------------------------------
        """
        # Definimos el output simulado del scrapper
        mock_scrapper.return_value = {
            'marbete': 
                {
                    'folio': 'Nn7777777777',
                    'nombre_marca': 'Siete Leguas',
                    'capacidad': 1000,
                    'tipo_producto': "Tequila joven o blanco 100{} agave".format('%'),
                    'fecha_envasado': '11-07-2019'
                },
            'status': '1'
        }

        # Tomamos el producto registrado que debe hacer match con la busqueda y lo serializamos
        serializer = ProductoIngredienteSerializer(self.producto_siete_leguas_blanco_1000_02)
        json_serializer = json.dumps(serializer.data)
        #print('::: SERIALIZER DATA - PRODUCTO INGREDIENTE :::')
        #print(serializer.data)
        #print(json_serializer)

        # Hacemos el request
        #url_sat = 'http://www.sat.gob.mx'
        folio_sat = mock_scrapper.return_value['marbete']['folio']
        url = reverse('inventarios:get-marbete-sat-v2', args=[folio_sat])
        response = self.client.get(url)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        output_esperado = {
            'data_marbete': mock_scrapper.return_value['marbete'],
            'producto': serializer.data
        }
        json_output_esperado = json.dumps(output_esperado)

        # Checamos que el request sea exitoso
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que los datos del response sean correctos
        self.assertEqual(response.data['data_marbete']['folio'], mock_scrapper.return_value['marbete']['folio'])
        # Checamos que el  ingrediente del Producto del match sea el correcto 
        self.assertEqual(response.data['producto']['ingrediente']['nombre'], self.siete_leguas_blanco.nombre)
        # Checamos que el Producto retornado en el response sea el match esperado
        self.assertEqual(response.data['producto']['folio'], self.producto_siete_leguas_blanco_1000_02.folio)
        # Checamos que todos los demas datos del response sean los esperados
        self.assertEqual(json_output_esperado, json_response)

    
    #-----------------------------------------------------------------------------
    @patch('inventarios.scrapper_2.get_data_sat')
    def test_get_marbete_sat_importado_ok_v2(self, mock_scrapper):
        """
        ---------------------------------------------------------------------------
        Test para el endpoint 'get_marbete_sat_v2'
        - Testear que hay un match de Producto Importado correcto

        ---------------------------------------------------------------------------
        """
        # Definimos el output simulado del scrapper
        mock_scrapper.return_value = {
            'marbete': 
                {
                    'folio': 'Ii7777777777',
                    'nombre_marca': 'LARIOS',
                    'capacidad': 700,
                    'tipo_producto': "Ginebra",
                    'fecha_importacion': '08-04-2019'
                },
            'status': '1'
        }

        # Tomamos el producto registrado que debe hacer match con la busqueda y lo serializamos
        serializer = ProductoIngredienteSerializer(self.producto_larios)
        json_serializer = json.dumps(serializer.data)
        #print('::: SERIALIZER DATA - PRODUCTO INGREDIENTE :::')
        #print(serializer.data)
        #print(json_serializer)

        # Hacemos el request
        #url_sat = 'http://www.sat.gob.mx'
        folio_sat = mock_scrapper.return_value['marbete']['folio']
        url = reverse('inventarios:get-marbete-sat-v2', args=[folio_sat])
        response = self.client.get(url)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        output_esperado = {
            'data_marbete': mock_scrapper.return_value['marbete'],
            'producto': serializer.data
        }
        json_output_esperado = json.dumps(output_esperado)

        # Checamos que el request sea exitoso
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que los datos del response sean correctos
        self.assertEqual(response.data['data_marbete']['folio'], mock_scrapper.return_value['marbete']['folio'])
        # Checamos que el  ingrediente del Producto del match sea el correcto 
        self.assertEqual(response.data['producto']['ingrediente']['nombre'], self.larios.nombre)
        # Checamos que el Producto retornado en el response sea el match esperado
        self.assertEqual(response.data['producto']['folio'], self.producto_larios.folio)
        # Checamos que todos los demas datos del response sean los esperados
        self.assertEqual(json_output_esperado, json_response)

    
    #-----------------------------------------------------------------------------
    @patch('inventarios.scrapper_2.get_data_sat')
    def test_get_marbete_sat_error_producto_v2(self, mock_scrapper):
        """
        ---------------------------------------------------------------------------
        Test para el endpoint 'get_marbete_sat_v2'
        - Testear cuando no se encuentra un match de Producto
        - No hay match de 'fecha_envasado'

        ---------------------------------------------------------------------------
        """
        # Definimos el output simulado del scrapper
        mock_scrapper.return_value = {
            'marbete': 
                {
                    'folio': 'Nn7777777777',
                    'nombre_marca': 'Siete Leguas',
                    'capacidad': 1000,
                    'tipo_producto': "Tequila joven o blanco 100{} agave".format('%'),
                    'fecha_envasado': '31-12-2019'
                },
            'status': '1'
        }

        # Hacemos el request
        folio_sat = mock_scrapper.return_value['marbete']['folio']
        url = reverse('inventarios:get-marbete-sat-v2', args=[folio_sat])
        response = self.client.get(url)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        # Checamos que el request sea exitoso
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que los datos del response sean correctos
        self.assertEqual(response.data['mensaje'], 'No se encontro un match de Producto.')


    #-----------------------------------------------------------------------------
    @patch('inventarios.scrapper.get_data_sat')
    def test_get_marbete_sat(self, mock_scrapper):
        """
        Test para endpoint 'get_marbete_sat'
        - Display de datos de marbete y Producto existente OK
        - Testear que hay un match del patrón del folio
        """
        # Creamos un Producto adicional de Licor 43 con fecha anterior para el test
        with freeze_time("2019-05-01"):
            producto_licor43_2 = models.Producto.objects.create(
            folio='Ii0000000002',
            ingrediente=self.licor_43,
            peso_cristal = 500,
            capacidad=750,
            )
        
        # Definimos el output simulado del scrapper
        mock_scrapper.return_value = {
            'marbete': 
                {
                    'folio': 'Ii0000000009',
                    'nombre_marca': 'LICOR 43',
                    'capacidad': 750,
                    'tipo_producto': 'LICORES Y CREMAS',
                },
            'status': '1'
        }

        # Tomamos el producto registrado más reciente y lo serializamos
        serializer = ProductoIngredienteSerializer(self.producto_licor43)
        json_serializer = json.dumps(serializer.data)
        #print('::: SERIALIZER DATA - PRODUCTO INGREDIENTE :::')
        #print(serializer.data)
        #print(json_serializer)

        # Hacemos el request
        #url_sat = 'http://www.sat.gob.mx'
        folio_sat = 'Ii0000000009'
        url = reverse('inventarios:get-marbete-sat', args=[folio_sat])
        response = self.client.get(url)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        output_esperado = {
            'data_marbete': mock_scrapper.return_value['marbete'],
            'producto': serializer.data
        }
        json_output_esperado = json.dumps(output_esperado)

        # Checamos que el request sea exitoso
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que los datos del response sean correctos
        self.assertEqual(response.data['data_marbete']['folio'], mock_scrapper.return_value['marbete']['folio'])
        self.assertEqual(response.data['producto']['ingrediente']['nombre'], self.licor_43.nombre)
        self.assertEqual(json_output_esperado, json_response)


    #-----------------------------------------------------------------------------
    @patch('inventarios.scrapper.get_data_sat')
    def test_get_marbete_sat_patron_nombre(self, mock_scrapper):
        """
        Test para endpoint 'get_marbete_sat'
        - Display de datos de marbete y Producto existente OK
        - Testear que hay un match del patrón del nombre-marca
        """
        # Creamos un Producto adicional de Licor 43 con fecha anterior para el test
        with freeze_time("2019-05-01"):
            producto_licor43_2 = models.Producto.objects.create(
            folio='Ii0000000002',
            ingrediente=self.licor_43,
            peso_cristal = 500,
            capacidad=750,
            nombre_marca='LICOR 43'
            )
        
        # # Definimos el output simulado del scrapper
        mock_scrapper.return_value = {
            'marbete': 
                {
                    'folio': 'Ii9999999999',
                    'nombre_marca': 'LICOR 43',
                    'capacidad': 750,
                    'tipo_producto': 'LICORES Y CREMAS',
                },
            'status': '1'
        }

        # Tomamos el producto registrado más reciente y lo serializamos
        serializer = ProductoIngredienteSerializer(self.producto_licor43)
        json_serializer = json.dumps(serializer.data)
        #print('::: SERIALIZER DATA - PRODUCTO INGREDIENTE :::')
        #print(serializer.data)
        #print(json_serializer)

        # Hacemos el request
        #url_sat = 'http://www.sat.gob.mx'
        folio_sat = 'Ii9999999999'
        url = reverse('inventarios:get-marbete-sat', args=[folio_sat])
        response = self.client.get(url)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        output_esperado = {
            'data_marbete': mock_scrapper.return_value['marbete'],
            'producto': serializer.data
        }
        json_output_esperado = json.dumps(output_esperado)

        # Checamos que el request sea exitoso
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que los datos del response sean correctos
        self.assertEqual(response.data['data_marbete']['folio'], mock_scrapper.return_value['marbete']['folio'])
        self.assertEqual(response.data['producto']['ingrediente']['nombre'], self.licor_43.nombre)
        self.assertEqual(json_output_esperado, json_response)

    # ::: OJO: NO BORRAR ESTE TEST, DEJARLO COMENTADO COMO ESTÁ !!!!!!! ::::
    #-----------------------------------------------------------------------------
    # @patch('inventarios.scrapper.get_data_sat')
    # def test_get_marbete_sat_sin_producto(self, mock_scrapper):
    #     """
    #     Test para endpoint 'get_marbete_sat'
    #     - Testear cuando no se encuentra un Producto que haga match
    #     """
    #     # Creamos un Producto adicional de Licor 43 con fecha anterior para el test
    #     with freeze_time("2019-05-01"):
    #         producto_licor43_2 = models.Producto.objects.create(
    #         folio='Ii0000000002',
    #         ingrediente=self.licor_43,
    #         peso_cristal = 500,
    #         capacidad=750,
    #         nombre_marca='LICOR 43'
    #         )
        
    #     # Definimos el output simulado del scrapper
    #     mock_scrapper.return_value = {
    #         'marbete': 
    #             {
    #                 'folio': 'Ii9999999999',
    #                 'nombre_marca': ' ',
    #                 'capacidad': 750,
    #                 'tipo_producto': 'LICORES Y CREMAS',
    #             },
    #         'status': '1'
    #     }

    #     # Tomamos el producto registrado más reciente y lo serializamos
    #     serializer = ProductoIngredienteSerializer(self.producto_licor43)
    #     json_serializer = json.dumps(serializer.data)
    #     print('::: SERIALIZER DATA - PRODUCTO INGREDIENTE :::')
    #     #print(serializer.data)
    #     print(json_serializer)

    #     # Hacemos el request
    #     #url_sat = 'http://www.sat.gob.mx'
    #     folio_sat = 'Ii9999999999'
    #     url = reverse('inventarios:get-marbete-sat', args=[folio_sat])
    #     response = self.client.get(url)
    #     json_response = json.dumps(response.data)
    #     print('::: RESPONSE DATA :::')
    #     #print(response.data)
    #     print(json_response)

    #     output_esperado = {
    #         'data_marbete': mock_scrapper.return_value['marbete'],
    #         'producto': None
    #     }
    #     json_output_esperado = json.dumps(output_esperado)

    #     # Checamos que el request sea exitoso
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     # Checamos que los datos del response sean correctos
    #     self.assertEqual(response.data['data_marbete']['folio'], mock_scrapper.return_value['marbete']['folio'])
    #     self.assertEqual(response.data['producto'], None)
    #     self.assertEqual(json_output_esperado, json_response)


    #-----------------------------------------------------------------------------
    @patch('inventarios.scrapper.get_data_sat')
    def test_get_marbete_sat_error_producto(self, mock_scrapper):
        """
        Test para el endpoint 'get_marbete_sat'
        - Testear cuando no hubo un match de Producto (ni patrón de folio ni nombre)
        """
        # Definimos el output simulado del scrapper
        mock_scrapper.return_value = {
            'marbete': 
                {
                    'folio': 'Ii9999999999',
                    'nombre_marca': ' ',
                    'capacidad': 750,
                    'tipo_producto': 'LICORES Y CREMAS',
                },
            'status': '1'
        }

        # Hacemos el request
        #url_sat = 'http://www.sat.gob.mx'
        folio_sat = 'Ii9999999999'
        url = reverse('inventarios:get-marbete-sat', args=[folio_sat])
        response = self.client.get(url)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        # Checamos que el request sea exitoso
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que los datos del response sean correctos
        self.assertEqual(response.data['mensaje'], 'No se pudo identificar el producto.')


    #-----------------------------------------------------------------------------
    def test_get_marbete_sat_folio_existente(self):
        """
        ---------------------------------------------------------------------------
        Test para endpoint 'get_marbete_sat_v2'
        - Testear cuando escaneamos una botella que ya es parte del inventario
        ---------------------------------------------------------------------------
        """

        # Tomamos el folio de una botella que ya exista en nuestro inventario
        folio = self.botella_licor43.folio
        # Hacemos el request
        url = reverse('inventarios:get-marbete-sat-v2', args=[folio])
        response = self.client.get(url)
        #json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        # Checamos que los datos del request sean los esperados
        self.assertEqual(response.data['mensaje'], 'Esta botella ya es parte del inventario.')


    #-----------------------------------------------------------------------------
    @patch('inventarios.scrapper_2.get_data_sat')
    def test_get_marbete_sat_error(self, mock_scrapper):
        """
        ---------------------------------------------------------------------------
        Test para endpoint 'get_marbete_sat_v2'
        - Testear cuando el scrapper notifica que hubo problemas en la conexión con el SAT
        ---------------------------------------------------------------------------
        """

        # Definimos la respuesta simulada del scrapper
        mock_scrapper.return_value = {
            'status': '0'
        }

        # Hacemos el request
        folio_sat = 'Ii9999999999'
        url = reverse('inventarios:get-marbete-sat-v2', args=[folio_sat])
        response = self.client.get(url)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        self.assertEqual(response.data['mensaje'], 'Hubo problemas al conectarse con el SAT. Intente de nuevo más tarde.')



    #-----------------------------------------------------------------------------
    def test_get_categorias(self):
        """
        Test para el endpoint 'get_categorias'
        - Testear que se despliega la lista de categorías de destilados disponible
        """

        # Tomamos las categorías disponibles 
        categorias = models.Categoria.objects.all()
        # Serializamos las categorías
        serializer = CategoriaSerializer(categorias, many=True)
        json_serializer = json.dumps(serializer.data)
        #print('::: SERIALIZER DATA :::')
        #print(json_serializer)

        # Construimos el request
        url = reverse('inventarios:get-categorias')
        response = self.client.get(url)
        json_response = json.dumps(response.data)
        #print('::: REPONSE DATA :::')
        #print(json_response)

        # Checamos el status del response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que los datos del response y el serializer sean iguales
        self.assertEqual(response.data, serializer.data)

    
    #-----------------------------------------------------------------------------
    def test_get_ingredientes_categoria(self):
        """
        Test para el endpoint 'get_ingredientes_categoria'
        - Testear que se muestra la categoría seleccionada con sus ingredientes asociados
        """
        # Creamos un ingrediente extra de la categoria TEQUILA
        maestro_dobel = models.Ingrediente.objects.create(
            codigo='TEQU002',
            nombre='MAESTRO DOBEL',
            categoria=self.categoria_tequila,
            factor_peso=0.95
        )

        # Tomamos la categoría TEQUILA y la serializamos
        serializer = CategoriaIngredientesSerializer(self.categoria_tequila)
        json_serializer = json.dumps(serializer.data)
        #print('::: SERIALIZER DATA :::')
        #print(json_serializer)

        # Construimos el request
        url = reverse('inventarios:get-ingredientes-categoria', args=[self.categoria_tequila.id])
        response = self.client.get(url)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)

        # Checamos el status del response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que los datos del response y el serializer sean iguales
        self.assertEqual(response.data, serializer.data)

    
    #-----------------------------------------------------------------------------
    def test_crear_botella_importada_ok(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'crear_botella'
        - Testear que se da de alta con éxito una botella importada, en un almacén específico
        -----------------------------------------------------------------------------
        """

        # Creamos el payload para el request
        payload = {
            'folio': 'Ii0763516458',
            'tipo_marbete': 'Marbete de Importación',
            'fecha_elaboracion_marbete': '16-03-2018',
            'lote_produccion_marbete': 'M00032018',
            'url': 'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0763516458',
            'producto' : self.producto_licor43.id,

            'nombre_marca': 'LICOR 43',
            'tipo_producto': 'Licores y Cremas más de 20% Alc. Vol.',
            'graduacion_alcoholica': '31',
            #'capacidad': '750',
            'origen_del_producto': 'REINO DE ESPAÑA',
            'fecha_importacion': '08-08-2018',
            'numero_pedimento': '184890478001706',
            'nombre_fabricante': 'CASA CUERVO, S.A. DE C.V.',
            'rfc_fabricante': 'CCU870622986',

            'usuario_alta': self.usuario.id,
            'sucursal': self.magno_brasserie.id,
            'almacen': self.barra_1.id,
            'peso_inicial': 1212,
            'proveedor': self.vinos_america.id,
        }

        # Construimos el request
        url = reverse('inventarios:crear-botella')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)
        #print(response.data)

        # Checamos que se haya creado la botella
        self.assertTrue(models.Botella.objects.get(id=response.data['id']))

        # Tomamos la botella recien creada
        botella_creada = models.Botella.objects.get(id=response.data['id'])

        # Checamos que el folio de la botella creada sea igual al del payload
        self.assertEqual(payload['folio'], botella_creada.folio)

        # Checamos que el resto de los atributos de la botella sean iguales a los del payload
        self.assertEqual(payload['usuario_alta'], botella_creada.usuario_alta.id)
        self.assertEqual(payload['sucursal'], botella_creada.sucursal.id)
        self.assertEqual(payload['almacen'], botella_creada.almacen.id)
        self.assertEqual(payload['producto'], botella_creada.producto.id)
        self.assertEqual(payload['proveedor'], botella_creada.proveedor.id)


    #-----------------------------------------------------------------------------
    def test_crear_botella_nacional_ok(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'crear_botella'
        - Testear que se da de alta con éxito una botella nacional, en un almacén específico
        -----------------------------------------------------------------------------
        """

        # Creamos el payload para el request
        payload = {
            'folio': 'Nn1644803750',
            'tipo_marbete': 'Marbete Nacional',
            'fecha_elaboracion_marbete': '20-04-2018',
            'lote_produccion_marbete': 'M00062018',
            'url': 'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Nn1644803750',
            'producto' : self.producto_siete_leguas_reposado_1000_01.id,

            'nombre_marca': 'Siete Leguas',
            'tipo_producto': 'Tequila reposado 100% Agave',
            'graduacion_alcoholica': '38',
            #'capacidad': '750',
            'origen_del_producto': 'ESTADOS UNIDOS MEXICANOS',
            'fecha_envasado': '31-01-2019',
            'lote_produccion': 'L26019',
            'nombre_fabricante': 'TEQUILA SIETE LEGUAS SA DE CV',
            'rfc_fabricante': 'TSL860819L16',

            'usuario_alta': self.usuario.id,
            'sucursal': self.magno_brasserie.id,
            'almacen': self.barra_1.id,
            'peso_inicial': 1212,
            'proveedor': self.vinos_america.id,
        }

        # Construimos el request
        url = reverse('inventarios:crear-botella')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)
        #print(response.data)

        # Checamos que se haya creado la botella
        self.assertTrue(models.Botella.objects.get(id=response.data['id']))

        # Tomamos la botella recien creada
        botella_creada = models.Botella.objects.get(id=response.data['id'])

        # Checamos que el folio de la botella creada sea igual al del payload
        self.assertEqual(payload['folio'], botella_creada.folio)

        # Checamos que el resto de los atributos de la botella sean iguales a los del payload
        self.assertEqual(payload['usuario_alta'], botella_creada.usuario_alta.id)
        self.assertEqual(payload['sucursal'], botella_creada.sucursal.id)
        self.assertEqual(payload['almacen'], botella_creada.almacen.id)
        self.assertEqual(payload['producto'], botella_creada.producto.id)
        self.assertEqual(payload['proveedor'], botella_creada.proveedor.id)


    #-----------------------------------------------------------------------------
    @patch('inventarios.scrapper_2.get_data_sat')
    def test_get_marbete_sat_producto_v2(self, mock_scrapper):
        
        """
        -----------------------------------------------------------------------------
        Test para endpoint 'get_marbete_sat_producto_v2'
        - Display de datos de marbete OK
        -----------------------------------------------------------------------------
        """

        # Definimos el output simulado del scrapper
        mock_scrapper.return_value = {
            'marbete': 
                {
                    'folio': 'Ii7777777777',
                    'nombre_marca': 'LARIOS',
                    'capacidad': 700,
                    'tipo_producto': "Ginebra",
                    'fecha_importacion': '08-04-2019'
                },
            'status': '1'
        }

        # Hacemos el request
        folio_sat = mock_scrapper.return_value['marbete']['folio']
        url = reverse('inventarios:get-marbete-sat-producto-v2', args=[folio_sat])
        response = self.client.get(url)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        # output_esperado = {
        #     'data_marbete': mock_scrapper.return_value,
        # }
        output_esperado = mock_scrapper.return_value
        json_output_esperado = json.dumps(output_esperado)

        # Checamos que el request sea exitoso
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que los datos del response sean correctos
        self.assertEqual(response.data['marbete']['folio'], mock_scrapper.return_value['marbete']['folio'])
        self.assertEqual(json_output_esperado, json_response)

    
    #-----------------------------------------------------------------------------
    @patch('inventarios.scrapper_2.get_data_sat')
    def test_get_marbete_sat_producto_duplicado(self, mock_scrapper):
        
        """
        -----------------------------------------------------------------------------
        Test para endpoint 'get_marbete_sat_producto_v2'
        - Testear cuando el Producto que se quiere dar de alta ya existe en la base de datos
        -----------------------------------------------------------------------------
        """
        # Hacemos el request utilizano un folio de un Producto existente
        folio_sat = 'Ii0949090697'
        url = reverse('inventarios:get-marbete-sat-producto-v2', args=[folio_sat])
        response = self.client.get(url)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(response)
        #print(json_response)

        # Checamos que el status del response sea correcto
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que el mensaje del response sea correcto
        self.assertEqual(response.data['mensaje'], 'Este Producto ya esta registrado.')

    
    #-----------------------------------------------------------------------------
    @patch('inventarios.scrapper_2.get_data_sat')
    def test_get_marbete_sat_producto_error_v2(self, mock_scrapper):
        """
        -----------------------------------------------------------------------------
        Test para endpoint 'get_marbete_sat_producto_v2'
        - Testear cuando el scrapper tiene problemas para conectarse con el SAT
        -----------------------------------------------------------------------------
        """

        # Definimos la respuesta simulada del scrapper
        mock_scrapper.return_value = {
            'status': '0'
        }

        # Construimos el response
        folio_sat = 'Ii0000000009'
        url = reverse('inventarios:get-marbete-sat-producto-v2', args=[folio_sat])
        response = self.client.get(url)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        # Checamos que el response sea el mensaje de error esperado
        self.assertEqual(response.data['mensaje'], 'Hubo un error al conectarse con el SAT. Intente de nuevo más tarde.')


    #-----------------------------------------------------------------------------
    @patch('inventarios.scrapper.get_data_sat')
    def test_get_marbete_sat_producto(self, mock_scrapper):
        """
        Test para endpoint 'get_marbete_sat_producto'
        - Display de datos de marbete OK
        """
        
        # Definimos el output simulado del scrapper
        mock_scrapper.return_value = {
            'marbete': 
                {
                    'folio': 'Ii9999999999',
                    'nombre_marca': 'LICOR 43',
                    'capacidad': 750,
                    'tipo_producto': 'LICORES Y CREMAS',
                },
            'status': '1'
        }

        # Hacemos el request
        #url_sat = 'http://www.sat.gob.mx'
        folio_sat = 'Ii0000000009'
        url = reverse('inventarios:get-marbete-sat-producto', args=[folio_sat])
        response = self.client.get(url)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        # output_esperado = {
        #     'data_marbete': mock_scrapper.return_value,
        # }
        output_esperado = mock_scrapper.return_value
        json_output_esperado = json.dumps(output_esperado)

        # Checamos que el request sea exitoso
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que los datos del response sean correctos
        self.assertEqual(response.data['marbete']['folio'], mock_scrapper.return_value['marbete']['folio'])
        self.assertEqual(json_output_esperado, json_response)


    #-----------------------------------------------------------------------------
    @patch('inventarios.scrapper.get_data_sat')
    def test_get_marbete_sat_producto_error(self, mock_scrapper):
        """
        Test para endpoint 'get_marbete_sat_producto'
        - Testear cuando el scrapper tiene problemas para conectarse con el SAT
        """

        # Definimos la respuesta simulada del scrapper
        mock_scrapper.return_value = {
            'status': '0'
        }

        # Construimos el response
        folio_sat = 'Ii0000000009'
        url = reverse('inventarios:get-marbete-sat-producto', args=[folio_sat])
        response = self.client.get(url)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        # Checamos que el response sea el mensaje de error esperado
        self.assertEqual(response.data['mensaje'], 'Hubo un error al conectarse con el SAT. Intente de nuevo más tarde.')


    #-----------------------------------------------------------------------------
    def test_crear_producto_importado(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'crear_producto'
        - Testear que se crea un Producto importado OK
        -----------------------------------------------------------------------------
        """

        # Creamos el payload para el request
        payload = {
            'folio': 'Ii0763516458',
            'tipo_marbete': 'Marbete de Importación',
            'fecha_elaboracion_marbete': '16-03-2018',
            'lote_produccion_marbete': 'M00032018',
            'url': 'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0763516458',

            'nombre_marca': 'LICOR 43',
            'tipo_producto': 'Licores y Cremas más de 20% Alc. Vol.',
            'graduacion_alcoholica': '31',
            'capacidad': 750,
            'origen_del_producto': 'REINO DE ESPAÑA',
            'fecha_importacion': '08-08-2018',
            'numero_pedimento': '184890478001706',
            'nombre_fabricante': 'CASA CUERVO, S.A. DE C.V.',
            'rfc_fabricante': 'CCU870622986',

            'peso_cristal': 500,
            'precio_unitario': 350.50,
            'ingrediente': self.licor_43.id

        }
        json_payload = json.dumps(payload)
        #print('::: JSON PAYLOAD :::')
        #print(json_payload)


        # Construimos el request
        url = reverse('inventarios:crear-producto')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)

        #producto_creado = models.Producto.objects.get(id=response.data['id'])

        # Checamos el status del response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Checamos que el campo de 'ingrediente' sea correcto
        self.assertEqual(response.data['ingrediente'], self.licor_43.id)
        self.assertTrue(models.Producto.objects.get(id=response.data['id']))

    #-----------------------------------------------------------------------------
    def test_crear_producto_importado_peso_cristal(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'crear_producto_v2'
        - Testear que se crea un Producto importado OK
        - El cliente proporciona el peso del cristal
        -----------------------------------------------------------------------------
        """

        # Creamos el payload para el request
        payload = {
            'folio': 'Ii0763516458',
            'tipo_marbete': 'Marbete de Importación',
            'fecha_elaboracion_marbete': '16-03-2018',
            'lote_produccion_marbete': 'M00032018',
            'url': 'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0763516458',

            'nombre_marca': 'LICOR 43',
            'tipo_producto': 'Licores y Cremas más de 20% Alc. Vol.',
            'graduacion_alcoholica': '31',
            'capacidad': 750,
            'origen_del_producto': 'REINO DE ESPAÑA',
            'fecha_importacion': '08-08-2018',
            'numero_pedimento': '184890478001706',
            'nombre_fabricante': 'CASA CUERVO, S.A. DE C.V.',
            'rfc_fabricante': 'CCU870622986',

            'peso_cristal': 500,
            'precio_unitario': 350.50,
            'ingrediente': self.licor_43.id

        }
        json_payload = json.dumps(payload)
        #print('::: JSON PAYLOAD :::')
        #print(json_payload)


        # Construimos el request
        url = reverse('inventarios:crear-producto-v2')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)

        #producto_creado = models.Producto.objects.get(id=response.data['id'])

        # Checamos el status del response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Checamos que el campo de 'ingrediente' sea correcto
        self.assertEqual(response.data['ingrediente'], self.licor_43.id)
        # Checamos que el Producto se creo
        self.assertTrue(models.Producto.objects.get(id=response.data['id']))

        # Checamos que 'peso_nueva' sea correcto
        capacidad = payload['capacidad']
        peso_cristal = payload['peso_cristal']
        factor_peso = self.licor_43.factor_peso
        peso_nueva = round(peso_cristal + (capacidad * factor_peso))
        self.assertEqual(response.data['peso_nueva'], peso_nueva)


    #-----------------------------------------------------------------------------
    def test_crear_producto_importado_peso_nueva(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'crear_producto_v2'
        - Testear que se crea un Producto importado OK
        - El cliente proporciona el peso de la botella nueva sin tapa
        -----------------------------------------------------------------------------
        """

        # Creamos el payload para el request
        payload = {
            'folio': 'Ii0763516458',
            'tipo_marbete': 'Marbete de Importación',
            'fecha_elaboracion_marbete': '16-03-2018',
            'lote_produccion_marbete': 'M00032018',
            'url': 'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0763516458',

            'nombre_marca': 'LICOR 43',
            'tipo_producto': 'Licores y Cremas más de 20% Alc. Vol.',
            'graduacion_alcoholica': '31',
            'capacidad': 750,
            'origen_del_producto': 'REINO DE ESPAÑA',
            'fecha_importacion': '08-08-2018',
            'numero_pedimento': '184890478001706',
            'nombre_fabricante': 'CASA CUERVO, S.A. DE C.V.',
            'rfc_fabricante': 'CCU870622986',

            'peso_nueva': 1288,
            'precio_unitario': 350.50,
            'ingrediente': self.licor_43.id

        }
        json_payload = json.dumps(payload)
        #print('::: JSON PAYLOAD :::')
        #print(json_payload)


        # Construimos el request
        url = reverse('inventarios:crear-producto-v2')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)

        #producto_creado = models.Producto.objects.get(id=response.data['id'])

        # Checamos el status del response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Checamos que el campo de 'ingrediente' sea correcto
        self.assertEqual(response.data['ingrediente'], self.licor_43.id)
        # Checamos que el Producto se creo
        self.assertTrue(models.Producto.objects.get(id=response.data['id']))

        # Checamos que 'peso_cristal' sea correcto
        capacidad = payload['capacidad']
        peso_nueva = payload['peso_nueva']
        factor_peso = self.licor_43.factor_peso
        peso_cristal = round(peso_nueva - (capacidad * factor_peso))
        self.assertEqual(response.data['peso_cristal'], peso_cristal)


    #-----------------------------------------------------------------------------
    def test_crear_producto_nacional_peso_cristal(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'crear_producto_v2'
        - Testear que se crea un Producto nacional OK
        - El cliente proporciona el peso del cristal
        -----------------------------------------------------------------------------
        """

        # Creamos el payload para el request
        payload = {
            'folio': 'Nn1644803750',
            'tipo_marbete': 'Marbete Nacional',
            'fecha_elaboracion_marbete': '20-04-2018',
            'lote_produccion_marbete': 'M00062018',
            'url': 'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Nn1644803750',

            'nombre_marca': 'Siete Leguas',
            'tipo_producto': 'Tequila reposado 100% Agave',
            'graduacion_alcoholica': '38',
            'capacidad': 750,
            'origen_del_producto': 'ESTADOS UNIDOS MEXICANOS',
            'fecha_envasado': '31-01-2019',
            'lote_produccion': 'L26019',
            'nombre_fabricante': 'TEQUILA SIETE LEGUAS SA DE CV',
            'rfc_fabricante': 'TSL860819L16',

            'peso_cristal': 600,
            'precio_unitario': 350.50,
            'ingrediente': self.siete_leguas_reposado.id

        }
        json_payload = json.dumps(payload)
        #print('::: JSON PAYLOAD :::')
        #print(json_payload)


        # Construimos el request
        url = reverse('inventarios:crear-producto-v2')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)

        #producto_creado = models.Producto.objects.get(id=response.data['id'])

        # Checamos el status del response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Checamos que el campo de 'ingrediente' sea correcto
        self.assertEqual(response.data['ingrediente'], self.siete_leguas_reposado.id)
        # Checamos que el Producto se creo
        self.assertTrue(models.Producto.objects.get(id=response.data['id']))
        
        # Checamos que 'peso_nueva' sea correcto
        capacidad = payload['capacidad']
        peso_cristal = payload['peso_cristal']
        factor_peso = self.siete_leguas_reposado.factor_peso
        peso_nueva = round(peso_cristal + (capacidad * factor_peso))
        self.assertEqual(response.data['peso_nueva'], peso_nueva)

    
    #-----------------------------------------------------------------------------
    def test_crear_producto_nacional_peso_nueva(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'crear_producto_v2'
        - Testear que se crea un Producto nacional OK
        - El cliente proporciona el peso de la botella nueva sin tapa
        -----------------------------------------------------------------------------
        """

        # Creamos el payload para el request
        payload = {
            'folio': 'Nn1644803750',
            'tipo_marbete': 'Marbete Nacional',
            'fecha_elaboracion_marbete': '20-04-2018',
            'lote_produccion_marbete': 'M00062018',
            'url': 'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Nn1644803750',

            'nombre_marca': 'Siete Leguas',
            'tipo_producto': 'Tequila reposado 100% Agave',
            'graduacion_alcoholica': '38',
            'capacidad': 750,
            'origen_del_producto': 'ESTADOS UNIDOS MEXICANOS',
            'fecha_envasado': '31-01-2019',
            'lote_produccion': 'L26019',
            'nombre_fabricante': 'TEQUILA SIETE LEGUAS SA DE CV',
            'rfc_fabricante': 'TSL860819L16',

            'peso_nueva': 1312,
            'precio_unitario': 350.50,
            'ingrediente': self.siete_leguas_reposado.id

        }
        json_payload = json.dumps(payload)
        #print('::: JSON PAYLOAD :::')
        #print(json_payload)


        # Construimos el request
        url = reverse('inventarios:crear-producto-v2')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)

        #producto_creado = models.Producto.objects.get(id=response.data['id'])

        # Checamos el status del response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Checamos que el campo de 'ingrediente' sea correcto
        self.assertEqual(response.data['ingrediente'], self.siete_leguas_reposado.id)
        # Checamos que el Producto se creo
        self.assertTrue(models.Producto.objects.get(id=response.data['id']))
        
        # Checamos que 'peso_cristal' sea correcto
        capacidad = payload['capacidad']
        peso_nueva = payload['peso_nueva']
        factor_peso = self.siete_leguas_reposado.factor_peso
        peso_cristal = round(peso_nueva - (capacidad * factor_peso))
        self.assertEqual(response.data['peso_cristal'], peso_cristal)

    
    #-----------------------------------------------------------------------------
    def test_crear_producto_nacional(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'crear_producto'
        - Testear que se crea un Producto nacional OK
        -----------------------------------------------------------------------------
        """

        # Creamos el payload para el request
        payload = {
            'folio': 'Nn1644803750',
            'tipo_marbete': 'Marbete Nacional',
            'fecha_elaboracion_marbete': '20-04-2018',
            'lote_produccion_marbete': 'M00062018',
            'url': 'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Nn1644803750',

            'nombre_marca': 'Siete Leguas',
            'tipo_producto': 'Tequila reposado 100% Agave',
            'graduacion_alcoholica': '38',
            'capacidad': 750,
            'origen_del_producto': 'ESTADOS UNIDOS MEXICANOS',
            'fecha_envasado': '31-01-2019',
            'lote_produccion': 'L26019',
            'nombre_fabricante': 'TEQUILA SIETE LEGUAS SA DE CV',
            'rfc_fabricante': 'TSL860819L16',

            'peso_cristal': 600,
            'precio_unitario': 350.50,
            'ingrediente': self.siete_leguas_reposado.id

        }
        json_payload = json.dumps(payload)
        #print('::: JSON PAYLOAD :::')
        #print(json_payload)


        # Construimos el request
        url = reverse('inventarios:crear-producto')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)

        #producto_creado = models.Producto.objects.get(id=response.data['id'])

        # Checamos el status del response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Checamos que el campo de 'ingrediente' sea correcto
        self.assertEqual(response.data['ingrediente'], self.siete_leguas_reposado.id)
        self.assertTrue(models.Producto.objects.get(id=response.data['id']))
        


    #-----------------------------------------------------------------------------
    def test_crear_producto_importado_error_peso_cristal(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'crear_producto'
        - Testear que no se puede crear un Producto importado sin ingresar el 'peso_cristal'
        -----------------------------------------------------------------------------
        """

        # Creamos el payload para el request
        payload = {
            'folio': 'Ii0763516458',
            'tipo_marbete': 'Marbete de Importación',
            'fecha_elaboracion_marbete': '16-03-2018',
            'lote_produccion_marbete': 'M00032018',
            'url': 'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0763516458',

            'nombre_marca': 'LICOR 43',
            'tipo_producto': 'Licores y Cremas más de 20% Alc. Vol.',
            'graduacion_alcoholica': '31',
            'capacidad': 750,
            'origen_del_producto': 'REINO DE ESPAÑA',
            'fecha_importacion': '08-08-2018',
            'numero_pedimento': '184890478001706',
            'nombre_fabricante': 'CASA CUERVO, S.A. DE C.V.',
            'rfc_fabricante': 'CCU870622986',

            'peso_cristal': '',
            'precio_unitario': 350.50,
            'ingrediente': self.licor_43.id

        }

        # Construimos el request
        url = reverse('inventarios:crear-producto')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)
        #print(response)
        #print(response.data)

        # Checamos que el status del response sea correcto
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    
    #-----------------------------------------------------------------------------
    def test_crear_producto_importado_error_precio_unitario(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'crear_producto-v2'
        - Testear que no se puede crear un Producto importado sin ingresar el 'precio_unitario'
        -----------------------------------------------------------------------------
        """

        # Creamos el payload para el request
        payload = {
            'folio': 'Ii0763516458',
            'tipo_marbete': 'Marbete de Importación',
            'fecha_elaboracion_marbete': '16-03-2018',
            'lote_produccion_marbete': 'M00032018',
            'url': 'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0763516458',

            'nombre_marca': 'LICOR 43',
            'tipo_producto': 'Licores y Cremas más de 20% Alc. Vol.',
            'graduacion_alcoholica': '31',
            'capacidad': 750,
            'origen_del_producto': 'REINO DE ESPAÑA',
            'fecha_importacion': '08-08-2018',
            'numero_pedimento': '184890478001706',
            'nombre_fabricante': 'CASA CUERVO, S.A. DE C.V.',
            'rfc_fabricante': 'CCU870622986',

            'peso_cristal': 600,
            'precio_unitario': '',
            'ingrediente': self.licor_43.id

        }

        # Construimos el request
        url = reverse('inventarios:crear-producto-v2')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)
        #print(response)
        #print(response.data)

        # Checamos que el status del response sea correcto
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    #-----------------------------------------------------------------------------
    def test_crear_producto_nacional_error_peso_cristal(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'crear_producto'
        - Testear que no se puede crear un Producto nacional sin ingresar el 'peso_cristal'
        -----------------------------------------------------------------------------
        """

        # Creamos el payload para el request
        payload = {
            'folio': 'Nn1644803750',
            'tipo_marbete': 'Marbete Nacional',
            'fecha_elaboracion_marbete': '20-04-2018',
            'lote_produccion_marbete': 'M00062018',
            'url': 'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Nn1644803750',

            'nombre_marca': 'Siete Leguas',
            'tipo_producto': 'Tequila reposado 100% Agave',
            'graduacion_alcoholica': '38',
            'capacidad': 750,
            'origen_del_producto': 'ESTADOS UNIDOS MEXICANOS',
            'fecha_envasado': '31-01-2019',
            'lote_produccion': 'L26019',
            'nombre_fabricante': 'TEQUILA SIETE LEGUAS SA DE CV',
            'rfc_fabricante': 'TSL860819L16',

            'peso_cristal': '',
            'precio_unitario': 350.50,
            'ingrediente': self.siete_leguas_reposado.id

        }

        # Construimos el request
        url = reverse('inventarios:crear-producto')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)
        #print(response)
        #print(response.data)

        # Checamos que el status del response sea correcto
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    #-----------------------------------------------------------------------------
    def test_crear_producto_nacional_error_precio_unitario(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'crear_producto_v2'
        - Testear que no se puede crear un Producto nacional sin ingresar el 'precio_unitario'
        -----------------------------------------------------------------------------
        """

        # Creamos el payload para el request
        payload = {
            'folio': 'Nn1644803750',
            'tipo_marbete': 'Marbete Nacional',
            'fecha_elaboracion_marbete': '20-04-2018',
            'lote_produccion_marbete': 'M00062018',
            'url': 'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Nn1644803750',

            'nombre_marca': 'Siete Leguas',
            'tipo_producto': 'Tequila reposado 100% Agave',
            'graduacion_alcoholica': '38',
            'capacidad': 750,
            'origen_del_producto': 'ESTADOS UNIDOS MEXICANOS',
            'fecha_envasado': '31-01-2019',
            'lote_produccion': 'L26019',
            'nombre_fabricante': 'TEQUILA SIETE LEGUAS SA DE CV',
            'rfc_fabricante': 'TSL860819L16',

            'peso_cristal': 600,
            'precio_unitario': '',
            'ingrediente': self.siete_leguas_reposado.id

        }

        # Construimos el request
        url = reverse('inventarios:crear-producto-v2')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)
        #print(response)
        #print(response.data)

        # Checamos que el status del response sea correcto
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        


    #-----------------------------------------------------------------------------
    def test_crear_producto_error_precio_unitario(self):
        """
        Test para el viewset ProductoViewSet
        - Testear que no se puede crear un Producto sin ingresar el 'precio_unitario'
        """

        # Creamos el payload para el request
        payload = {
            'folio': 'Ii0763516458',
            'tipo_marbete': 'Marbete de Importación',
            'fecha_elaboracion_marbete': '16-03-2018',
            'lote_produccion_marbete': 'M00032018',
            'url': 'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0763516458',

            'nombre_marca': 'LICOR 43',
            'tipo_producto': 'Licores y Cremas más de 20% Alc. Vol.',
            'graduacion_alcoholica': '31',
            'capacidad': 750,
            'origen_del_producto': 'REINO DE ESPAÑA',
            'fecha_importacion': '08-08-2018',
            'nombre_fabricante': 'CASA CUERVO, S.A. DE C.V.',
            'rfc_fabricante': 'CCU870622986',

            'peso_cristal': 500,
            'precio_unitario': '',
            'ingrediente': self.licor_43.id

        }

        # Construimos el request
        url = reverse('inventarios:producto-list')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)

        # Checamos que el status del response sea correcto
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        

    #-----------------------------------------------------------------------------
    def test_crear_traspaso(self):
        """
        Test para el ednpoint 'crear_traspaso'
        - Testear que se crea un Traspaso con éxito
        """

        # Creamos un nuevo almacén para el test
        self.barra_2 = models.Almacen.objects.create(nombre='BARRA 2', numero=2, sucursal=self.magno_brasserie)

        # Construimos el payload
        payload = {
            'almacen': self.barra_2.id,
            'sucursal': self.magno_brasserie,
            'folio': self.botella_licor43.folio,
        }

        # Construimos el request
        url = reverse('inventarios:crear-traspaso')
        response = self.client.post(url, payload)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        # Refrescamos la instancia de la botella
        self.botella_licor43.refresh_from_db()

        #print('::: ALMACEN DE LA BOTELLA :::')
        #print(self.botella_licor43.almacen.id)

        # Checamos el status del response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Checamos que el almacen y sucursal del response sean correctos
        self.assertEqual(response.data['sucursal'], self.magno_brasserie.id)
        self.assertEqual(response.data['almacen'], self.barra_2.id)
        # Checamos que a la botella se le asignó el nuevo almacén con éxito
        self.assertEqual(self.botella_licor43.almacen.id, self.barra_2.id)


    #-----------------------------------------------------------------------------
    def test_crear_traspaso_botella_not_found(self):
        """
        Test para el ednpoint 'crear_traspaso'
        - Testear que no se pueden traspasar botellas que no están registradas
        """

        # Creamos un nuevo almacén para el test
        self.barra_2 = models.Almacen.objects.create(nombre='BARRA 2', numero=2, sucursal=self.magno_brasserie)

        # Construimos el payload
        payload = {
            'almacen': self.barra_2.id,
            'sucursal': self.magno_brasserie,
            'folio': 'Ii0763516458',
        }

        # Construimos el request
        url = reverse('inventarios:crear-traspaso')
        response = self.client.post(url, payload)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        # Checamos el mensaje del response
        self.assertEqual(response.data['mensaje'], 'No se puede hacer el traspaso porque la botella no está registrada.')


    #-----------------------------------------------------------------------------
    def test_crear_traspaso_botella_vacia(self):
        """
        Test para el ednpoint 'crear_traspaso'
        - Testear que no se pueden traspasar botellas que estén vacías o perdidas
        """

        # Creamos un nuevo almacén para el test
        self.barra_2 = models.Almacen.objects.create(nombre='BARRA 2', numero=2, sucursal=self.magno_brasserie)

        # Creamos una botella VACIA para el test
        botella_herradura_blanco_2 = models.Botella.objects.create(
            folio='Nn1727494182',
            producto=self.producto_herradura_blanco,
            url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Nn1727494182',
            capacidad=700,
            usuario_alta=self.usuario,
            sucursal=self.magno_brasserie,
            almacen=self.barra_1,
            proveedor=self.vinos_america,
            estado='0'
        )

        # Construimos el payload
        payload = {
            'almacen': self.barra_2.id,
            'sucursal': self.magno_brasserie,
            'folio': botella_herradura_blanco_2.folio,
        }

        # Construimos el request
        url = reverse('inventarios:crear-traspaso')
        response = self.client.post(url, payload)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        # Checamos el mensaje del response
        self.assertEqual(response.data['mensaje'], 'Esta botella está registrada como VACIA.')


    #-----------------------------------------------------------------------------
    def test_crear_traspaso_botella_perdida(self):
        """
        Test para el ednpoint 'crear_traspaso'
        - Testear que no se pueden traspasar botellas que estén vacías o perdidas
        """

        # Creamos un nuevo almacén para el test
        self.barra_2 = models.Almacen.objects.create(nombre='BARRA 2', numero=2, sucursal=self.magno_brasserie)

        # Creamos una botella PERDIDA para el test
        botella_herradura_blanco_2 = models.Botella.objects.create(
            folio='Nn1727494182',
            producto=self.producto_herradura_blanco,
            url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Nn1727494182',
            capacidad=700,
            usuario_alta=self.usuario,
            sucursal=self.magno_brasserie,
            almacen=self.barra_1,
            proveedor=self.vinos_america,
            estado='3'
        )

        # Construimos el payload
        payload = {
            'almacen': self.barra_2.id,
            'sucursal': self.magno_brasserie,
            'folio': botella_herradura_blanco_2.folio,
        }

        # Construimos el request
        url = reverse('inventarios:crear-traspaso')
        response = self.client.post(url, payload)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        # Checamos el mensaje del response
        self.assertEqual(response.data['mensaje'], 'Esta botella está registrada como PERDIDA.')


    #-----------------------------------------------------------------------------
    def test_crear_traspaso_mismo_almacen(self):
        """
        Test para el ednpoint 'crear_traspaso'
        - Testear que no se pueden traspasar botellas al almacén al que ya pertenecen
        """

        # Construimos el payload
        payload = {
            'almacen': self.barra_1.id,
            'sucursal': self.magno_brasserie,
            'folio': self.botella_licor43.folio,
        }

        # Construimos el request
        url = reverse('inventarios:crear-traspaso')
        response = self.client.post(url, payload)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        # Checamos el mensaje del response
        self.assertEqual(response.data['mensaje'], 'Esta botella ya es parte de este almacén.')

    
    #-----------------------------------------------------------------------------
    def test_consultar_botella(self):
        """
        Test para el endpoint 'consultar_botella
        - Testear que se consulta el detalle de la botella OK
        """

        folio = self.botella_licor43.folio

        # Serializamos la botella que luego cotejaremos en el response
        serializer = BotellaConsultaSerializer(self.botella_licor43)


        # Construimos el request
        url = reverse('inventarios:consultar-botella', args=[folio])
        response = self.client.get(url)
        json_response = json.dumps(response.data)

        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)


        # Checamos el status del response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que el los datos del response sean iguales a los del serializer
        self.assertEqual(response.data, serializer.data)


    #-----------------------------------------------------------------------------
    def test_consultar_botella_no_registrada(self):
        """
        Test para el endpoint 'consultar_botella
        - Testear cuando se consulta una botella no registrada
        """

        folio = 'Ii0763516458'

        # Construimos el request
        url = reverse('inventarios:consultar-botella', args=[folio])
        response = self.client.get(url)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        # Checamos que el los datos del response sean iguales a los del serializer
        self.assertEqual(response.data['mensaje'], 'Esta botella no está registrada en el inventario.')


    #-----------------------------------------------------------------------------
    def test_crear_ingrediente(self):
        """
        Test para el endpoint 'crear_ingrediente'
        - Testear que se crea un ingrediente OK
        """
        # Construimos el request
        payload = {
            'nombre': 'MAESTRO DOBEL DIAMANTE',
            'codigo': 'TEQU100',
            'categoria': self.categoria_tequila.id,
            'factor_peso': 0.95,
        }

        url = reverse('inventarios:crear-ingrediente')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)

        #print('::: RESPONSE DATA :::')
        #print(json_response)

        ingrediente_creado = models.Ingrediente.objects.get(id=response.data['id'])

        # Checamos el status del response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Checamos que los datos del ingrediente creado estén OK
        self.assertEqual(ingrediente_creado.nombre, payload['nombre'])
        self.assertEqual(ingrediente_creado.codigo, payload['codigo'])
        self.assertEqual(ingrediente_creado.categoria.id, payload['categoria'])


    #-----------------------------------------------------------------------------
    def test_get_proveedores(self):
        """
        Test para el endpoint 'get_proveedores'
        - Testear que se despliega la lista de proveedores
        """

        # Creamos un par de porveedores extra para el Test
        la_playa = models.Proveedor.objects.create(
            nombre='Super La Playa',
            razon_social='Super La PLaya SA de CV',
            rfc='XXXYYYYYYZZZ',
            direccion='Federalismo 750',
            ciudad='Guadalajara'
        )

        la_europea = models.Proveedor.objects.create(
            nombre='La Europea',
            razon_social='La Europea SA de CV',
            rfc='XXXYYYYYYZZZ',
            direccion='Pablo Neruda 1090',
            ciudad='Guadalajara'
        )

        queryset = models.Proveedor.objects.all()
        serializer = ProveedorSerializer(queryset, many=True)

        # Construimos el request
        url = reverse('inventarios:get-proveedores')
        response = self.client.get(url)
        json_response = json.dumps(response.data)

        #print('::: RESPONSE DATA :::')
        #print(json_response)

        # Checamos el status del request
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos los datos del response
        self.assertEqual(response.data, serializer.data)


    #-----------------------------------------------------------------------------
    def test_get_servicios_usuario(self):
        """
        Test para el endpoint 'get_servicios_usuario'
        - Testear que se despliegan los servicios asignados al usuario OK
        """

        url = reverse('inventarios:get-servicios-usuario')
        response = self.client.get(url)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['Movimientos']), 2)
        self.assertEqual(response.data['Movimientos'][0], 'Alta Botella')


    #-----------------------------------------------------------------------------
    def test_get_peso_botella_nueva_ok(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'get_peso_botella_nueva'
        - Testear que se obtiene el peso de la botella nueva cuando el Producto asociado
        ya cuenta con el atributo 'peso_nueva'
        -----------------------------------------------------------------------------
        """

        # Creamos un Producto nuevo para este test sin peso de cristal
        producto_larios = models.Producto.objects.create(
            folio='Ii0949090821',
            ingrediente=self.larios,
            peso_nueva=1165,
            peso_cristal=500,
            capacidad=700,
            nombre_marca='LARIOS',
            tipo_producto="Ginebra",
            fecha_importacion='08-04-2019',
        )

        # Construimos el request
        producto_id = self.producto_larios.id
        url = reverse('inventarios:get-peso-botella-nueva', args=[producto_id])
        response = self.client.get(url)
        #print(response.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que el peso de la botella nueva sea correcto
        self.assertEqual(response.data['data'], 1165)


    #-----------------------------------------------------------------------------
    def test_get_peso_botella_nueva_ok_calculado(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'get_peso_botella_nueva'
        - Testear que se obtiene el peso de la botella nueva cuando el Producto
        asociado no cuenta con 'peso_nueva'
        -----------------------------------------------------------------------------
        """

        # Construimos el request
        producto_id = self.producto_siete_leguas_blanco_1000_01.id
        url = reverse('inventarios:get-peso-botella-nueva', args=[producto_id])
        response = self.client.get(url)
        #print(response.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que el peso de la botella nueva sea correcto
        self.assertEqual(response.data['data'], 1550)


    #-----------------------------------------------------------------------------
    def test_get_peso_botella_nueva_error_peso_cristal(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'get_peso_botella_nueva'
        - Testear cuando el Producto asociado no cuenta con peso de cristal
        -----------------------------------------------------------------------------
        """
        # Creamos un Producto nuevo para este test sin peso de cristal
        producto_larios = models.Producto.objects.create(
            folio='Ii0949090821',
            ingrediente=self.larios,
            #peso_cristal=500,
            capacidad=700,
            nombre_marca='LARIOS',
            tipo_producto="Ginebra",
            fecha_importacion='08-04-2019',
        )


        # Construimos el request
        producto_id = producto_larios.id
        url = reverse('inventarios:get-peso-botella-nueva', args=[producto_id])
        response = self.client.get(url)
        # print(response.data)
        #print(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'El Producto asociado a esta botella no tiene un peso de cristal registrado.')


    #-----------------------------------------------------------------------------
    def test_get_peso_botella_nueva_error_capacidad(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'get_peso_botella_nueva'
        - Testear cuando el Producto asociado no cuenta con capacidad
        -----------------------------------------------------------------------------
        """
        # Creamos un Producto nuevo para este test sin peso de cristal
        producto_larios = models.Producto.objects.create(
            folio='Ii0949090821',
            ingrediente=self.larios,
            peso_cristal=500,
            #capacidad=700,
            nombre_marca='LARIOS',
            tipo_producto="Ginebra",
            fecha_importacion='08-04-2019',
        )


        # Construimos el request
        producto_id = producto_larios.id
        url = reverse('inventarios:get-peso-botella-nueva', args=[producto_id])
        response = self.client.get(url)
        # print(response.data)
        #print(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'El Producto asociado a esta botella no tiene capacidad registrada.')


    #-----------------------------------------------------------------------------
    def test_get_peso_botella_nueva_error_factor(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'get_peso_botella_nueva'
        - Testear cuando el Ingrediente del Producto asociado no cuenta con factor peso
        -----------------------------------------------------------------------------
        """
        # Creamos unnuvo ingrediente para este test sin factor de peso
        ingrediente_larios = models.Ingrediente.objects.create(
            codigo='GINE010',
            nombre='LARIOS',
            categoria=self.categoria_ginebra,
            #factor_peso=0.95
        )

        # Creamos un Producto nuevo para este test sin peso de cristal
        producto_larios = models.Producto.objects.create(
            folio='Ii0949090821',
            ingrediente=ingrediente_larios,
            peso_cristal=500,
            capacidad=700,
            nombre_marca='LARIOS',
            tipo_producto="Ginebra",
            fecha_importacion='08-04-2019',
        )


        # Construimos el request
        producto_id = producto_larios.id
        url = reverse('inventarios:get-peso-botella-nueva', args=[producto_id])
        response = self.client.get(url)
        #print(response.data)
        #print(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'El Ingrediente del Producto asociado a esta botella no tiene factor de peso registrado.')

    #-----------------------------------------------------------------------------
    #-----------------------------------------------------------------------------
    #-----------------------------------------------------------------------------
    #-----------------------------------------------------------------------------
    #-----------------------------------------------------------------------------

    #-----------------------------------------------------------------------------
    def test_get_producto_ok(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'get_producto'
        - Testear que se retornan los datos de un Producto cuando este existe en
        la base de datos
        -----------------------------------------------------------------------------
        """

        # Construimos el request
        codigo_barras = self.producto_licor43.codigo_barras
        url = reverse('inventarios:get-producto', args=[codigo_barras])
        response = self.client.get(url)
        json_response = json.dumps(response.data)

        #print(json_response)

        #print(response.data)

        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['codigo_barras'], codigo_barras)


    #-----------------------------------------------------------------------------
    def test_get_producto_error(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'get_producto'
        - Testear cuando se busca un Producto con un codigo de barras que no existe
        -----------------------------------------------------------------------------
        """

        # Construimos el request
        codigo_barras = '0000000000'
        url = reverse('inventarios:get-producto', args=[codigo_barras])
        response = self.client.get(url)
        json_response = json.dumps(response.data)

        #print(json_response)

        self.assertEqual(response.data['status'], 'error')

    
    #-----------------------------------------------------------------------------
    def test_crear_botella_nueva_con_peso_ok(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'crear_botella_nueva'
        - Testear que se crea con éxito una botella nueva.
        - El payload incluye el peso de la botella tomado con la bascula.
        -----------------------------------------------------------------------------
        """

        # Creamos el payload para el request
        payload = {
            'folio': 'Nn1644803750',
            'producto' : self.producto_siete_leguas_reposado_1000_01.id,
            'usuario_alta': self.usuario.id,
            'sucursal': self.magno_brasserie.id,
            'almacen': self.barra_1.id,
            'peso_nueva': 1550,
            'proveedor': self.vinos_america.id,
        }

        # Construimos el request
        url = reverse('inventarios:crear-botella-nueva')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)
        #print(response.data)

        # Checamos que se haya creado la botella
        self.assertTrue(models.Botella.objects.get(id=response.data['id']))

        # Tomamos la botella recien creada
        botella_creada = models.Botella.objects.get(id=response.data['id'])

        # Checamos que el folio de la botella creada sea igual al del payload
        self.assertEqual(payload['folio'], botella_creada.folio)

        # Checamos que el resto de los atributos de la botella sean iguales a los del payload
        self.assertEqual(payload['usuario_alta'], botella_creada.usuario_alta.id)
        self.assertEqual(payload['sucursal'], botella_creada.sucursal.id)
        self.assertEqual(payload['almacen'], botella_creada.almacen.id)
        self.assertEqual(payload['producto'], botella_creada.producto.id)
        self.assertEqual(payload['proveedor'], botella_creada.proveedor.id)

        # Checamos que el 'peso_nueva' de la botella creada sea igual que el 'peso_nueva' del payload
        self.assertEqual(botella_creada.peso_nueva, payload['peso_nueva'])

        # Checamos que el 'peso_inicial' de la botella creada sea igual al 'peso_nueva' del payload
        self.assertEqual(botella_creada.peso_inicial, payload['peso_nueva'])


    #-----------------------------------------------------------------------------
    def test_crear_botella_nueva_sin_peso_ok(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'crear_botella_nueva'
        - Testear que se crea con éxito una botella nueva.
        - El payload NO incluye el peso de la botella tomado con la bascula.
        -----------------------------------------------------------------------------
        """

        # Creamos el payload para el request
        payload = {
            'folio': 'Nn1467616922',
            'producto' : self.producto_balero.id,
            'usuario_alta': self.usuario.id,
            'sucursal': self.magno_brasserie.id,
            'almacen': self.barra_1.id,
            #'peso_nueva': 1241,
            'proveedor': self.vinos_america.id,
        }

        # Construimos el request
        url = reverse('inventarios:crear-botella-nueva')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)
        #print(response.data)

        # Checamos que se haya creado la botella
        self.assertTrue(models.Botella.objects.get(id=response.data['id']))

        # Tomamos la botella recien creada
        botella_creada = models.Botella.objects.get(id=response.data['id'])

        # Checamos que el folio de la botella creada sea igual al del payload
        self.assertEqual(payload['folio'], botella_creada.folio)

        # Checamos que el resto de los atributos de la botella sean iguales a los del payload
        self.assertEqual(payload['usuario_alta'], botella_creada.usuario_alta.id)
        self.assertEqual(payload['sucursal'], botella_creada.sucursal.id)
        self.assertEqual(payload['almacen'], botella_creada.almacen.id)
        self.assertEqual(payload['producto'], botella_creada.producto.id)
        self.assertEqual(payload['proveedor'], botella_creada.proveedor.id)

        # Checamos que el 'peso_inicial' de la botella sea igual al 'peso_nueva' del blueprint
        self.assertEqual(botella_creada.peso_inicial, self.producto_balero.peso_nueva) 

        # Checamos que el 'peso_nueva' de la botella sea igual al 'peso_nueva' del blueprint
        self.assertEqual(botella_creada.peso_nueva, self.producto_balero.peso_nueva)


    #-----------------------------------------------------------------------------
    def test_crear_botella_nueva_update_blueprint_ok(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'crear_botella_nueva'
        - Testear que al crear una botella nueva y se le asigne el peso de la bascula, 
        tambien se le asigne al blueprint si este no cuenta con 'peso_nueva'
        -----------------------------------------------------------------------------
        """

        # Creamos el payload para el request
        payload = {
            'folio': 'Nn1644803750',
            'producto' : self.producto_siete_leguas_reposado_1000_01.id,
            'usuario_alta': self.usuario.id,
            'sucursal': self.magno_brasserie.id,
            'almacen': self.barra_1.id,
            'peso_nueva': 1550,
            'proveedor': self.vinos_america.id,
        }

        # Construimos el request
        url = reverse('inventarios:crear-botella-nueva')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)
        #print(response.data)

        # Checamos que se haya creado la botella
        self.assertTrue(models.Botella.objects.get(id=response.data['id']))

        # Tomamos la botella recien creada
        botella_creada = models.Botella.objects.get(id=response.data['id'])

        # Checamos que el folio de la botella creada sea igual al del payload
        self.assertEqual(payload['folio'], botella_creada.folio)

        # Checamos que el resto de los atributos de la botella sean iguales a los del payload
        self.assertEqual(payload['usuario_alta'], botella_creada.usuario_alta.id)
        self.assertEqual(payload['sucursal'], botella_creada.sucursal.id)
        self.assertEqual(payload['almacen'], botella_creada.almacen.id)
        self.assertEqual(payload['producto'], botella_creada.producto.id)
        self.assertEqual(payload['proveedor'], botella_creada.proveedor.id)

        # Checamos que el 'peso_nueva' del blueprint sea igual que 'peso_nueva' del payload
        # Para ello tenemos que primero refrescar la instancia del blueprint
        self.producto_siete_leguas_reposado_1000_01.refresh_from_db()
        self.assertEqual(payload['peso_nueva'], self.producto_siete_leguas_reposado_1000_01.peso_nueva) 

    
    #-----------------------------------------------------------------------------
    def test_crear_producto_v3_con_peso_nueva_ok(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'crear_producto_v3'
        - Testear que se crea un producto ok
        - En este caso se incluye el peso  de la botella nueva en el request
        -----------------------------------------------------------------------------
        """

        # Creamos el payload para el request
        payload = {
            'ingrediente': self.licor_43.id,
            'codigo_barras': '8410221110075',
            'nombre': 'LICOR 43 750',
            'capacidad': 750,
            'precio_unitario': 350.50,
            'peso_nueva': 1352
        }

        # Construimos el request
        url = reverse('inventarios:crear-producto-v3')
        response = self.client.post(url, payload)
        #json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)
        #print(response.data)

        # Checamos que se haya creado el producto
        self.assertTrue(models.Producto.objects.get(id=response.data['id']))

        # Tomamos el producto recien creado
        producto_creado = models.Producto.objects.get(id=response.data['id'])

        # Checamos que los atributos del producto sean iguales a los del payload
        self.assertEqual(payload['ingrediente'], producto_creado.ingrediente.id)
        self.assertEqual(payload['codigo_barras'], producto_creado.codigo_barras)
        self.assertEqual(payload['nombre'], producto_creado.nombre_marca)
        self.assertEqual(payload['capacidad'], producto_creado.capacidad)
        self.assertEqual(payload['peso_nueva'], producto_creado.peso_nueva)
        self.assertAlmostEqual(payload['precio_unitario'], float(producto_creado.precio_unitario))
        


    #-----------------------------------------------------------------------------
    def test_crear_producto_v3_sin_peso_nueva_ok(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'crear_producto_v3'
        - Testear que se crea un producto ok
        - En este caso NO se incluye el peso de la botella nueva en el request
        -----------------------------------------------------------------------------
        """

        # Creamos el payload para el request
        payload = {
            'ingrediente': self.licor_43.id,
            'codigo_barras': '8410221110075',
            'nombre': 'LICOR 43 750',
            'capacidad': 750,
            'precio_unitario': 350.50,
            #'peso_nueva': None
        }

        # Construimos el request
        url = reverse('inventarios:crear-producto-v3')
        response = self.client.post(url, payload)
        #json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)
        #print(response.data)

        # Checamos que se haya creado el producto
        self.assertTrue(models.Producto.objects.get(id=response.data['id']))

        # Tomamos el producto recien creado
        producto_creado = models.Producto.objects.get(id=response.data['id'])

        # Checamos que los atributos del producto sean iguales a los del payload
        self.assertEqual(payload['ingrediente'], producto_creado.ingrediente.id)
        self.assertEqual(payload['codigo_barras'], producto_creado.codigo_barras)
        self.assertEqual(payload['nombre'], producto_creado.nombre_marca)
        self.assertEqual(payload['capacidad'], producto_creado.capacidad)
        self.assertAlmostEqual(payload['precio_unitario'], float(producto_creado.precio_unitario))

        # Checamos que el 'peso_nueva' del producto sea None
        self.assertEqual(producto_creado.peso_nueva, None)



    #-----------------------------------------------------------------------------
    @patch('inventarios.scrapper_2.get_data_sat')
    def test_get_match_botella_nacional_ok(self, mock_scrapper):
        """
        ---------------------------------------------------------------------------
        Test para el endpoint 'get_match_botella'
        - Testear que hay un match de Botella nacional correcto

        ---------------------------------------------------------------------------
        """
        # Definimos el output simulado del scrapper
        mock_scrapper.return_value = {
            'marbete': 
                {
                    'folio': 'Nn7777777777',
                    'nombre_marca': 'Siete Leguas',
                    'capacidad': 1000,
                    'tipo_producto': "Tequila joven o blanco 100{} agave".format('%'),
                    'fecha_envasado': '11-07-2019'
                },
            'status': '1'
        }

        # Tomamos la botella registrada que debe hacer match con la busqueda y la serializamos
        serializer = BotellaProductoSerializer(self.botella_siete_leguas_blanco_1000)
        json_serializer = json.dumps(serializer.data)
        #print('::: SERIALIZER DATA - PRODUCTO INGREDIENTE :::')
        #print(serializer.data)
        #print(json_serializer)

        # Hacemos el request
        #url_sat = 'http://www.sat.gob.mx'
        folio_sat = mock_scrapper.return_value['marbete']['folio']
        url = reverse('inventarios:get-match-botella', args=[folio_sat])
        response = self.client.get(url)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        output_esperado = {
            'status': 'success',
            'data': serializer.data
        }
        json_output_esperado = json.dumps(output_esperado)

        #self.assertEqual(1, 1)

        # Checamos que el response sea exitoso
        self.assertEqual(response.data['status'], 'success')
        # Checamos que el id de la botella buscada sea el correcto
        self.assertEqual(response.data['data']['id'], self.botella_siete_leguas_blanco_1000.id)
        # Checamos que todos los demas datos del response sean los esperados
        self.assertEqual(json_output_esperado, json_response)


    #-----------------------------------------------------------------------------
    @patch('inventarios.scrapper_2.get_data_sat')
    def test_get_match_botella_importada_ok(self, mock_scrapper):
        """
        ---------------------------------------------------------------------------
        Test para el endpoint 'get_match_botella'
        - Testear que hay un match de Botella importada correcto

        ---------------------------------------------------------------------------
        """
        # Definimos el output simulado del scrapper
        mock_scrapper.return_value = {
            'marbete': 
                {
                    'folio': 'Ii7777777777',
                    'nombre_marca': 'LARIOS',
                    'capacidad': 700,
                    'tipo_producto': "Ginebra",
                    'fecha_importacion': '11-07-2019'
                },
            'status': '1'
        }

        # Tomamos la botella registrada que debe hacer match con la busqueda y la serializamos
        serializer = BotellaProductoSerializer(self.botella_larios)
        #json_serializer = json.dumps(serializer.data)
        #print('::: SERIALIZER DATA - PRODUCTO INGREDIENTE :::')
        #print(serializer.data)
        #print(json_serializer)

        # Hacemos el request
        #url_sat = 'http://www.sat.gob.mx'
        folio_sat = mock_scrapper.return_value['marbete']['folio']
        url = reverse('inventarios:get-match-botella', args=[folio_sat])
        response = self.client.get(url)
        #json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        output_esperado = {
            'status': 'success',
            'data': serializer.data
        }
        json_output_esperado = json.dumps(output_esperado)

        #self.assertEqual(1, 1)

        # Checamos que el response sea exitoso
        self.assertEqual(response.data['status'], 'success')
        # Checamos que el id de la botella buscada sea el correcto
        self.assertEqual(response.data['data']['id'], self.botella_larios.id)
        # Checamos que todos los demas datos del response sean los esperados
        self.assertEqual(json_output_esperado, json_response)


    
    #-----------------------------------------------------------------------------
    @patch('inventarios.scrapper_2.get_data_sat')
    def test_get_match_botella_error_sat(self, mock_scrapper):
        """
        ---------------------------------------------------------------------------
        Test para el endpoint 'get_match_botella'
        - Testear cuando hay un error de conexion con el SAT

        ---------------------------------------------------------------------------
        """

        # Definimos la respuesta simulada del scrapper
        mock_scrapper.return_value = {
            'status': '0'
        }

        # Construimos el response
        folio_sat = 'Ii0000000009'
        url = reverse('inventarios:get-match-botella', args=[folio_sat])
        response = self.client.get(url)
        #json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        # Checamos que el response sea el mensaje de error esperado
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'Hubo problemas al conectarse con el SAT. Intente de nuevo más tarde.')


    
    #-----------------------------------------------------------------------------
    def test_get_match_botella_error_botella_existente(self):
        """
        ---------------------------------------------------------------------------
        Test para el endpoint 'get_match_botella'
        - Testear cuando la botella consultada ya existe en la base de datos

        ---------------------------------------------------------------------------
        """

        # Construimos el response
        folio_sat = 'Ii0000000001'
        url = reverse('inventarios:get-match-botella', args=[folio_sat])
        response = self.client.get(url)
        #json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        # Checamos que el response sea el correcto
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'Esta botella ya es parte del inventario.')


    #-----------------------------------------------------------------------------
    @patch('inventarios.scrapper_2.get_data_sat')
    def test_get_match_botella_error_match(self, mock_scrapper):
        """
        ---------------------------------------------------------------------------
        Test para el endpoint 'get_match_botella'
        - Testear cuando no e encuentra un match de Botella

        ---------------------------------------------------------------------------
        """
        # Definimos el output simulado del scrapper
        mock_scrapper.return_value = {
            'marbete': 
                {
                    'folio': 'Ii7777777777',
                    'nombre_marca': 'LARIOS',
                    'capacidad': 700,
                    'tipo_producto': "Ginebra",
                    'fecha_importacion': '01-01-2019' # Cambiamos la fecha de importacion para que no haya match
                },
            'status': '1'
        }

        # Construimos el request
        folio_sat = mock_scrapper.return_value['marbete']['folio']
        url = reverse('inventarios:get-match-botella', args=[folio_sat])
        response = self.client.get(url)
        #json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        # Checamos que el response sea el correcto
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'No se encontro un match de Botella.')


    #-----------------------------------------------------------------------------
    def test_crear_botella_usada_ok(self):
        """
        -----------------------------------------------------------------------------
        Test para el endpoint 'crear_botella_usada'
        - Testear que se crea con éxito una botella usada.
        -----------------------------------------------------------------------------
        """

        # Creamos el payload para el request
        payload = {
            'folio': 'Nn1644803750',
            'producto' : self.producto_siete_leguas_reposado_1000_01.id,
            'usuario_alta': self.usuario.id,
            'sucursal': self.magno_brasserie.id,
            'almacen': self.barra_1.id,
            'peso_nueva': 1550,
            'peso_bascula': 1000,
            'proveedor': self.vinos_america.id,
        }

        # Construimos el request
        url = reverse('inventarios:crear-botella-usada')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)
        #print(response.data)

        # Checamos que se haya creado la botella
        self.assertTrue(models.Botella.objects.get(id=response.data['id']))

        # Tomamos la botella recien creada
        botella_creada = models.Botella.objects.get(id=response.data['id'])

        # Checamos que el folio de la botella creada sea igual al del payload
        self.assertEqual(payload['folio'], botella_creada.folio)

        # Checamos que el resto de los atributos de la botella sean iguales a los del payload
        self.assertEqual(payload['usuario_alta'], botella_creada.usuario_alta.id)
        self.assertEqual(payload['sucursal'], botella_creada.sucursal.id)
        self.assertEqual(payload['almacen'], botella_creada.almacen.id)
        self.assertEqual(payload['producto'], botella_creada.producto.id)
        self.assertEqual(payload['proveedor'], botella_creada.proveedor.id)

        # Checamos que el 'peso_nueva' de la botella creada sea igual que el 'peso_nueva' del payload
        self.assertEqual(botella_creada.peso_nueva, payload['peso_nueva'])

        # Checamos que el 'peso_inicial' de la botella creada sea igual al 'peso_bascula' del payload
        self.assertEqual(botella_creada.peso_inicial, payload['peso_bascula'])

        # Checamos que el estado de la botella creada sea '1', o sea, usada
        self.assertEqual(botella_creada.estado, '1')


