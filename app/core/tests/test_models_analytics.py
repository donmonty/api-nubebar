from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch

from core import models

import datetime
from django.utils.timezone import make_aware
from decimal import Decimal
import json
from freezegun import freeze_time


class ModelsAnalyticsTests(TestCase):
    """ Testear acceso autenticado al API """
    maxDiff = None

    def setUp(self):

        # API Client
        #self.client = APIClient()

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
        #self.client.force_authenticate(self.usuario)

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

        with freeze_time("2019-06-02"):
            # Manejamos el tema del naive datetime
            naive_datetime = datetime.datetime.now()
            aware_datetime = make_aware(naive_datetime)

            # Ventas
            self.venta_licor43 = models.Venta.objects.create(
                receta=self.trago_licor_43,
                sucursal=self.magno_brasserie,
                #fecha=self.ayer,
                fecha=aware_datetime,
                unidades=1,
                importe=120,
                caja=self.caja_1
            )

            self.venta_herradura_blanco = models.Venta.objects.create(
                receta=self.trago_herradura_blanco,
                sucursal=self.magno_brasserie,
                #fecha=self.ayer,
                fecha=aware_datetime,
                unidades=1,
                importe=90,
                caja=self.caja_1
            )

            self.venta_jw_black = models.Venta.objects.create(
                receta=self.trago_jw_black,
                sucursal=self.magno_brasserie,
                fecha=aware_datetime,
                unidades=12,
                importe=90,
                caja=self.caja_1
            )

            self.venta_maestro_dobel = models.Venta.objects.create(
                receta=self.trago_maestro_dobel,
                sucursal=self.magno_brasserie,
                fecha=aware_datetime,
                unidades=1,
                importe=90,
                caja=self.caja_3
            )

            # Consumos Recetas Vendidas
            self.cr_licor43 = models.ConsumoRecetaVendida.objects.create(
                ingrediente=self.licor_43,
                receta=self.trago_licor_43,
                venta=self.venta_licor43,
                #fecha=self.ayer,
                fecha=aware_datetime,
                volumen=60
            ) 

            self.cr_herradura_blanco = models.ConsumoRecetaVendida.objects.create(
                ingrediente=self.herradura_blanco,
                receta=self.trago_herradura_blanco,
                venta=self.venta_herradura_blanco,
                #fecha=self.ayer,
                fecha=aware_datetime,
                volumen=60
            )

            self.cr_jw_black = models.ConsumoRecetaVendida.objects.create(
                ingrediente=self.jw_black,
                receta=self.trago_jw_black,
                venta=self.venta_jw_black,
                fecha=aware_datetime,
                volumen=720
            )

            self.cr_maestro_dobel = models.ConsumoRecetaVendida.objects.create(
                ingrediente=self.maestro_dobel,
                receta=self.trago_maestro_dobel,
                venta=self.venta_maestro_dobel,
                fecha=aware_datetime,
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

        self.producto_jw_black = models.Producto.objects.create(
            folio='Ii0814634647',
            ingrediente=self.maestro_dobel,
            peso_cristal=500,
            capacidad=750,
        )

        self.producto_maestro_dobel = models.Producto.objects.create(
            folio='Nn1647414423',
            ingrediente=self.maestro_dobel,
            peso_cristal=500,
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
            proveedor=self.vinos_america,
            peso_cristal=500,
            peso_inicial=1212,
            peso_actual=1000,
        )

        self.botella_licor43_2 = models.Botella.objects.create(
            folio='Ii0000000002',
            producto=self.producto_licor43,
            url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0765216599',
            capacidad=750,
            usuario_alta=self.usuario,
            sucursal=self.magno_brasserie,
            almacen=self.barra_1,
            proveedor=self.vinos_america,
            peso_cristal=500,
            peso_inicial=1212,
            peso_actual=1000,
        )

        self.botella_herradura_blanco = models.Botella.objects.create(
            folio='Nn0000000001',
            producto=self.producto_herradura_blanco,
            url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Nn1727494182',
            capacidad=700,
            usuario_alta=self.usuario,
            sucursal=self.magno_brasserie,
            almacen=self.barra_1,
            proveedor=self.vinos_america,
            peso_cristal=500,
            peso_inicial=1165,
            peso_actual=1000,
        )

        self.botella_jw_black = models.Botella.objects.create(
            folio='Ii0814634647',
            producto=self.producto_jw_black,
            url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0814634647',
            capacidad=750,
            usuario_alta=self.usuario,
            sucursal=self.magno_brasserie,
            almacen=self.barra_1,
            proveedor=self.vinos_america,
            peso_cristal=500,
            peso_inicial=1212,
            peso_actual=1000,
        )

        self.botella_maestro_dobel = models.Botella.objects.create(
            folio='Nn1647414423',
            producto=self.producto_maestro_dobel,
            url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Nn1647414423',
            capacidad=750,
            usuario_alta=self.usuario,
            sucursal=self.magno_brasserie,
            almacen=self.barra_3,
            proveedor=self.vinos_america,
            peso_cristal=500,
            peso_inicial=1212,
            peso_actual=800,
        )

        # Creamos una botella de JW Black VACIA y con fecha de alta > fecha inspeccion_anterior
        with freeze_time("2019-06-02"):

            self.botella_jw_black_2 = models.Botella.objects.create(
                folio='Ii0814634648',
                producto=self.producto_jw_black,
                url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0814634648',
                capacidad=750,
                usuario_alta=self.usuario,
                sucursal=self.magno_brasserie,
                almacen=self.barra_1,
                proveedor=self.vinos_america,
                peso_cristal=500,
                peso_inicial=1212,
                peso_actual=500,
                estado='0',
            )

        # Creamos una botella de JW Black en BARRA 2 que vamos a traspasar después a BARRA 1
        with freeze_time("2019-05-01"):

            self.botella_jw_black_3 = models.Botella.objects.create(
                folio='Ii0814634649',
                producto=self.producto_jw_black,
                url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0814634649',
                capacidad=750,
                usuario_alta=self.usuario,
                sucursal=self.magno_brasserie,
                almacen=self.barra_2,
                proveedor=self.vinos_america,
                peso_cristal=500,
                peso_inicial=1212,
                peso_actual=1212,
                estado='2',
            )

        # Creamos otra botella de JW Black en BARRA 2 que vamos a traspasar después a BARRA 1
        with freeze_time("2019-05-01"):

            self.botella_jw_black_4 = models.Botella.objects.create(
                folio='Ii0814634650',
                producto=self.producto_jw_black,
                url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0814634650',
                capacidad=750,
                usuario_alta=self.usuario,
                sucursal=self.magno_brasserie,
                almacen=self.barra_2,
                proveedor=self.vinos_america,
                peso_cristal=500,
                peso_inicial=1212,
                peso_actual=1212,
                estado='2',
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
            peso_cristal=500,
            peso_inicial=1165,
            peso_actual=1000,
            estado='0',
        )

        #--------------------------------------------------------------------------

        # Creamos una Inspeccion previa para la BARRA 1
        with freeze_time("2019-06-01"):
            
            self.inspeccion_1 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1' # CERRADA
                )
            # Creamos los ItemsInspeccion para la Inspeccion previa
            self.item_inspeccion_11 = models.ItemInspeccion.objects.create(
                inspeccion=self.inspeccion_1,
                botella=self.botella_herradura_blanco,
                peso_botella = 1165
                )
            self.item_inspeccion_12 = models.ItemInspeccion.objects.create(
                inspeccion=self.inspeccion_1,
                botella=self.botella_licor43_2,
                peso_botella=1212
            )
            self.item_inspeccion_13 = models.ItemInspeccion.objects.create(
                inspeccion=self.inspeccion_1,
                botella=self.botella_licor43,
                peso_botella = 1212
            )

        # Creamos una Inspeccion posterior para la BARRA 1
        with freeze_time("2019-06-03"):
            
            self.inspeccion_2 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1' # CERRADA
                )
            # Creamos los ItemsInspeccion para la Inspeccion posterior
            self.item_inspeccion_21 = models.ItemInspeccion.objects.create(
                inspeccion=self.inspeccion_2,
                botella=self.botella_herradura_blanco,
                peso_botella = 1000
                )
            self.item_inspeccion_22 = models.ItemInspeccion.objects.create(
                inspeccion=self.inspeccion_2,
                botella=self.botella_licor43_2,
                peso_botella=1000
            )
            self.item_inspeccion_23 = models.ItemInspeccion.objects.create(
                inspeccion=self.inspeccion_2,
                botella=self.botella_licor43,
                peso_botella=1000
            )
            
            # Esta es la única inspección para la botella de JW Black
            self.item_inspeccion_24 = models.ItemInspeccion.objects.create(
                inspeccion=self.inspeccion_2,
                botella=self.botella_jw_black,
                peso_botella=1000
            )

        #------------------------------------------------------------------------

        # Creamos una Inspeccion previa para la BARRA 2
        with freeze_time("2019-05-02"):
            
            self.inspeccion_barra2_1 = models.Inspeccion.objects.create(
                almacen=self.barra_2,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1' # CERRADA
                )
            # Creamos los ItemsInspeccion para la Inspeccion previa
            self.item_inspeccion_barra2_11 = models.ItemInspeccion.objects.create(
                inspeccion=self.inspeccion_barra2_1,
                botella=self.botella_jw_black_3,
                peso_botella = 1212
                )

        # Creamos una Inspeccion posterior para la BARRA 2
        with freeze_time("2019-05-03"):
            
            self.inspeccion_barra2_2 = models.Inspeccion.objects.create(
                almacen=self.barra_2,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1' # CERRADA
                )
            # Creamos los ItemsInspeccion para la Inspeccion 
            self.item_inspeccion_barra2_21 = models.ItemInspeccion.objects.create(
                inspeccion=self.inspeccion_barra2_2,
                botella=self.botella_jw_black_3,
                peso_botella = 1000
                )

        #------------------------------------------------------------------------

        # Creamos una Inspeccion previa para la BARRA 3
        with freeze_time("2019-06-02"):
            
            self.inspeccion_barra3_1 = models.Inspeccion.objects.create(
                almacen=self.barra_3,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1' # CERRADA
            )
            # Creamos los ItemsInspeccion para la Inspeccion previa
            self.item_inspeccion_barra3_11 = models.ItemInspeccion.objects.create(
                inspeccion=self.inspeccion_barra3_1,
                botella=self.botella_maestro_dobel,
                peso_botella = 1212
            )

        # Creamos una Inspeccion posterior para la BARRA 3
        with freeze_time("2019-06-03"):
            
            self.inspeccion_barra3_2 = models.Inspeccion.objects.create(
                almacen=self.barra_3,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1' # CERRADA
            )
            # Creamos los ItemsInspeccion para la Inspeccion 
            self.item_inspeccion_barra3_21 = models.ItemInspeccion.objects.create(
                inspeccion=self.inspeccion_barra3_2,
                botella=self.botella_maestro_dobel,
                peso_botella = 800
            )


    #---------------------------------------------------------------------------------------------------------------
    #---------------------------------------------------------------------------------------------------------------
    #---------------------------------------------------------------------------------------------------------------
    #---------------------------------------------------------------------------------------------------------------

    def test_reporte_mermas(self):
        """ Testear la creacion de una instancia de ReporteMermas en la base de datos """

        with freeze_time("2019-06-03"):
            reporte_mermas = models.ReporteMermas.objects.create(
                fecha_inicial=self.inspeccion_1.fecha_alta,
                fecha_final=self.inspeccion_2.fecha_alta,
                inspeccion=self.inspeccion_2,
                almacen=self.barra_1
            )

        #print('::: STRING REPRESENTATION :::')
        #print(reporte_mermas)
        
        # Checamos los atributos del modelo creado
        self.assertEqual(reporte_mermas.fecha_inicial, self.inspeccion_1.fecha_alta)
        self.assertEqual(reporte_mermas.fecha_final, self.inspeccion_2.fecha_alta)
        self.assertEqual(reporte_mermas.inspeccion.id, self.inspeccion_2.id)
        self.assertEqual(reporte_mermas.almacen.id, self.barra_1.id)


    #---------------------------------------------------------------------------------------------------------------
    def test_merma_ingrediente_ok(self):
        """ Testear la creasion de una instancia de MermaIngrediente en la base de datos"""

        # Creamos una instancia de ReporteMermas
        with freeze_time("2019-06-03"):
            reporte_mermas = models.ReporteMermas.objects.create(
                fecha_inicial=self.inspeccion_1.fecha_alta,
                fecha_final=self.inspeccion_2.fecha_alta,
                inspeccion=self.inspeccion_2,
                almacen=self.barra_1
            )

        # Creamos una instancia de MermaIngrediente
        merma_ingrediente = models.MermaIngrediente.objects.create(
            ingrediente=self.licor_43,
            reporte=reporte_mermas,
            almacen=self.barra_1,
            fecha_inicial=self.inspeccion_1.fecha_alta,
            fecha_final=self.inspeccion_2.fecha_alta,
            consumo_ventas=Decimal(60),
            consumo_real=Decimal(90)
        )

        # print('::: STRING REPRESENTATION :::')
        # print(merma_ingrediente)

        # print('::: MERMA :::')
        # print(merma_ingrediente.merma)

        # print('::: PORCENTAJE :::')
        # print(merma_ingrediente.porcentaje)

        
        # Chcamos los atributos de la instancia de MermaIngrediente
        self.assertEqual(merma_ingrediente.ingrediente.id, self.licor_43.id)
        self.assertEqual(merma_ingrediente.reporte.id, reporte_mermas.id)
        self.assertEqual(merma_ingrediente.almacen.id, self.barra_1.id)
        self.assertEqual(merma_ingrediente.fecha_inicial, self.inspeccion_1.fecha_alta)
        self.assertEqual(merma_ingrediente.fecha_final, self.inspeccion_2.fecha_alta)
        self.assertAlmostEqual(float(merma_ingrediente.consumo_ventas), 60.00)
        self.assertAlmostEqual(float(merma_ingrediente.consumo_real), 90.00)
        self.assertAlmostEqual(float(merma_ingrediente.merma), -30.00)
        self.assertAlmostEqual(float(merma_ingrediente.porcentaje), -50.0)


    #---------------------------------------------------------------------------------------------------------------
    def test_merma_ingrediente_cventas_none(self):
        """ 
        Testear la creasion de una instancia de MermaIngrediente en la base de datos
        cuando 'consumo_ventas' == None
        """

        # Creamos una instancia de ReporteMermas
        with freeze_time("2019-06-03"):
            reporte_mermas = models.ReporteMermas.objects.create(
                fecha_inicial=self.inspeccion_1.fecha_alta,
                fecha_final=self.inspeccion_2.fecha_alta,
                inspeccion=self.inspeccion_2,
                almacen=self.barra_1
            )

        # Creamos una instancia de MermaIngrediente
        merma_ingrediente = models.MermaIngrediente.objects.create(
            ingrediente=self.licor_43,
            reporte=reporte_mermas,
            almacen=self.barra_1,
            fecha_inicial=self.inspeccion_1.fecha_alta,
            fecha_final=self.inspeccion_2.fecha_alta,
            consumo_ventas=None,
            consumo_real=Decimal(90)
        )

        # print('::: STRING REPRESENTATION :::')
        # print(merma_ingrediente)

        # print('::: MERMA :::')
        # print(merma_ingrediente.merma)

        # print('::: PORCENTAJE :::')
        # print(merma_ingrediente.porcentaje)

        # Checamos los valores de merma y porcentaje de la instancia de MermaIngrediente
        self.assertAlmostEqual(float(merma_ingrediente.merma), -90.00)
        self.assertAlmostEqual(float(merma_ingrediente.porcentaje), -100.00)


    #---------------------------------------------------------------------------------------------------------------
    def test_merma_ingrediente_creal_none(self):
        """ 
        Testear la creasion de una instancia de MermaIngrediente en la base de datos
        cuando 'consumo_real' == None
        """

        # Creamos una instancia de ReporteMermas
        with freeze_time("2019-06-03"):
            reporte_mermas = models.ReporteMermas.objects.create(
                fecha_inicial=self.inspeccion_1.fecha_alta,
                fecha_final=self.inspeccion_2.fecha_alta,
                inspeccion=self.inspeccion_2,
                almacen=self.barra_1
            )

        # Creamos una instancia de MermaIngrediente
        merma_ingrediente = models.MermaIngrediente.objects.create(
            ingrediente=self.licor_43,
            reporte=reporte_mermas,
            almacen=self.barra_1,
            fecha_inicial=self.inspeccion_1.fecha_alta,
            fecha_final=self.inspeccion_2.fecha_alta,
            consumo_ventas=60,
            consumo_real=None
        )

        # print('::: STRING REPRESENTATION :::')
        # print(merma_ingrediente)

        # print('::: MERMA :::')
        # print(merma_ingrediente.merma)

        # print('::: PORCENTAJE :::')
        # print(merma_ingrediente.porcentaje)

        # Checamos los valores de merma y porcentaje de la instancia de MermaIngrediente
        self.assertEqual(1, 1)
        self.assertAlmostEqual(float(merma_ingrediente.merma), 60.00)
        self.assertAlmostEqual(float(merma_ingrediente.porcentaje), 100.00)


    #---------------------------------------------------------------------------------------------------------------
    def test_merma_ingrediente_cventas_cero(self):
        """ 
        Testear la creasion de una instancia de MermaIngrediente en la base de datos
        cuando 'consumo_ventas' == 0
        """

        # Creamos una instancia de ReporteMermas
        with freeze_time("2019-06-03"):
            reporte_mermas = models.ReporteMermas.objects.create(
                fecha_inicial=self.inspeccion_1.fecha_alta,
                fecha_final=self.inspeccion_2.fecha_alta,
                inspeccion=self.inspeccion_2,
                almacen=self.barra_1
            )

        # Creamos una instancia de MermaIngrediente
        merma_ingrediente = models.MermaIngrediente.objects.create(
            ingrediente=self.licor_43,
            reporte=reporte_mermas,
            almacen=self.barra_1,
            fecha_inicial=self.inspeccion_1.fecha_alta,
            fecha_final=self.inspeccion_2.fecha_alta,
            consumo_ventas=0,
            consumo_real=90
        )

        # print('::: STRING REPRESENTATION :::')
        # print(merma_ingrediente)

        # print('::: MERMA :::')
        # print(merma_ingrediente.merma)

        # print('::: PORCENTAJE :::')
        # print(merma_ingrediente.porcentaje)

        # Checamos los valores de merma y porcentaje de la instancia de MermaIngrediente
        self.assertAlmostEqual(float(merma_ingrediente.merma), -90.00)
        self.assertAlmostEqual(float(merma_ingrediente.porcentaje), -100.00)


    #---------------------------------------------------------------------------------------------------------------
    def test_merma_ingrediente_todo_none(self):
        """ 
        Testear la creasion de una instancia de MermaIngrediente en la base de datos
        cuando 'consumo_ventas' y 'consumo_real' son ambos igual a None
        """

        # Creamos una instancia de ReporteMermas
        with freeze_time("2019-06-03"):
            reporte_mermas = models.ReporteMermas.objects.create(
                fecha_inicial=self.inspeccion_1.fecha_alta,
                fecha_final=self.inspeccion_2.fecha_alta,
                inspeccion=self.inspeccion_2,
                almacen=self.barra_1
            )

        # Creamos una instancia de MermaIngrediente
        merma_ingrediente = models.MermaIngrediente.objects.create(
            ingrediente=self.licor_43,
            reporte=reporte_mermas,
            almacen=self.barra_1,
            fecha_inicial=self.inspeccion_1.fecha_alta,
            fecha_final=self.inspeccion_2.fecha_alta,
            consumo_ventas=None,
            consumo_real=None
        )

        # print('::: STRING REPRESENTATION :::')
        # print(merma_ingrediente)

        # print('::: MERMA :::')
        # print(merma_ingrediente.merma)

        # print('::: PORCENTAJE :::')
        # print(merma_ingrediente.porcentaje)

        # Checamos los valores de merma y porcentaje de la instancia de MermaIngrediente
        self.assertAlmostEqual(float(merma_ingrediente.merma), 0.00)
        self.assertAlmostEqual(float(merma_ingrediente.porcentaje), 0.00)


