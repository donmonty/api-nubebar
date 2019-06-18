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
                                        ProductoIngredienteSerializer
                                    )

import datetime
import json
from freezegun import freeze_time


INSPECCIONES_URL = reverse('inventarios:inspecciones-list')


def url_params(parametros):
    """Construye un url con los query_params del request"""

    return reverse('inventarios:get_inspecciones-list', kwargs=parametros)


class InspeccionesTests(TestCase):
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

       

    #--------------------------------------------------------------------------
    def test_crear_inspeccion(self):
        """ Testear que se crea una inspección de forma exitosa """

        with freeze_time("2019-04-30"): 
            #print('::: INICIO DEL TEST :::')
            #assert datetime.datetime.now() != datetime.datetime(2019, 5, 2)
            #mock_now.return_value = yesterday
            # Creamos una inspección previa
            inspeccion_previa = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario_2,
                estado='1'
            )

        # print('::: TEST: DATOS INSPECCION PREVIA :::')
        # print(inspeccion_previa.estado)
        # print(inspeccion_previa.fecha_alta)
        # print(inspeccion_previa.usuario_alta)
        # print('::: TEST: REPR INSPECCION PREVIA :::')
        # print(inspeccion_previa)

        payload = {
            'almacen': self.barra_1.id,
            'sucursal': self.magno_brasserie.id,
            'usuario_alta': self.usuario.id
        }

        # Hacemos un POST con los datos del payload
        res = self.client.post(INSPECCIONES_URL, payload)
        #print('::: TEST: DATOS DEL RESPONSE :::')
        #print(res.data)

        # Tomamos la inspección creada con el POST
        inspeccion = models.Inspeccion.objects.get(id=res.data['id'])
        # print('::: TEST: INSPECCION DEL RESPONSE')
        # print(inspeccion)
        # print('::: TEST: ITEMS INSPECCIONADOS DEL RESPONSE')
        # print(inspeccion.items_inspeccionados.all())
        # Tomamos los ItemInspeccion de la inspección creada
        items_inspeccionados = inspeccion.items_inspeccionados.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(inspeccion.items_inspeccionados.count(), 2)

    # #------------------------------------------------------------------------
    # def  test_crear_inspeccion_fecha_error(self):
    #     """
    #     Testear que se produce un error cuando se intenta crear una nueva
    #     inspección en una fecha no válida.
    #     """ 
    #     #print('::: INICIO DEL TEST :::')
           
    #     # Creamos una inspección previa con fecha de hoy
    #     inspeccion_previa = models.Inspeccion.objects.create(
    #         almacen=self.barra_1,
    #         sucursal=self.magno_brasserie,
    #         usuario_alta=self.usuario,
    #         estado='1'
    #     )

    #     # Creamos un payload con la misma fecha que la inspección previa
    #     payload = {
    #         'almacen': self.barra_1.id,
    #         'sucursal': self.magno_brasserie.id,
    #         'usuario_alta': self.usuario.id
    #     }

    #     # Hacemos un POST con los datos del payload
    #     res = self.client.post(INSPECCIONES_URL, payload)
    #     #print('::: TEST: DATOS DEL RESPONSE :::')
    #     #print(res.data)

    #     self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    
    # def test_crear_inspeccion_estado_abierta(self):
    #     """
    #     Testear que no se puede crear una inspección nueva cuando la anterior
    #     sigue abierta
    #     """

    #     #print('::: INICIO DEL TEST :::')
    #     # Creamos una inspección previa con fecha congelada y estado 'ABIERTA'
    #     with freeze_time("2019-04-30"): 
    #         #print('::: INICIO DEL TEST :::')
    #         #assert datetime.datetime.now() != datetime.datetime(2019, 5, 2)
    #         #mock_now.return_value = yesterday
    #         # Creamos una inspección previa
    #         inspeccion_previa = models.Inspeccion.objects.create(
    #             almacen=self.barra_1,
    #             sucursal=self.magno_brasserie,
    #             usuario_alta=self.usuario_2,
    #             estado='0'
    #         )

    #     # Creamos un payload para crear una nueva inspección
    #     payload = {
    #         'almacen': self.barra_1.id,
    #         'sucursal': self.magno_brasserie.id,
    #         'usuario_alta': self.usuario.id
    #     }

    #     # Hacemos un POST request con los datos del payload
    #     res = self.client.post(INSPECCIONES_URL, payload)
    #     #print('::: TEST: DATOS DEL RESPONSE :::')
    #     #print(res.data)

    #     # Checamos que hubo un error
    #     self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    # def test_crear_inspeccion_primera_vez(self):
    #     """
    #     Testear que se crea la primera inspección ever
    #     (cuando no existen inspecciones previas)
    #     """

    #     print('::: INICIO DEL TEST :::')
    #     # Creamos un payload para crear una nueva inspección
    #     payload = {
    #         'almacen': self.barra_1.id,
    #         'sucursal': self.magno_brasserie.id,
    #         'usuario_alta': self.usuario.id
    #     }

    #     # Hacemos un POST request con los datos del payload
    #     res = self.client.post(INSPECCIONES_URL, payload)

    #     # Tomamos la inspección creada con el POST
    #     inspeccion = models.Inspeccion.objects.get(id=res.data['id'])
    #     #print('::: TEST: INSPECCION DEL RESPONSE')
    #     #print(inspeccion)
    #     #print('::: TEST: ITEMS INSPECCIONADOS DEL RESPONSE')
    #     #print(inspeccion.items_inspeccionados)
    #     # Tomamos los ItemInspeccion de la inspección creada
    #     items_inspeccionados = inspeccion.items_inspeccionados.all()

    #     self.assertEqual(res.status_code, status.HTTP_201_CREATED)
    #     self.assertEqual(inspeccion.items_inspeccionados.count(), 2)



    """
    def test_crear_inspeccion_function(self):
        #Testear que se crea una inspección de forma exitosa

        # Creamos la fecha de ayer
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)

        # Obtenemos la info para el payload
        sucursal_id = self.magno_brasserie.id
        almacen_id = self.barra_1.id
        usuario_id = self.usuario.id

        # Mockeamos 'now' para poder crear una inspección previa con fecha de ayer
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = yesterday
            # Creamos una inspección previa
            inspeccion_previa = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario
            )

        payload = {
            'almacen': almacen_id,
            'sucursal': sucursal_id,
            'usuario_alta': usuario_id
        }

        # Hacemos un POST con los datos del payload
        url = reverse('inventarios:crear_inspeccion')
        res = self.client.post(url, payload)
        print('::: DATOS DEL RESPONSE :::')
        print(res.data)

        # Tomamos la inspección creada con el POST
        inspeccion = models.Inspeccion.objects.get(res.data['id'])
        # Tomamos los ItemInspeccion de la inspección creada
        items_inspeccionados = inspeccion.items_inspeccionados.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(items_inspeccionados.count(), 2)
    """

    #--------------------------------------------------------------------------
    def test_inspeccionpost_serializer(self):
        #Testear que el serialializer InspeccionPostSerializer funciona ok

        # Usamos freeze gun para controlar la fecha de creación de la inspección previa
        with freeze_time("2019-04-30"):
            assert datetime.datetime.now() != datetime.datetime(2019, 5, 1)
            inspeccion_previa = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                estado = '1'
            )
            #print('::: INSPECCION PREVIA :::')
            #print(inspeccion_previa)

        botellas = [self.botella_herradura_blanco, self.botella_licor43]
        fecha_ultima_inspeccion = inspeccion_previa.fecha_alta
        estado_ultima_inspeccion = inspeccion_previa.estado
        usuario = self.usuario

        context = {
            'lista_botellas_inspeccionar': botellas,
            'fecha_ultima_inspeccion': fecha_ultima_inspeccion,
            'estado_ultima_inspeccion': estado_ultima_inspeccion,
            #'usuario': usuario
        }
        #print('::: CONTEXTO :::')
        #print(context)
        payload = {
            'almacen': self.barra_1.id,
            'sucursal': self.magno_brasserie.id,
            #'usuario_alta': self.usuario.id
        }

        # Creamos un diccionario con los datos de una inspeccion para comparar sus atributos con los del serializer
        inspeccion_test = {
            'almacen': self.barra_1.id,
            'sucursal': self.magno_brasserie.id,
            #'usuario_alta': self.usuario.id,
            'items_inspeccionados':
                [
                    {
                        'inspeccion': 1,
                        'botella': self.botella_herradura_blanco.id
                    },
                    {
                        'inspeccion': 1,
                        'botella': self.botella_licor43.id
                    }
                ]
        }

        serializer = InspeccionPostSerializer(data=payload, context=context)
        serializer.is_valid()
        #print(serializer.is_valid())
        #print(serializer.errors)
        serializer.save()
        #print('::: SERIALIZER DATA :::')
        #print(serializer.data)
    
        inspecciones = models.Inspeccion.objects.all()
        lista_items_inspeccion = models.ItemInspeccion.objects.all()
        #print('::: INSPECCIONES :::')
        #print(inspecciones)
        #print('::: ITEMS A INSPECCIONAR :::')
        #print(lista_items_inspeccion)

        data = serializer.data

        self.assertEqual(data['almacen'], inspeccion_test['almacen'])
        self.assertEqual(data['sucursal'], inspeccion_test['sucursal'])
        #self.assertEqual(data['usuario_alta'], inspeccion_test['usuario_alta'])

    
    #--------------------------------------------------------------------------
    def test_inspeccionespost_serializer_botellas_none(self):
        """
        Testear que no se crea la inspección si no hay botellas
        para inspeccionar
        """

        # Creamos la inspección previa con fecha fecha congelada
        with freeze_time("2019-04-30"):
            assert datetime.datetime.now() != datetime.datetime(2019, 5, 1)
            inspeccion_previa = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                estado = '1'
            )

        botellas = None
        fecha_ultima_inspeccion = inspeccion_previa.fecha_alta
        estado_ultima_inspeccion = inspeccion_previa.estado
        usuario = self.usuario

        context = {
            'lista_botellas_inspeccionar': botellas,
            'fecha_ultima_inspeccion': fecha_ultima_inspeccion,
            'estado_ultima_inspeccion': estado_ultima_inspeccion,
            'usuario': usuario
        }

        payload = {
            'almacen': self.barra_1.id,
            'sucursal': self.magno_brasserie.id,
            'usuario_alta': self.usuario.id
        }

        serializer = InspeccionPostSerializer(data=payload, context=context)
        serializer.is_valid()
        #print(serializer.is_valid())
        #print(serializer.errors)
        
        with self.assertRaises(serializers.ValidationError):
            serializer.save()

        #print('::: SERIALIZER DATA :::')
        #print(serializer.data)


    #--------------------------------------------------------------------------
    def test_lista_inspecciones(self):
        """ Testear el display de la lista de inspecciones """

        # Creamos dos inspecciones para el test 
        with freeze_time("2019-05-01"): 
            # Inspección 1
            inspeccion_1 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1' # CERRADA
            )
            item_inspeccion_1a = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_herradura_blanco,
                peso_botella = 1212
            )
            item_inspeccion_1b = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212
            )

        # Inspeccion 2
        with freeze_time("2019-05-02"):
            inspeccion_2 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1' # CERRADA
            )
            item_inspeccion_2a = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_2,
                botella=self.botella_herradura_blanco,
                peso_botella = 1212
            )
            item_inspeccion_2b = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_2,
                botella=self.botella_licor43,
                peso_botella = 1212
            )
        
        # parametros = {
        #     #'sucursal_id': self.magno_brasserie.id,
        #     'almacen_id': self.barra_1.id
        # }

        inspecciones = models.Inspeccion.objects.all().order_by('-fecha_alta')
        #lista_inspecciones = [inspeccion.almacen.id for inspeccion in inspecciones]
        #print('::: LISTA DE INSPECCIONES :::')
        #print(lista_inspecciones)

        #url = url_params(parametros)
        #url = reverse('inventarios:get-inspecciones', kwargs=parametros)
        #url = reverse('inventarios:lista-inspecciones', kwargs=parametros)
        url = reverse('inventarios:get-inspecciones-list', args=[self.barra_1.id])
        #print('::: URL - LISTA INSPECCIONES :::')
        #print(url)


        res = self.client.get(url)
        json_response = json.dumps(res.data)
        #print('::: RES DATA - LISTA INSPECCIONES :::')
        #print(json_response)
       
        serializer = InspeccionListSerializer(inspecciones, many=True)
        #print('::: DATA SERIALIZER - LISTA INSPECCIONES :::')
        #print(serializer.data)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


    #--------------------------------------------------------------------------
    def test_lista_inspecciones_totales(self):
        """
        Test para el endpoint 'get-lista-inspecciones' 
        - Testear el display de la lista de inspecciones TOTALES 
        """

        # Creamos dos inspecciones TOTALES para el test 
        with freeze_time("2019-05-01"): 
            # Inspección 1
            inspeccion_1 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1', # CERRADA
                tipo='1',
            )
            item_inspeccion_1a = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_herradura_blanco,
                peso_botella = 1212
            )
            item_inspeccion_1b = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212
            )

        # Inspeccion 2
        with freeze_time("2019-05-02"):
            inspeccion_2 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1', # CERRADA
                tipo='1',
            )
            item_inspeccion_2a = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_2,
                botella=self.botella_herradura_blanco,
                peso_botella = 1212
            )
            item_inspeccion_2b = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_2,
                botella=self.botella_licor43,
                peso_botella = 1212
            )
        
        parametros = {
            #'sucursal_id': self.magno_brasserie.id,
            'almacen_id': self.barra_1.id,
            'tipo_id': '1'
        }

        inspecciones = models.Inspeccion.objects.all().order_by('-fecha_alta')
        #lista_inspecciones = [inspeccion.almacen.id for inspeccion in inspecciones]
        #print('::: LISTA DE INSPECCIONES :::')
        #print(lista_inspecciones)

        #url = url_params(parametros)
        #url = reverse('inventarios:get-inspecciones', kwargs=parametros)
        #url = reverse('inventarios:lista-inspecciones', kwargs=parametros)
        url = reverse('inventarios:get-lista-inspecciones', kwargs=parametros)
        #print('::: URL - LISTA INSPECCIONES :::')
        #print(url)


        res = self.client.get(url)
        json_response = json.dumps(res.data)
        #print('::: RES DATA - LISTA INSPECCIONES :::')
        #print(json_response)
       
        serializer = InspeccionListSerializer(inspecciones, many=True)
        #print('::: DATA SERIALIZER - LISTA INSPECCIONES :::')
        #print(serializer.data)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


    #--------------------------------------------------------------------------
    def test_lista_inspecciones_error_forbidden(self):
        """
        Test para el endpoint 'get-lista-inspecciones' 
        - Testear que el usuario solo tenga acceso a inspecciones de sus sucursales
        asignadas
        """
        # Creamos una nueva sucursal y barra para el test
        atomic_thai = models.Sucursal.objects.create(nombre='ATOMIC THAI', cliente=self.operadora_magno)
        barra_1_atomic = models.Almacen.objects.create(nombre='BARRA 1 ATOMIC', numero=1, sucursal=atomic_thai) 

        # Creamos dos inspecciones TOTALES para el test 
        with freeze_time("2019-05-01"): 
            # Inspección 1
            inspeccion_1 = models.Inspeccion.objects.create(
                almacen=barra_1_atomic,
                sucursal=atomic_thai,
                usuario_alta=self.usuario_2,
                usuario_cierre=self.usuario_2,
                estado='1', # CERRADA
                tipo='1',
            )
            
        parametros = {
            #'sucursal_id': self.magno_brasserie.id,
            'almacen_id': barra_1_atomic.id,
            'tipo_id': '1'
        }

        
        url = reverse('inventarios:get-lista-inspecciones', kwargs=parametros)
        res = self.client.get(url)
        #json_response = json.dumps(res.data)
        #print('::: RES DATA - LISTA INSPECCIONES :::')
        #print(res.data)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['mensaje'], 'No estás autorizado para consultar las inspecciones de esta sucursal.')


    #--------------------------------------------------------------------------
    def test_inspeccion_detalle(self):
        """
        Testear la vista detalle de una Inspeccion
        """

        # Creamos una Inspección para el test con fecha congelada
        with freeze_time("2019-05-01"): 
            # Inspección 1
            inspeccion_1 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1' # CERRADA
            )
            item_inspeccion_1a = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_herradura_blanco,
                peso_botella = 1212
            )
            item_inspeccion_1b = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212
            )

            inspeccion_id = inspeccion_1.id 
            #print('::: ID DE LA INSPECCION :::')
            #print(inspeccion_id)

            url = reverse('inventarios:get-inspeccion', args=[inspeccion_id])
            
            res = self.client.get(url)
            json_response = json.dumps(res.data)
            #print('::: URL - DETALLE INSPECCION :::')
            #print(url)

            #print('::: RES DATA - DETALLE INSPECCION :::')
            #print(json_response)

            serializer = InspeccionDetalleSerializer(inspeccion_1)
            #print('::: DATA SERIALIZADOR - DETALLE INSPECCION :::')
            #print(serializer.data)
            self.assertEqual(res.data, serializer.data)


    #--------------------------------------------------------------------------
    def test_inspeccion_detalle_403(self):
        """
        - Test para el endpoint 'get_inspeccion'
        Testear que un usuario no puede ver el detalle de una inspección que no 
        pertenece a una de sus sucursales asignadas
        """
        # Creamos una nueva sucursal y almacen
        atomic_thai = models.Sucursal.objects.create(nombre='ATOMIC THAI', cliente=self.operadora_magno)
        barra_1_atomic = models.Almacen.objects.create(nombre='BARRA 1 ATOMIC', numero=1, sucursal=atomic_thai)

        # Creamos una Inspección para el test con fecha congelada
        with freeze_time("2019-05-01"): 
            # Inspección 1
            inspeccion_1 = models.Inspeccion.objects.create(
                almacen=barra_1_atomic,
                sucursal=atomic_thai,
                usuario_alta=self.usuario_2,
                usuario_cierre=self.usuario_2,
                estado='1' # CERRADA
            )
            item_inspeccion_1a = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_herradura_blanco,
                peso_botella = 1212
            )
            item_inspeccion_1b = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212
            )

            inspeccion_id = inspeccion_1.id 
            #print('::: ID DE LA SUCURSAL :::')
            #print(atomic_thai.id)

            #url = reverse('inventarios:get-inspeccion-detail', kwargs={'inspeccion_id': inspeccion_id})
            url = reverse('inventarios:get-inspeccion', args=[inspeccion_id])
            #url = reverse('inventarios:detalle-inspeccion', kwargs={'inspeccion_id': inspeccion_id})
            #url = reverse('inventarios:get-inspeccion-detail', kwargs={'inspeccion_id': inspeccion_id})
            res = self.client.get(url)
            #json_response = json.dumps(res.data)
            #print('::: URL - DETALLE INSPECCION :::')
            #print(url)

            #print('::: RES DATA - DETALLE INSPECCION :::')
            #print(json_response)

            #serializer = InspeccionDetalleSerializer(inspeccion_1)
            #print('::: DATA SERIALIZADOR - DETALLE INSPECCION :::')
            #print(serializer.data)
            self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


    #--------------------------------------------------------------------------
    def test_inspeccion_detalle_404(self):
        """
        - Test para el endpoint 'get_inspeccion'
        Testear cuando no existe la inspeccion solicitada
        """

        url = reverse('inventarios:get-inspeccion', args=[2])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)



    #--------------------------------------------------------------------------
    def test_queryset(self):
        """ 
        Testear querysets del endpoint 'Resumen de Inspeccion'
        """

        # Creamos una Inspección para el test con fecha congelada
        with freeze_time("2019-05-01"):
            # Creamos una botella extra de Licor 43 solo para este test
            botella_licor43_2 = models.Botella.objects.create(
                folio='Ii0000000002',
                producto=self.producto_licor43,
                url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0765216599',
                capacidad=750,
                usuario_alta=self.usuario,
                sucursal=self.magno_brasserie,
                almacen=self.barra_1,
                proveedor=self.vinos_america
            )

            inspeccion_1 = models.Inspeccion.objects.create(
                    almacen=self.barra_1,
                    sucursal=self.magno_brasserie,
                    usuario_alta=self.usuario,
                    usuario_cierre=self.usuario,
                    estado='1' # CERRADA
                )
            item_inspeccion_1a = models.ItemInspeccion.objects.create(
                    inspeccion=inspeccion_1,
                    botella=self.botella_herradura_blanco,
                    peso_botella = 1212
                )
            item_inspeccion_1a2 = models.ItemInspeccion.objects.create(
                    inspeccion=inspeccion_1,
                    botella=botella_licor43_2,
                    peso_botella=1212
            )
            item_inspeccion_1b = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212
            )
            

        # QUERYSET 1: Numero de items inspeccionados en la inspeccion
        total_items_inspeccionar = models.Inspeccion.objects.filter(fecha_alta='2019-05-01').annotate(
            num_items_inspeccionados=Count('items_inspeccionados')
        )

        #print('::: TOTAL ITEMS INSPECCIONAR :::')
        #print(total_items_inspeccionar)
        #print(total_items_inspeccionar[0].num_items_inspeccionados)

        # QUERYSET 2: Numero de botellas a inspeccionar de cada ingrediente
        queryset_2 = models.Ingrediente.objects.annotate(
            items_inspeccion=Subquery(models.ItemInspeccion.objects
                .filter(inspeccion=inspeccion_1, botella__producto__ingrediente=OuterRef('pk'))
                .values('botella__producto__ingrediente')
                .annotate(count=Count('botella__producto__ingrediente'))
                .values('count')
            )
        )
        #print('::: QUERYSET 2 :::')
        #print(queryset_2)
        #print('::: ItemsInspeccion de Licor 43 :::')
        #print(queryset_2[0].items_inspeccion)
        #print('::: ItemsInspeccion de Herradura Blanco :::')
        #print(queryset_2[1].items_inspeccion)
        #print('::: ItemsInspeccion de J. Walker Black :::')
        #print(queryset_2[2].items_inspeccion)


        # QUERYSET 2A: Cantidad de ItemsInspeccion por ingrediente NO CONTADOS
        queryset_2a = models.Ingrediente.objects.annotate(
            items_inspeccion=Subquery(models.ItemInspeccion.objects
                .filter(inspeccion=inspeccion_1, botella__producto__ingrediente=OuterRef('pk'))
                .values('botella__producto__ingrediente')
                .annotate(count=Count('botella__producto__ingrediente'))
                .values('count')
            )
        )
        #print('::: QUERYSET 2A :::')
        #print(queryset_2a)
        #print('::: ItemsInspeccion de Licor 43 :::')
        #print(queryset_2a[0].items_inspeccion)
        #print('::: ItemsInspeccion de Herradura Blanco :::')
        #print(queryset_2a[1].items_inspeccion)
        #print('::: ItemsInspeccion de J. Walker Black :::')
        #print(queryset_2a[2].items_inspeccion)


        # QUERYSET 2B: Cantidad de ItemsInspeccion por ingrediente NO CONTADOS
        #queryset_2b = models.ItemInspeccion.objects.filter(inspeccion=inspeccion_1, inspeccionado=False, botella__producto__ingrediente=self.licor_43)


        queryset_2b = models.Ingrediente.objects.annotate(
            items_inspeccion=Subquery(models.ItemInspeccion.objects
                .filter(inspeccion=inspeccion_1, botella__producto__ingrediente=OuterRef('pk'))
                .values('botella__producto__ingrediente')
                .annotate(count=Count('botella__producto__ingrediente'))
                .values('count')
            )
        )
        #print('::: QUERYSET 2B :::')
        #print(queryset_2b)
        #print(ingredientes)
        # print('::: ItemsInspeccion de Licor 43 :::')
        # print(queryset_2b[0].items_inspeccion)
        # print('::: ItemsInspeccion de Herradura Blanco :::')
        # print(queryset_2b[1].items_inspeccion)
        # print('::: ItemsInspeccion de J. Walker Black :::')
        # print(queryset_2b[2].items_inspeccion)


        # QUERYSET 3: Mismo que el 2, pero solo retorna los casos que existen
        queryset_3 = models.Ingrediente.objects.annotate(
            items_inspeccion=Exists(models.ItemInspeccion.objects
                .filter(inspeccion=inspeccion_1, botella__producto__ingrediente=OuterRef('pk'))
                .values('botella__producto__ingrediente')
                .annotate(count=Count('botella__producto__ingrediente'))
                .values('count')
            )
        ).filter(items_inspeccion=True)

        #print('::: QUERYSET 3 :::')
        #print(queryset_3)


        # QUERYSET 4: Categorías a inspeccionar
        # ItemInspeccion > Inspeccion  :::::: ItemInspeccion > Botella > Producto > Ingrediente > Categoria

        #items_inspeccionados = models.ItemInspeccion.objects.filter(inspeccion=inspeccion_1, botella__producto__ingrediente__categoria=OuterRef('pk')).values('botella__producto__ingrediente__categoria')

        queryset_4 = models.Categoria.objects.annotate(
            items_inspeccion=Subquery(models.ItemInspeccion.objects
                .filter(inspeccion=inspeccion_1, botella__producto__ingrediente__categoria=OuterRef('pk'))
                .values('botella__producto__ingrediente__categoria')
                .annotate(count=Count('botella__producto__ingrediente__categoria'))
                .values('count')
            )
        )

        #queryset_4 = models.Categoria.objects.annotate(items_inspeccion=Subquery(items_inspeccionados))


        
        #queryset_4 = models.ItemInspeccion.objects.filter(inspeccion=inspeccion_1, botella__producto__ingrediente__categoria=self.categoria_licor).values('botella__producto__ingrediente__categoria')

        #print('::: QUERYSET 4 :::')
        #print(str(queryset_4.query))
        #print(queryset_4)
        #print(queryset_4[0].items_inspeccion)


        # QUERYSET 5: Igual que 4, pero solo arroja Categorías que tienen items a inspeccionar
        queryset_5 = models.Categoria.objects.annotate(
            has_items_inspeccion=Exists(models.ItemInspeccion.objects
                .filter(inspeccion=inspeccion_1, botella__producto__ingrediente__categoria=OuterRef('pk'))
                .values('botella__producto__ingrediente__categoria')
                .annotate(count=Count('botella__producto__ingrediente__categoria'))
                .values('count')
            )
        ).filter(has_items_inspeccion=True)

        #print('::: QUERYSET 5A :::')
        #print(str(queryset_4.query))
        #print(queryset_5)
        #print(queryset_5[0].has_items_inspeccion)

        # QUERYSET 5A: Igual que el 5 pero con un annotate() extra
        queryset_5a = queryset_5.annotate(
            items_inspeccion=Subquery(models.ItemInspeccion.objects
                .filter(inspeccion=inspeccion_1, botella__producto__ingrediente__categoria=OuterRef('pk'))
                .values('botella__producto__ingrediente__categoria')
                .annotate(count=Count('botella__producto__ingrediente__categoria'))
                .values('count')
            )
        )

        #print('::: QUERYSET 5A :::')
        #print(str(queryset_4.query))
        #print(queryset_5a)
        #print(queryset_5a[0].items_inspeccion)


        # QUERYSET 6: Categorias con items a inspeccionar NO CONTADOS
        queryset_6 = models.Categoria.objects.annotate(
            has_items_inspeccion=Exists(models.ItemInspeccion.objects
                .filter(inspeccion=inspeccion_1, inspeccionado=False, botella__producto__ingrediente__categoria=OuterRef('pk'))
                .values('botella__producto__ingrediente__categoria')
                .annotate(count=Count('botella__producto__ingrediente__categoria'))
                .values('count')
            )
        ).filter(has_items_inspeccion=True)

        #print('::: QUERYSET 6 :::')
        #print(str(queryset_6.query))
        #print(queryset_6)
        

        # QUERYSET 6A: Igual que 6 pero con un annotate() extra
        queryset_6a = queryset_6.annotate(
            items_inspeccion=Subquery(models.ItemInspeccion.objects
                .filter(inspeccion=inspeccion_1, botella__producto__ingrediente__categoria=OuterRef('pk'))
                .values('botella__producto__ingrediente__categoria')
                .annotate(count=Count('botella__producto__ingrediente__categoria'))
                .values('count')
            )
        )

        #print('::: QUERYSET 6A :::')
        #print(str(queryset_6.query))
        #print(queryset_6a)
        #print(queryset_6a[0].items_inspeccion)


        # QUERYSET 7: botellas NO CONTADAS

        items = models.ItemInspeccion.objects.filter(inspeccion=inspeccion_1)
        items = items.exclude(inspeccionado=True)

        queryset_7a = models.Categoria.objects.annotate(
            has_items_inspeccion=Exists(items
                .filter(botella__producto__ingrediente__categoria=OuterRef('pk'))
                .values('botella__producto__ingrediente__categoria')
                .annotate(count=Count('botella__producto__ingrediente__categoria'))
                .values('count')
            )
        ).filter(has_items_inspeccion=True)

        queryset_7b = models.Categoria.objects.annotate(
            items_inspeccion=Subquery(items
                .filter(botella__producto__ingrediente__categoria=OuterRef('pk'))
                .values('botella__producto__ingrediente__categoria')
                .annotate(count=Count('botella__producto__ingrediente__categoria'))
                .values('count')
            )
        )

        queryset_7c = queryset_7a.annotate(
            items_inspeccion=Subquery(items
                .filter(botella__producto__ingrediente__categoria=OuterRef('pk'))
                .values('botella__producto__ingrediente__categoria')
                .annotate(count=Count('botella__producto__ingrediente__categoria'))
                .values('count')
            )
        )



        #print('::: QUERYSET 7 :::')
        #print(items)
        #print(queryset_7a)
        #print(queryset_7b)
        #print(queryset_7b[0].items_inspeccion)
        #print(queryset_7b[1].items_inspeccion)
        #print(queryset_7b[2].items_inspeccion)
        # for categoria in queryset_7b:
        #     print('::: Categoria :::')
        #     print(categoria)
        lista_categorias = [categoria for categoria in queryset_7b if categoria.items_inspeccion is not None]
        #print('::: Lista de Categorías :::')
        #print(lista_categorias)
        #print(queryset_7c)


        #----------------------------------------------------------------------------------

        # Checar QuerySet 1
        self.assertEqual(total_items_inspeccionar[0].num_items_inspeccionados, 3)

        # Checar QuerySet 2
        # Debe haber 2 botellas de Licor 43 a inspeccionar
        self.assertEqual(queryset_2[0].items_inspeccion, 2)

        # Checar QuerySet 3
        # NO hay botellas de J. Walker Black para inspeccionar
        self.assertEqual(queryset_3.count(), 2)

        # Checar QUERYSET 4
        # Debe haber 3 Categorías: Licor, Tequila y Whisky
        # La categoría Licor debe tener 2 items por inspeccionar
        self.assertEqual(queryset_4.count(), 3)
        self.assertEqual(queryset_4[0].items_inspeccion, 2)

        # Checar QUERYSET 5
        # Deber haber solo 2 categorias: Licor y Tequila
        self.assertEqual(queryset_5.count(), 2)
        

    #--------------------------------------------------------------------------
    def test_data_resumen_inspeccion(self):
        """
        Testear que se construye el JSON de la vista 'Resumen de Inspeccion'
        de forma adecuada
        """

        # Creamos una Inspección para el test con fecha congelada
        with freeze_time("2019-05-01"):
            # Creamos una botella extra de Licor 43 solo para este test
            botella_licor43_2 = models.Botella.objects.create(
                folio='Ii0000000002',
                producto=self.producto_licor43,
                url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0765216599',
                capacidad=750,
                usuario_alta=self.usuario,
                sucursal=self.magno_brasserie,
                almacen=self.barra_1,
                proveedor=self.vinos_america
            )

            inspeccion_1 = models.Inspeccion.objects.create(
                    almacen=self.barra_1,
                    sucursal=self.magno_brasserie,
                    usuario_alta=self.usuario,
                    usuario_cierre=self.usuario,
                    estado='1' # CERRADA
                )
            item_inspeccion_1a = models.ItemInspeccion.objects.create(
                    inspeccion=inspeccion_1,
                    botella=self.botella_herradura_blanco,
                    peso_botella = 1212
                )
            item_inspeccion_1a2 = models.ItemInspeccion.objects.create(
                    inspeccion=inspeccion_1,
                    botella=botella_licor43_2,
                    peso_botella=1212
            )
            item_inspeccion_1b = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212
            )

        #---------------------------------------------------------------
        # Definimos la estructura del output deseado
        #---------------------------------------------------------------

        # [
        #     {
        #         'categoria': 'LICOR',
        #         'total_botellas': 4, # QUERYSET 4
        #         'botellas': [
        #             {
        #                 'ingrediente': 'LICOR 43', # QUERYSET 1
        #                 'cantidad': 2 # QUERYSET 1
        #             },
        #             {
        #                 'ingrediente': 'CAMPARI',
        #                 'cantidad': 1 
        #             }
        #         ]
        #     },
        # ]

        #---------------------------------------------------------------
        # Definimos los querysets a utilizar
        #---------------------------------------------------------------

        # QUERYSET 1: Cantidad de items a inspeccionar por tipo de ingrediente
        queryset_1 = models.Ingrediente.objects.annotate(
            items_inspeccion=Subquery(models.ItemInspeccion.objects
                .filter(inspeccion=inspeccion_1, botella__producto__ingrediente=OuterRef('pk'))
                .values('botella__producto__ingrediente')
                .annotate(count=Count('botella__producto__ingrediente'))
                .values('count')
            )
        )

        # QUERYSET 2: Categorías que contienen items a inspeccionar
        queryset_2 = models.Categoria.objects.annotate(
            items_inspeccion=Exists(models.ItemInspeccion.objects
                .filter(inspeccion=inspeccion_1, botella__producto__ingrediente__categoria=OuterRef('pk'))
                .values('botella__producto__ingrediente__categoria')
                .annotate(count=Count('botella__producto__ingrediente__categoria'))
                .values('count')
            )
        ).filter(items_inspeccion=True)

        # QUERYSET 2A: Numero de items a inspeccionar por categoría
        queryset_2a = queryset_2.annotate(
            items_inspeccion=Subquery(models.ItemInspeccion.objects
                .filter(inspeccion=inspeccion_1, botella__producto__ingrediente__categoria=OuterRef('pk'))
                .values('botella__producto__ingrediente__categoria')
                .annotate(count=Count('botella__producto__ingrediente__categoria'))
                .values('count')
            )
        )

        #---------------------------------------------------------------
        # Construimos el JSON del response
        #---------------------------------------------------------------

        # Tomamos las categorías que contienen items a inspeccionar
        categorias = queryset_2a
        # Tomamos los ingredientes que contienen items a inspeccionar
        ingredientes = queryset_1 

        # Una lista donde guardaremos el output a renderearse por el Response
        resumen_inspeccion = []

        # Iteramos por el queryset de las categorias
        for categoria in categorias:
            # Creamos un objecto en donde guardaremos la categoría y sus items a inspeccionar
            obj = {}
            lista_ingredientes = []
            # Tomamos el nombre de la categoria
            nombre_categoria = categoria.nombre
            # Tomamos el total de items a inspeccionar de la categoria
            total_items_inspeccion = categoria.items_inspeccion
            # Guardamos las variables en un diccionario
            obj['categoria'] = nombre_categoria
            obj['total_botellas'] = total_items_inspeccion

            # Iteramos por el queryset de los ingredientes
            for ingrediente in ingredientes:
                obj_ingrediente = {}
                # Si la categoría del ingrediente es igual a la categoría del loop:
                if ingrediente.categoria.id == categoria.id:
                    # Tomamos el nombre del ingrediente y sus items inspeccion
                    nombre_ingrediente = ingrediente.nombre
                    cantidad = ingrediente.items_inspeccion
                    # Los guardamos en un diccionario
                    obj_ingrediente['ingrediente'] = nombre_ingrediente
                    obj_ingrediente['cantidad'] = cantidad
                    # Guardamos el diccionario en una lista de ingredientes
                    lista_ingredientes.append(obj_ingrediente)
            
            # Guardamos la lista de ingredientes en la categoría actual
            obj['botellas'] = lista_ingredientes
            # Guardamos el objecto en la lista del output del Response
            resumen_inspeccion.append(obj)

        #print('::: RESUMEN INSPECCION')
        #print(resumen_inspeccion)



        self.assertEqual(queryset_2.count(), 2)

    
    #--------------------------------------------------------------------------
    def test_resumen_inspeccion(self):
        """
        Testear el endpoint de Resumen de Inspeccion
        """

        # Creamos una Inspección para el test con fecha congelada
        with freeze_time("2019-05-01"):
            # Creamos una botella extra de Licor 43 solo para este test
            botella_licor43_2 = models.Botella.objects.create(
                folio='Ii0000000002',
                producto=self.producto_licor43,
                url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0765216599',
                capacidad=750,
                usuario_alta=self.usuario,
                sucursal=self.magno_brasserie,
                almacen=self.barra_1,
                proveedor=self.vinos_america
            )

            inspeccion_1 = models.Inspeccion.objects.create(
                    almacen=self.barra_1,
                    sucursal=self.magno_brasserie,
                    usuario_alta=self.usuario,
                    usuario_cierre=self.usuario,
                    estado='1' # CERRADA
                )
            item_inspeccion_1a = models.ItemInspeccion.objects.create(
                    inspeccion=inspeccion_1,
                    botella=self.botella_herradura_blanco,
                    peso_botella = 1212
                )
            item_inspeccion_1a2 = models.ItemInspeccion.objects.create(
                    inspeccion=inspeccion_1,
                    botella=botella_licor43_2,
                    peso_botella=1212
            )
            item_inspeccion_1b = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212
            )
        
        # Construimos el Response
        inspeccion_id = inspeccion_1.id
        url = reverse('inventarios:resumen-inspeccion', args=[inspeccion_id])
        response = self.client.get(url)

        #print('::: DATOS DEL RESPONSE :::')
        #print(response.data)

        # Checamos el status del response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que la categoría LICOR esté en el response
        self.assertEqual(response.data[0]['categoria'], 'LICOR')


    #-------------------------------------------------------------------
    def test_resumen_botellas_conteo(self):
        """
        Testear el endpoint que muestra el resumen de botellas contadas/no contadas
        """

        # Creamos una Inspección para el test con fecha congelada
        with freeze_time("2019-05-01"):
            # Creamos una botella extra de Licor 43 solo para este test
            botella_licor43_2 = models.Botella.objects.create(
                folio='Ii0000000002',
                producto=self.producto_licor43,
                url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0765216599',
                capacidad=750,
                usuario_alta=self.usuario,
                sucursal=self.magno_brasserie,
                almacen=self.barra_1,
                proveedor=self.vinos_america
            )

            inspeccion_1 = models.Inspeccion.objects.create(
                    almacen=self.barra_1,
                    sucursal=self.magno_brasserie,
                    usuario_alta=self.usuario,
                    usuario_cierre=self.usuario,
                    estado='1' # CERRADA
                )
            item_inspeccion_1a = models.ItemInspeccion.objects.create(
                    inspeccion=inspeccion_1,
                    botella=self.botella_herradura_blanco,
                    peso_botella = 1212
                )
            item_inspeccion_1a2 = models.ItemInspeccion.objects.create(
                    inspeccion=inspeccion_1,
                    botella=botella_licor43_2,
                    peso_botella=1212
            )
            item_inspeccion_1b = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212
            )

            # Construimos el Response
            inspeccion_id = inspeccion_1.id
            url = reverse('inventarios:resumen-botellas-conteo', args=[inspeccion_id])
            response = self.client.get(url)
            json_response = json.dumps(response.data)

            #print('::: DATOS DEL RESPONSE :::')
            #print(json_response)

            # Checamos el status del response
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Checamos el número de botellas no contadas
            self.assertEqual(response.data['botellas_no_contadas'], 3)
            # Checamos la cantidad de botellas contadas
            self.assertEqual(response.data['botellas_contadas'], 0)

    #--------------------------------------------------------------------------------------
    def test_resumen_inspeccion_no_contado(self):
        """
        Testear el endpoint de Resumen de Inspeccion (BOTELLAS NO CONTADAS)
        """

        # Creamos una Inspección para el test con fecha congelada
        with freeze_time("2019-05-01"):
            # Creamos una botella extra de Licor 43 solo para este test
            botella_licor43_2 = models.Botella.objects.create(
                folio='Ii0000000002',
                producto=self.producto_licor43,
                url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0765216599',
                capacidad=750,
                usuario_alta=self.usuario,
                sucursal=self.magno_brasserie,
                almacen=self.barra_1,
                proveedor=self.vinos_america
            )

            inspeccion_1 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1' # CERRADA
            )
            item_inspeccion_1a = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_herradura_blanco,
                peso_botella = 1212,
                inspeccionado=True
            )
            item_inspeccion_1a2 = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=botella_licor43_2,
                peso_botella=1212
            )
            item_inspeccion_1b = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212
            )
        
        # Construimos el Response
        inspeccion_id = inspeccion_1.id
        url = reverse('inventarios:resumen-inspeccion-no-contado', args=[inspeccion_id])
        response = self.client.get(url)

        #print('::: DATOS DEL RESPONSE :::')
        #print(response.data)

        # Checamos el status del response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        """
        Checamos que todas las botellas no contadas estén en el response
        - 2 botellas de Licor 43
        - 1 botella de Herradura Blanco
        """
        # Checamos que la categoría LICOR esté en el response
        self.assertEqual(response.data[0]['categoria'], 'LICOR')
        # Checamos que haya 2 botellas de Licor 43
        self.assertEqual(response.data[0]['botellas'][0]['cantidad'], 2)
        self.assertEqual(response.data[0]['botellas'][0]['ingrediente'], 'LICOR 43')
        # Checamos que haya 1 botella de Herradura Blanco
        #self.assertEqual(response.data[1]['botellas'][0]['cantidad'], 1)
        #self.assertEqual(response.data[1]['botellas'][0]['ingrediente'], 'HERRADURA BLANCO')
        # Checamos que la botella de Heradura Blanco no esté presente en el response (ya fue inspeccionada)
        self.assertEqual(len(response.data), 1)


        
    def test_resumen_inspeccion_contado(self):
        """
        Testear el endpoint de Resumen de Inspeccion (BOTELLAS CONTADAS)
        """

        # Creamos una Inspección para el test con fecha congelada
        with freeze_time("2019-05-01"):
            # Creamos una botella extra de Licor 43 solo para este test
            botella_licor43_2 = models.Botella.objects.create(
                folio='Ii0000000002',
                producto=self.producto_licor43,
                url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0765216599',
                capacidad=750,
                usuario_alta=self.usuario,
                sucursal=self.magno_brasserie,
                almacen=self.barra_1,
                proveedor=self.vinos_america
            )

            inspeccion_1 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1' # CERRADA
                )
            item_inspeccion_1a = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_herradura_blanco,
                peso_botella = 1212,
                inspeccionado=False
                )
            item_inspeccion_1a2 = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=botella_licor43_2,
                peso_botella=1212,
                inspeccionado=True
            )
            item_inspeccion_1b = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212,
                inspeccionado=True
            )
        
        # Construimos el Response
        inspeccion_id = inspeccion_1.id
        url = reverse('inventarios:resumen-inspeccion-contado', args=[inspeccion_id])
        response = self.client.get(url)

        #print('::: DATOS DEL RESPONSE :::')
        #print(response.data)

        # Checamos el status del response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        """
        Checamos que todas las botellas contadas estén en el response
        - 2 botellas de Licor 43
        - 1 botella de Herradura Blanco
        """
        # Checamos que la categoría LICOR esté en el response
        self.assertEqual(response.data[0]['categoria'], 'LICOR')
        # Checamos que haya 2 botellas de Licor 43
        self.assertEqual(response.data[0]['botellas'][0]['cantidad'], 2)
        self.assertEqual(response.data[0]['botellas'][0]['ingrediente'], 'LICOR 43')
        # Checamos que haya 1 botella de Herradura Blanco
        #self.assertEqual(response.data[1]['botellas'][0]['cantidad'], 1)
        #self.assertEqual(response.data[1]['botellas'][0]['ingrediente'], 'HERRADURA BLANCO')
        # Checamos que la botella de Heradura Blanco no esté presente en el response (no ha sido inspeccionada)
        self.assertEqual(len(response.data), 1)


    #--------------------------------------------------------------------------------
    def test_lista_botellas_no_contadas(self):
        """
        Test para el view 'lista_botellas_no_contadas'
        """

        # Creamos una Inspección para el test con fecha congelada
        with freeze_time("2019-05-01"):
            # Creamos dos botellas extras de Licor 43 solo para este test
            botella_licor43_2 = models.Botella.objects.create(
                folio='Ii0000000002',
                producto=self.producto_licor43,
                url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0765216599',
                capacidad=750,
                usuario_alta=self.usuario,
                sucursal=self.magno_brasserie,
                almacen=self.barra_1,
                proveedor=self.vinos_america
            )

            botella_licor43_3 = models.Botella.objects.create(
                folio='Ii0000000003',
                producto=self.producto_licor43,
                url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0765216599',
                capacidad=750,
                usuario_alta=self.usuario,
                sucursal=self.magno_brasserie,
                almacen=self.barra_1,
                proveedor=self.vinos_america
            )

            inspeccion_1 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1' # CERRADA
            )
            item_inspeccion_1 = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212
            )
            item_inspeccion_2 = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=botella_licor43_2,
                peso_botella=1212
            )
            item_inspeccion_3 = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=botella_licor43_3,
                peso_botella=1212,
                inspeccionado=True
            )

        

        # Tomamos los ItemsInspeccion de la base de datos y los serializamos
        items_inspeccion = models.ItemInspeccion.objects.filter(inspeccion=inspeccion_1, botella__producto__ingrediente=self.licor_43, inspeccionado=False)
        serializer = ItemInspeccionDetalleSerializer(items_inspeccion, many=True)

        #print('::: DATA SERIALIZADOR - LISTA BOTELLAS NO CONTADAS :::')
        #print(serializer.data)

        # Definimos los paramteros del request
        parametros = {
            'inspeccion_id': inspeccion_1.id,
            'ingrediente_id': self.licor_43.id
            }

        #print('::: PARAMETROS :::')
        #print(parametros)

        # Definimos el URL del endpoint
        url = reverse('inventarios:botellas-no-contadas', kwargs=parametros)
        
        # Hacemos un request al endpoint
        response = self.client.get(url)
        json_response = json.dumps(response.data)

        #print('::: RESPONSE DATA - LISTA BOTELLAS NO CONTADAS :::')
        #print(response.data)
        #print(json_response)

        # Checamos que el request sea exitoso
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que los datos del response y los datos del serializer sean iguales
        self.assertEqual(response.data, serializer.data)

    
    #--------------------------------------------------------------------------------
    def test_lista_botellas_contadas(self):
        """
        Test para el view 'lista_botellas_contadas'
        """

        # Creamos una Inspección para el test con fecha congelada
        with freeze_time("2019-05-01"):
            # Creamos dos botellas extras de Licor 43 solo para este test
            botella_licor43_2 = models.Botella.objects.create(
                folio='Ii0000000002',
                producto=self.producto_licor43,
                url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0765216599',
                capacidad=750,
                usuario_alta=self.usuario,
                sucursal=self.magno_brasserie,
                almacen=self.barra_1,
                proveedor=self.vinos_america
            )

            botella_licor43_3 = models.Botella.objects.create(
                folio='Ii0000000003',
                producto=self.producto_licor43,
                url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0765216599',
                capacidad=750,
                usuario_alta=self.usuario,
                sucursal=self.magno_brasserie,
                almacen=self.barra_1,
                proveedor=self.vinos_america
            )

            inspeccion_1 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1' # CERRADA
            )
            item_inspeccion_1 = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212,
                inspeccionado=True
            )
            item_inspeccion_2 = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=botella_licor43_2,
                peso_botella=1212,
                inspeccionado=True
            )
            item_inspeccion_3 = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=botella_licor43_3,
                peso_botella=1212,
            
            )

        # Tomamos los ItemsInspeccion de la base de datos y los serializamos
        items_inspeccion = models.ItemInspeccion.objects.filter(inspeccion=inspeccion_1, botella__producto__ingrediente=self.licor_43, inspeccionado=True)
        serializer = ItemInspeccionDetalleSerializer(items_inspeccion, many=True)

        #print('::: DATA SERIALIZADOR - LISTA BOTELLAS NO CONTADAS :::')
        #print(serializer.data)

        # Definimos los paramteros del request
        parametros = {
            'inspeccion_id': inspeccion_1.id,
            'ingrediente_id': self.licor_43.id
            }

        #print('::: PARAMETROS :::')
        #print(parametros)
        # Definimos el URL del endpoint
        url = reverse('inventarios:botellas-contadas', kwargs=parametros)
        
        # Hacemos un request al endpoint
        response = self.client.get(url)

        #print('::: RESPONSE DATA - LISTA BOTELLAS CONTADAS :::')
        #print(response.data)

        # Checamos que el request sea exitoso
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que los datos del response y los datos del serializer sean iguales
        self.assertEqual(response.data, serializer.data)


    #------------------------------------------------------------------------
    def test_inspecciones_botella(self):
        """ Test para el endpoint 'lista_inspecciones_botella' """

        # Definimos el historial de inspecciones de nuestra botella de Licor 43
        with freeze_time("2019-05-01"):
            # Inspeccion 1
            inspeccion_1 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1' # CERRADA
            )

            # ItemsInspeccion de la Inspeccion 1
            item_inspeccion_1 = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212,
                inspeccionado=True
            )

        with freeze_time("2019-05-02"):

            # Inspeccion 2
            inspeccion_2 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1' # CERRADA
            )

            # ItemsInspeccion de la Inspeccion 2
            item_inspeccion_2 = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_2,
                botella=self.botella_licor43,
                peso_botella = 1000,
                inspeccionado=True
            )

        # Tomamos nuestra botella y su historial y lo serializamos
        serializer = BotellaItemInspeccionSerializer(self.botella_licor43)
        #print('::: SERIALIZER DATA - BOTELLA ITEMS INSPECCION :::')
        #print(serializer.data)

        # Hacemos el request
        url = reverse('inventarios:get-inspecciones-botella', args=[self.botella_licor43.folio])
        response = self.client.get(url)
        json_response = json.dumps(response.data)
        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        # Checamos que el request sea exitoso
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que los datos del response y los datos del serializer sean iguales
        self.assertEqual(response.data, serializer.data)


    #-----------------------------------------------------------------------------
    def test_detalle_botella_inspeccion(self):
        """ Testear el endpoint 'detalle_botella_inspeccion' """

        # Definimos el historial de inspecciones de nuestra botella de Licor 43
        with freeze_time("2019-05-01"):
            # Inspeccion 1
            inspeccion_1 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                #estado='0' # ABIERTA
            )

            # ItemsInspeccion de la Inspeccion 1
            item_inspeccion_1 = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212,
            )

        # Tomamos el ItemInspeccion y lo serializamos
        serializer = ItemInspeccionDetalleSerializer(item_inspeccion_1)
        #print('::: SERIALIZER DATA :::')
        #print(serializer.data)

        # Hacemos el request
        parametros = {
            'inspeccion_id': inspeccion_1.id,
            'folio_id': self.botella_licor43.folio
        }
        url = reverse('inventarios:get-detalle-botella-inspeccion', kwargs=parametros)
        response = self.client.get(url)
        json_response = json.dumps(response.data)

        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        # Checamos que el request sea exitoso
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que los datos del response y los datos del serializer sean iguales
        self.assertEqual(response.data, serializer.data)

    
    #-----------------------------------------------------------------------------
    def test_detalle_botella_inspeccion_alerta(self):
        """ 
        Testear el endpoint 'detalle_botella_inspeccion' cuando la botella
        ya fue inspeccionada anteriormente 
        """

        # Definimos el historial de inspecciones de nuestra botella de Licor 43
        with freeze_time("2019-05-01"):
            # Inspeccion 1
            inspeccion_1 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                #estado='0' # ABIERTA
            )

            # ItemsInspeccion de la Inspeccion 1
            item_inspeccion_1 = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212,
                inspeccionado=True
            )

        # Tomamos el ItemInspeccion y lo serializamos
        serializer = ItemInspeccionDetalleSerializer(item_inspeccion_1)
        #print('::: SERIALIZER DATA :::')
        #print(serializer.data)

        # Hacemos el request
        parametros = {
            'inspeccion_id': inspeccion_1.id,
            'folio_id': self.botella_licor43.folio
        }
        url = reverse('inventarios:get-detalle-botella-inspeccion', kwargs=parametros)
        response = self.client.get(url)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        # Checamos que el request sea exitoso
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que los datos del response y los datos del serializer sean iguales
        self.assertEqual(response.data['mensaje'], 'Esta botella ya fue inspeccionada.')


    #-----------------------------------------------------------------------------
    def test_detalle_botella_inspeccion_error(self):
        """ 
        Testear el endpoint 'detalle_botella_inspeccion' cuando la botella
        no pertenece a la Inspeccion en curso
        """

        # Definimos el historial de inspecciones de nuestra botella de Licor 43
        with freeze_time("2019-05-01"):
            # Inspeccion 1
            inspeccion_1 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                #estado='0' # ABIERTA
            )

            # ItemsInspeccion de la Inspeccion 1
            item_inspeccion_1 = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212,
                inspeccionado=True
            )

        # Tomamos el ItemInspeccion y lo serializamos
        serializer = ItemInspeccionDetalleSerializer(item_inspeccion_1)
        #print('::: SERIALIZER DATA :::')
        #print(serializer.data)

        # Hacemos el request
        parametros = {
            'inspeccion_id': inspeccion_1.id,
            'folio_id': self.botella_herradura_blanco.folio
        }
        url = reverse('inventarios:get-detalle-botella-inspeccion', kwargs=parametros)
        response = self.client.get(url)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        # Checamos que el request sea exitoso
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que los datos del response y los datos del serializer sean iguales
        self.assertEqual(response.data['mensaje'], 'Esta botella no es parte de la inspección.')


    #-----------------------------------------------------------------------------
    def test_lista_sucursales(self):
        """ Testear que se muestra la lista de sucursales asignadas al usuario del request """

        # Creamos una nueva sucursal para el test y se la asignamos al usuario
        atomic_thai = models.Sucursal.objects.create(nombre='ATOMIC-THAI', cliente=self.operadora_magno)
        self.usuario.sucursales.add(atomic_thai)
        # Tomamos las sucursales del usuario
        sucursales_usuario = self.usuario.sucursales.all()
        # Serializamos las sucursales
        serializer = SucursalSerializer(sucursales_usuario, many=True)

        #print('::: SERIALIZER DATA :::')
        #print(serializer.data)

        # Creamos el request
        url = reverse('inventarios:get-lista-sucursales')
        response = self.client.get(url)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        # Checamos que el request sea exitoso
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que los datos del response y los datos del serializer sean iguales
        self.assertEqual(response.data, serializer.data)

    
    #-----------------------------------------------------------------------------
    def test_lista_sucursales_almacenes(self):
        """ Testear que se muestra la lista de sucursales asignadas al usuario del request """

        # Creamos una nueva sucursal para el test y se la asignamos al usuario
        atomic_thai = models.Sucursal.objects.create(nombre='ATOMIC-THAI', cliente=self.operadora_magno)
        self.usuario.sucursales.add(atomic_thai)
        # Creamos dos almacenes para la nueva sucursal
        barra_1_atomic = models.Almacen.objects.create(nombre='BARRA 1', numero=1, sucursal=atomic_thai)
        barra_2_atomic = models.Almacen.objects.create(nombre='BARRA 2', numero=2, sucursal=atomic_thai)
        # Tomamos las sucursales del usuario
        sucursales_usuario = self.usuario.sucursales.all()
        # Serializamos las sucursales
        serializer = SucursalDetalleSerializer(sucursales_usuario, many=True)

        #print('::: SERIALIZER DATA :::')
        #print(serializer.data)

        # Creamos el request
        url = reverse('inventarios:get-lista-sucursales-almacenes')
        response = self.client.get(url)
        json_response = json.dumps(response.data)

        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        # Checamos que el request sea exitoso
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checamos que los datos del response y los datos del serializer sean iguales
        self.assertEqual(response.data, serializer.data)


    #-----------------------------------------------------------------------------
    def test_update_peso_botella(self):
        """
        Test para el view 'update_peso_botella'.
        Testear que el peso de la botella y su estatus de inspección se actualizan de forma correcta 
        """

        # Definimos el historial de inspecciones de nuestra botella de Licor 43
        with freeze_time("2019-05-01"):
            # Inspeccion 1
            inspeccion_1 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                #estado='0' # ABIERTA
            )

            # ItemsInspeccion de la Inspeccion 1
            item_inspeccion_1 = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212,
                inspeccionado=False
            )
        
        # Construimos el request
        payload = {
            'item_inspeccion': item_inspeccion_1.id,
            'peso_botella': 800,
            'estado': '1',
        }
        url = reverse('inventarios:update-peso-botella')
        response = self.client.patch(url, payload)
        json_response = json.dumps(response.data)

        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        # Refrescamos nuestro ItemInspeccion y nuestra Botella
        item_inspeccion_1.refresh_from_db()
        self.botella_licor43.refresh_from_db()

        # Checamos que el nuevo peso de nuestro ItemInspeccion sea correcto
        self.assertEqual(item_inspeccion_1.peso_botella, payload['peso_botella'])
        # Checamos que el nuevo peso de la botella sea correcto
        self.assertEqual(self.botella_licor43.peso_actual, payload['peso_botella'])

    
    #-----------------------------------------------------------------------------
    def test_cerrar_inspeccion(self):
        """
        Test para el endpoint 'cerrar_inspeccion'
        Testear que a la Inspeccion se le asignan el estado CERRADA y un usuario de cierre
        """

        # Definimos nuestra Inspeccion
        with freeze_time("2019-05-01"):
            # Inspeccion 1
            inspeccion_1 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario_2,
                #usuario_cierre=self.usuario,
            )
        
        # Construimos el request
        payload = {'inspeccion': inspeccion_1.id}
        email_usuario_1 = self.usuario.email
        url = reverse('inventarios:cerrar-inspeccion')
        response = self.client.patch(url, payload)
        json_response = json.dumps(response.data)

        #print('::: RESPONSE DATA :::')
        #print(response.data)
        #print(json_response)

        # Refrescamos nuestra Inspeccion en la base de datos
        inspeccion_1.refresh_from_db()

        # Checamos que el estado y el usuario de la Inspeccion sean correctos
        self.assertEqual(inspeccion_1.estado, '1')
        self.assertEqual(inspeccion_1.usuario_cierre.email, email_usuario_1)

    
    #-----------------------------------------------------------------------------
    def test_update_estado_botella_vacia(self):
        """
        Test para el view 'update_botella_nueva_vacia'.
        Testear que el peso de la botella, su estatus de inspección y su contenido (VACIA)
        se actualizan de forma correcta 
        """

        # Definimos el historial de inspecciones de nuestra botella de Licor 43
        with freeze_time("2019-05-01"):
            # Inspeccion 1
            inspeccion_1 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                #estado='0' # ABIERTA
            )

            # ItemsInspeccion de la Inspeccion 1
            item_inspeccion_1 = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212,
                inspeccionado=False
            )
        
        # Construimos el request
        payload = {
            'item_inspeccion': item_inspeccion_1.id,
            'estado': '0',
        }
        url = reverse('inventarios:update-botella-nueva-vacia')
        response = self.client.patch(url, payload)

        #print('::: RESPONSE DATA :::')
        #print(response.data)
        json_response = json.dumps(response.data)
        #print(json_response)

        # Refrescamos nuestro ItemInspeccion y la Botella
        item_inspeccion_1.refresh_from_db()
        self.botella_licor43.refresh_from_db()
        #print('::: DATOS BOTELLA :::')
        #print(self.botella_licor43.estado)
        #print(self.botella_licor43.peso_inicial)
        #print(self.botella_licor43.fecha_baja)

        # Checamos que el nuevo estado de la botella asociada al ItemInspeccion sea correcto
        self.assertEqual(item_inspeccion_1.botella.estado, payload['estado'])
        # Checamos que el nuevo peso de la botella declarado en el ItemInspeccion  sea igual al peso del cristal, o sea, 500
        self.assertEqual(item_inspeccion_1.peso_botella, 500)
        # Checamos que el peso nuevo de la botella ('peso_actual') sea igual que el peso del cristal
        self.assertEqual(self.botella_licor43.peso_actual, 500)

    
    #-----------------------------------------------------------------------------
    def test_update_estado_botella_nueva(self):
        """
        Test para el view 'update_botella_nueva_vacia'.
        Testear que el peso de la botella, su estatus de inspección y su contenido (NUEVA)
        se actualizan de forma correcta 
        """

        # Definimos el historial de inspecciones de nuestra botella de Licor 43
        with freeze_time("2019-05-01"):
            # Inspeccion 1
            inspeccion_1 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                #estado='0' # ABIERTA
            )

            # ItemsInspeccion de la Inspeccion 1
            item_inspeccion_1 = models.ItemInspeccion.objects.create(
                inspeccion=inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212,
                inspeccionado=False
            )
        
        # Construimos el request
        payload = {
            'item_inspeccion': item_inspeccion_1.id,
            'estado': '2',
        }
        url = reverse('inventarios:update-botella-nueva-vacia')
        response = self.client.patch(url, payload)

        #print('::: RESPONSE DATA :::')
        #print(response.data)
        json_response = json.dumps(response.data)
        #print(json_response)

        # Refrescamos nuestro ItemInspeccion y la Botella
        item_inspeccion_1.refresh_from_db()
        self.botella_licor43.refresh_from_db()
        #print('::: DATOS BOTELLA :::')
        #print(self.botella_licor43.estado)
        #print(self.botella_licor43.peso_actual)

        # Checamos que el nuevo estado de la botella asociada al ItemInspeccion sea correcto
        self.assertEqual(item_inspeccion_1.botella.estado, payload['estado'])
        # Checamos que el peso botella nevo sea igual a 1288
        self.assertEqual(item_inspeccion_1.peso_botella, 1288)
        # Checamos que el peso nuevo de la botella sea igual a 1288
        self.assertEqual(self.botella_licor43.peso_actual, 1288)


    #-----------------------------------------------------------------------------
    # @patch('inventarios.scrapper.get_data_sat')
    # def test_get_marbete_sat(self, mock_scrapper):
    #     """
    #     Test para endpoint 'get_marbete_sat'
    #     Display de datos de marbete y Producto existente OK
    #     """
    #     # Creamos un Producto adicional de Licor 43 con fecha anterior para el test
    #     with freeze_time("2019-05-01"):
    #         producto_licor43_2 = models.Producto.objects.create(
    #         folio='Ii0000000002',
    #         ingrediente=self.licor_43,
    #         peso_cristal = 500,
    #         capacidad=750,
    #         )
        
    #     # Definimos el output simulado del scrapper
    #     mock_scrapper.return_value = {
    #         'folio': 'Ii0000000009',
    #         'nombre_marca': 'LICOR 43',
    #         'capacidad': 750,
    #         'tipo_producto': 'LICORES Y CREMAS',
    #     }

    #     # Tomamos el producto registrado más reciente y lo serializamos
    #     serializer = ProductoIngredienteSerializer(self.producto_licor43)
    #     json_serializer = json.dumps(serializer.data)
    #     print('::: SERIALIZER DATA - PRODUCTO INGREDIENTE :::')
    #     #print(serializer.data)
    #     print(json_serializer)

    #     # Hacemos el request
    #     #url_sat = 'http://www.sat.gob.mx'
    #     folio_sat = 'Ii0000000009'
    #     url = reverse('inventarios:get-marbete-sat', args=[folio_sat])
    #     response = self.client.get(url)
    #     json_response = json.dumps(response.data)
    #     print('::: RESPONSE DATA :::')
    #     #print(response.data)
    #     print(json_response)

    #     output_esperado = {
    #         'data_marbete': mock_scrapper.return_value,
    #         'producto': serializer.data
    #     }
    #     json_output_esperado = json.dumps(output_esperado)

    #     # Checamos que el request sea exitoso
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     # Checamos que los datos del response sean correctos
    #     self.assertEqual(response.data['data_marbete']['folio'], mock_scrapper.return_value['folio'])
    #     self.assertEqual(response.data['producto']['ingrediente']['nombre'], self.licor_43.nombre)
    #     self.assertEqual(json_output_esperado, json_response)


    #-----------------------------------------------------------------------------
    def test_crear_inspeccion_total(self):
        """ Testear que se crea una inspección TOTAL de forma exitosa """

        with freeze_time("2019-04-30"): 
            #print('::: INICIO DEL TEST :::')
            #assert datetime.datetime.now() != datetime.datetime(2019, 5, 2)
            #mock_now.return_value = yesterday
            # Creamos una inspección previa
            inspeccion_previa = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario_2,
                estado='1'
            )
        
        # Creamos un Producto y Botella nuevos para el test
        self.producto_jw_black = models.Producto.objects.create(
            folio='Ii0000000009',
            ingrediente=self.jw_black,
            peso_cristal = 490,
            capacidad=750,
        )
        self.botella_jw_black = models.Botella.objects.create(
            folio='Ii0000000009',
            producto=self.producto_jw_black,
            url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0814634647',
            capacidad=750,
            usuario_alta=self.usuario,
            sucursal=self.magno_brasserie,
            almacen=self.barra_1,
            proveedor=self.vinos_america
        )


        # print('::: TEST: DATOS INSPECCION PREVIA :::')
        # print(inspeccion_previa.estado)
        # print(inspeccion_previa.fecha_alta)
        # print(inspeccion_previa.usuario_alta)
        # print('::: TEST: REPR INSPECCION PREVIA :::')
        # print(inspeccion_previa)

        payload = {
            'almacen': self.barra_1.id,
            'sucursal': self.magno_brasserie.id,
            #'usuario_alta': self.usuario.id,
            'tipo_inspeccion': 'TOTAL',
        }

        # Hacemos un POST con los datos del payload
        url = reverse('inventarios:inspeccion-total-list')
        res = self.client.post(url, payload)
        #print('::: TEST: DATOS DEL RESPONSE :::')
        #print(res.data)

        # Tomamos la inspección creada con el POST
        inspeccion = models.Inspeccion.objects.get(id=res.data['id'])
        #print('::: TEST: INSPECCION DEL RESPONSE')
        #print(inspeccion)
        #print('::: TEST: ITEMS INSPECCIONADOS DEL RESPONSE')
        #print(inspeccion.items_inspeccionados.all())
        # Tomamos los ItemInspeccion de la inspección creada
        items_inspeccionados = inspeccion.items_inspeccionados.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(inspeccion.items_inspeccionados.count(), 3)
        # Checamos que el tipo de Inspeccion sea 'TOTAL'
        self.assertEqual(inspeccion.tipo, '1')

    #-----------------------------------------------------------------------------
    def test_crear_inspeccion_ok(self):
        """ Testear que se crea una inspección de forma exitosa """

        with freeze_time("2019-04-30"): 
            #print('::: INICIO DEL TEST :::')
            #assert datetime.datetime.now() != datetime.datetime(2019, 5, 2)
            #mock_now.return_value = yesterday
            # Creamos una inspección previa
            inspeccion_previa = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario_2,
                estado='1'
            )

        # print('::: TEST: DATOS INSPECCION PREVIA :::')
        # print(inspeccion_previa.estado)
        # print(inspeccion_previa.fecha_alta)
        # print(inspeccion_previa.usuario_alta)
        # print('::: TEST: REPR INSPECCION PREVIA :::')
        # print(inspeccion_previa)

        payload = {
            'almacen': self.barra_1.id,
            'sucursal': self.magno_brasserie.id,
            #'usuario_alta': self.usuario.id
            'tipo_inspeccion': 'DIARIA'
        }

        # Hacemos un POST con los datos del payload
        url = reverse('inventarios:inspeccion-total-list')
        #print('::: URL :::')
        #print(url)
        res = self.client.post(url, payload)
        json_response = json.dumps(res.data)
        #print('::: TEST: DATOS DEL RESPONSE :::')
        #print(res.data)
        #print(json_response)

        # Tomamos la inspección creada con el POST
        inspeccion = models.Inspeccion.objects.get(id=res.data['id'])
        #print('::: TEST: INSPECCION DEL RESPONSE')
        #print(inspeccion)
        #print('::: TEST: ITEMS INSPECCIONADOS DEL RESPONSE')
        #print(inspeccion.items_inspeccionados.all())
        # Tomamos los ItemInspeccion de la inspección creada
        #items_inspeccionados = inspeccion.items_inspeccionados.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(inspeccion.items_inspeccionados.count(), 2)


    #--------------------------------------------------------------------------
    def test_crear_inspeccion_error_fecha(self):
        """
        Testear que se produce un error cuando se intenta crear una nueva
        inspección en una fecha no válida.
        """ 
        #print('::: INICIO DEL TEST :::')
           
        # Creamos una inspección previa con fecha de hoy
        inspeccion_previa = models.Inspeccion.objects.create(
            almacen=self.barra_1,
            sucursal=self.magno_brasserie,
            usuario_alta=self.usuario,
            estado='1'
        )

        # Creamos un payload con la misma fecha que la inspección previa
        payload = {
            'almacen': self.barra_1.id,
            'sucursal': self.magno_brasserie.id,
            #'usuario_alta': self.usuario.id
            'tipo_inspeccion': 'DIARIA'
        }

        # Hacemos un POST con los datos del payload
        url = reverse('inventarios:inspeccion-total-list')
        res = self.client.post(url, payload)
        #print('::: TEST: DATOS DEL RESPONSE :::')
        #print(res.data)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    #----------------------------------------------------------------------
    def test_crear_inspeccion_error_abierta(self):
        """
        Testear que no se puede crear una inspección nueva cuando la inspección anterior
        sigue abierta
        """

        #print('::: INICIO DEL TEST :::')
        # Creamos una inspección previa con fecha congelada y estado 'ABIERTA'
        with freeze_time("2019-04-30"): 
            #print('::: INICIO DEL TEST :::')
            #assert datetime.datetime.now() != datetime.datetime(2019, 5, 2)
            #mock_now.return_value = yesterday
            # Creamos una inspección previa
            inspeccion_previa = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario_2,
                estado='0'
            )

        # Creamos un payload para crear una nueva inspección
        payload = {
            'almacen': self.barra_1.id,
            'sucursal': self.magno_brasserie.id,
            #'usuario_alta': self.usuario.id
            'tipo_inspeccion': 'DIARIA',
        }

        # Hacemos un POST request con los datos del payload
        url = reverse('inventarios:inspeccion-total-list')
        res = self.client.post(url, payload)
        #print('::: TEST: DATOS DEL RESPONSE :::')
        #print(res.data)

        # Checamos que hubo un error
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    #-------------------------------------------------------------------------
    def test_crear_inspeccion_primera_vez(self):
        """
        Testear que se crea la primera inspección ever
        (cuando no existen inspecciones previas)
        """

        #print('::: INICIO DEL TEST :::')
        # Creamos un payload para crear una nueva inspección
        payload = {
            'almacen': self.barra_1.id,
            'sucursal': self.magno_brasserie.id,
            #'usuario_alta': self.usuario.id
            'tipo_inspeccion': 'DIARIA',
        }

        # Hacemos un POST request con los datos del payload
        url = reverse('inventarios:inspeccion-total-list')
        res = self.client.post(url, payload)
        json_response = json.dumps(res.data)
        #print('::: RESPONSE DATA :::')
        #print(json_response)

        # Tomamos la inspección creada con el POST
        inspeccion = models.Inspeccion.objects.get(id=res.data['id'])
        #print('::: TEST: INSPECCION DEL RESPONSE')
        #print(inspeccion)
        #print('::: TEST: ITEMS INSPECCIONADOS DEL RESPONSE')
        #print(inspeccion.items_inspeccionados)
        # Tomamos los ItemInspeccion de la inspección creada
        #items_inspeccionados = inspeccion.items_inspeccionados.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(inspeccion.items_inspeccionados.count(), 2)




class TestInspeccionesPublicAPI(TestCase):
    """ Testear acceso sin autenticación al API """

    def setUp(self):
        self.client = APIClient()

    #--------------------------------------------------------------------------
    def test_auth_required(self):
        """ Testear que se necesita estar autenticado """
        res = self.client.get(INSPECCIONES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
            


        


        







