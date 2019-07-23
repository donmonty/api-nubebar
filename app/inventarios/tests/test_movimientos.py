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
    #@patch('inventarios.scrapper.get_data_sat')
    def test_get_marbete_sat_folio_existente(self):
        """
        Test para endpoint 'get_marbete_sat'
        - Testear cuando escaneamos una botella que ya es parte del inventario
        """

        # Tomamos el folio de una botella que ya exista en nuestro inventario
        folio = self.botella_licor43.folio
        # Hacemos el request
        url = reverse('inventarios:get-marbete-sat', args=[folio])
        response = self.client.get(url)
        #json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        # Checamos que los datos del request sean los esperados
        self.assertEqual(response.data['mensaje'], 'Esta botella ya es parte del inventario.')


    #-----------------------------------------------------------------------------
    @patch('inventarios.scrapper.get_data_sat')
    def test_get_marbete_sat_error(self, mock_scrapper):
        """
        Test para endpoint 'get_marbete_sat'
        - Testear cuando el scrapper notifica que hubo problemas en la conexión con el SAT
        """

        # Definimos la respuesta simulada del scrapper
        mock_scrapper.return_value = {
            'status': '0'
        }

        # Hacemos el request
        folio_sat = 'Ii9999999999'
        url = reverse('inventarios:get-marbete-sat', args=[folio_sat])
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
    def test_crear_botella_ok(self):
        """
        Test para el endpoint 'crear_botella'
        - Testear que se da de alta con éxito una botella en un almacén específico
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

        botella_creada = models.Botella.objects.get(id=response.data['id'])

        # for key in payload.keys():
        #     if key not in keys_excluidas:
        #         self.assertEqual(payload[key], getattr(botella_creada, key))

        # Checamos que el resto de los atributos de la botella sean iguales a los del payload
        self.assertEqual(payload['usuario_alta'], botella_creada.usuario_alta.id)
        self.assertEqual(payload['sucursal'], botella_creada.sucursal.id)
        self.assertEqual(payload['almacen'], botella_creada.almacen.id)
        self.assertEqual(payload['producto'], botella_creada.producto.id)
        self.assertEqual(payload['proveedor'], botella_creada.proveedor.id)


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
    def test_crear_producto(self):
        """
        Test para el viewset ProductoViewSet
        - Testear que se crea un Producto OK
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
            'precio_unitario': 350.50,
            'ingrediente': self.licor_43.id

        }
        json_payload = json.dumps(payload)
        #print('::: JSON PAYLOAD :::')
        #print(json_payload)


        # Construimos el request
        url = reverse('inventarios:producto-list')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)

        producto_creado = models.Producto.objects.get(id=response.data['id'])

        # Checamos el status del response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Checamos que el campo de 'ingrediente' sea correcto
        self.assertEqual(response.data['ingrediente'], self.licor_43.id)


    #-----------------------------------------------------------------------------
    def test_crear_producto_error_peso_cristal(self):
        """
        Test para el viewset ProductoViewSet
        - Testear que no e puede crear un Producto sin ingresar el 'peso_cristal'
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

            'peso_cristal': '',
            'precio_unitario': 350.50,
            'ingrediente': self.licor_43.id

        }

        # Construimos el request
        url = reverse('inventarios:producto-list')
        response = self.client.post(url, payload)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)
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
