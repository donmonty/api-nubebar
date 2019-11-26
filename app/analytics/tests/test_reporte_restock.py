from django.test import TestCase
from django.db.models import F, Q, QuerySet, Avg, Count, Sum, Subquery, OuterRef, Exists, Func, ExpressionWrapper, DecimalField, IntegerField, Case, When
from django.contrib.auth import get_user_model
from django.urls import reverse
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIClient
from rest_framework import serializers

from core import models

import datetime
import math
#from datetime import datetime, timedelta

from django.utils.timezone import make_aware
from decimal import Decimal, ROUND_UP
import json
from freezegun import freeze_time
from analytics import reporte_restock

# from analytics.serializers import (
#     ReporteMermasDetalleSerializer,
#     MermaIngredienteReadSerializer,
#     ReporteMermasListSerializer,
# )



class AnalyticsTests(TestCase):
    """ Testear acceso autenticado al API """
    maxDiff = None

    def setUp(self):

        # API Client
        self.client = APIClient()

        #Fechas
        #self.hoy = datetime.date.today()
        #self.ayer = self.hoy - datetime.timedelta(days=1)

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
            nombre_marca='LICOR 43 750',
            ingrediente=self.licor_43,
            peso_cristal = 500,
            capacidad=750,
            precio_unitario=347.50,
        )

        self.producto_herradura_blanco = models.Producto.objects.create(
            folio='Nn0000000001',
            nombre_marca='HERRADURA BLANCO 700',
            ingrediente=self.herradura_blanco,
            peso_cristal = 500,
            capacidad=700,
            precio_unitario=296.50,
        )

        self.producto_jw_black = models.Producto.objects.create(
            folio='Ii0814634647',
            nombre_marca='JW BLACK 750',
            ingrediente=self.jw_black,
            peso_cristal=500,
            capacidad=750,
            precio_unitario=560.50,
        )

        self.producto_maestro_dobel = models.Producto.objects.create(
            folio='Nn1647414423',
            nombre_marca='MAESTRO DOBEL DIAMANTE 750',
            ingrediente=self.maestro_dobel,
            peso_cristal=500,
            capacidad=750,
            precio_unitario=450.50,
        )

        #-----------------------------------------------------------------------
        # Botellas que llegaron en el periodo de analisis y siguen ahi
        #-----------------------------------------------------------------------
        with freeze_time("2019-05-30"):

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

            #-----------------------------------------------------------------------
            # Botellas que llegaron en el periodo de analisis y se vaciaron
            #-----------------------------------------------------------------------

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
                peso_actual=500,
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

        # Creamos una botella de JW Black NUEVA y que se va a consumir y dar de baja el mismo dia
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
            peso_actual=1212,
            estado='2',
        )

        #-----------------------------------------------------------------------
        # Botellas que ya estaban antes y siguen ahí
        #-----------------------------------------------------------------------

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
                peso_actual=1212,
            )

        #-----------------------------------------------------------------------
        # Botellas que ya estaban antes y se vaciaron en el periodo
        #-----------------------------------------------------------------------

        # Creamos otra botella de JW Black en BARRA 2 que vamos a traspasar después a BARRA 1
        with freeze_time("2019-05-01"):

            self.botella_jw_black_4 = models.Botella.objects.create(
                folio='Ii0814634650',
                producto=self.producto_jw_black,
                url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0814634650',
                capacidad=750,
                usuario_alta=self.usuario,
                sucursal=self.magno_brasserie,
                almacen=self.barra_3,
                proveedor=self.vinos_america,
                peso_cristal=500,
                peso_inicial=1212,
                peso_actual=1212,
                estado='2',
            )
        #-----------------------------------------------------------------------
        # Botellas vacías que no son parte del análisis
        #-----------------------------------------------------------------------

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
                peso_actual=500,
                estado='0',
            )

        #--------------------------------------------------------------------------
        #--------------------------------------------------------------------------
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
                peso_botella=500
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
                peso_botella=500
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
                peso_botella=1212
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
                peso_botella=1212
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
                peso_botella=1212
            )

            self.item_inspeccion_barra3_22 = models.ItemInspeccion.objects.create(
                inspeccion=self.inspeccion_barra3_2,
                botella=self.botella_jw_black_4,
                peso_botella=500
                )


        """
        ----------------------------------------------------------------------------
        Ajustamos las Botellas que llegaron en el periodo de analisis y se vaciaron
        ----------------------------------------------------------------------------
        """ 
        with freeze_time("2019-06-03"):

            # Manejamos el tema del naive datetime
            naive_datetime = datetime.datetime.now()
            aware_datetime = make_aware(naive_datetime)

            # Update HERRADURA BLANCO 
            self.botella_herradura_blanco.fecha_baja = aware_datetime
            self.botella_herradura_blanco.peso_actual = 500
            self.botella_herradura_blanco.estado = '0'
            self.botella_herradura_blanco.save()
            self.botella_herradura_blanco.refresh_from_db()

            # Update JW BLACK 1
            self.botella_jw_black.fecha_baja = aware_datetime
            self.botella_jw_black.peso_actual = 500
            self.botella_jw_black.estado = '0'
            self.botella_jw_black.save()
            self.botella_jw_black.refresh_from_db()

        with freeze_time("2019-05-30"):

            # Update JW BLACK 2 (esta botella entró el 05-MAYO y salió el mismo día sin inspeccion de por medio)
            self.botella_jw_black_2.fecha_baja = aware_datetime
            self.botella_jw_black_2.peso_actual = 500
            self.botella_jw_black_2.estado = '0'
            self.botella_jw_black_2.save()
            self.botella_jw_black_2.refresh_from_db()

        """
        ----------------------------------------------------------------------------
        Ajustamos las Botellas que ya estaban antes y se vaciaron en el periodo
        ----------------------------------------------------------------------------
        """ 
        with freeze_time("2019-06-03"):

            # Manejamos el tema del naive datetime
            naive_datetime = datetime.datetime.now()
            aware_datetime = make_aware(naive_datetime)

            # Update JW BLACK 4
            self.botella_jw_black_4.fecha_baja = aware_datetime
            self.botella_jw_black_4.peso_actual = 500
            self.botella_jw_black_4.estado = '0'
            self.botella_jw_black_4.save()
            self.botella_jw_black_4.refresh_from_db()

        """
        ----------------------------------------------------------------------------
        Ajustamos las Botellas que no deben ser parte del reporte
        ----------------------------------------------------------------------------
        """ 
        with freeze_time("2019-05-02"):

            # Manejamos el tema del naive datetime
            naive_datetime = datetime.datetime.now()
            aware_datetime = make_aware(naive_datetime)

            # Update HERRADURA BLANCO 2
            self.botella_herradura_blanco_2.fecha_baja = aware_datetime
            self.botella_herradura_blanco_2.save()
            self.botella_herradura_blanco_2.refresh_from_db()

    """
    ----------------------------------------------------------------------------
    Test para probar los querysets del reporte
    ----------------------------------------------------------------------------
    """
    def test_qs(self):      

        """
        ----------------------------------------------------------------------------
        Testeamos los queries del reporte
        ----------------------------------------------------------------------------
        """ 
        with freeze_time("2019-06-06"):

            # Manejamos el tema del naive datetime
            naive_datetime = datetime.datetime.now()
            aware_datetime = make_aware(naive_datetime)

            # Definimos las fechas del reporte
            fecha_final = datetime.date.today()
            fecha_inicial = fecha_final - datetime.timedelta(days=7)

            #print('::: FECHA FINAL :::')
            #print(fecha_final)

            #print('::: FECHA INICIAL :::')
            #print(fecha_inicial)

            # Tomamos los Productos asociados a la sucursal
            botellas_sucursal = models.Botella.objects.filter(sucursal=self.magno_brasserie).values('producto').distinct()
            productos_sucursal = models.Producto.objects.filter(id__in=botellas_sucursal)

            #print('::: BOTELLAS SUCURSAL :::')
            #print(botellas_sucursal)

            #print('::: PRODUCTOS SUCURSAL :::')
            #print(productos_sucursal.values('folio', 'ingrediente__nombre'))

            # Botellas relevantes para el reporte
            botellas_periodo = models.Botella.objects.filter(

                Q(fecha_registro__lte=fecha_inicial, fecha_baja=None) |
                Q(fecha_registro__lte=fecha_inicial, fecha_baja__gte=fecha_inicial, fecha_baja__lte=fecha_final) |
                Q(fecha_registro__gte=fecha_inicial, fecha_baja__lte=fecha_final) |
                Q(fecha_registro__gte=fecha_inicial, fecha_baja=None)
            )

            #print('::: BOTELLAS PERIODO :::')
            #print(botellas_periodo.values('folio', 'producto__ingrediente__nombre'))

            # Numero de inspecciones por botella
            botellas_periodo = botellas_periodo.annotate(num_inspecciones=Count('inspecciones_botella'))
            #print('::: NUMERO DE INSPECCIONES X BOTELLA :::')
            #print(botellas_periodo.values('folio', 'producto__ingrediente__nombre', 'num_inspecciones'))

            # Subquery: Selección de 'peso_botella' de la última inspeccion
            sq_peso_ultima_inspeccion = Subquery(models.ItemInspeccion.objects
                                            .filter(botella=OuterRef('pk'))
                                            .order_by('-timestamp_inspeccion')
                                            .values('peso_botella')[:1]
            )

            sq_peso_inspeccion_inicial = Subquery(models.ItemInspeccion.objects
                                            .filter(botella=OuterRef('pk'), timestamp_inspeccion__gte=fecha_inicial, timestamp_inspeccion__lte=fecha_final)
                                            .order_by('timestamp_inspeccion')
                                            .values('peso_botella')[:1]
            )
            #----------------------------------------------------------------------

            #----------------------------------------------------------------------
            # Agregamos el 'peso_inspeccion_inicial'
            botellas_peso_inspeccion_inicial = botellas_periodo.annotate(
                peso_inspeccion_inicial=Case(
                    # CASO 1: La botella tiene más de 1 inspeccion
                    When(Q(num_inspecciones__gt=1), then=sq_peso_inspeccion_inicial),
                    # CASO 2: La botella tiene solo 1 inspeccion
                    When(Q(num_inspecciones=1), then=F('peso_inicial')),
                    # CASO 2: La botella no tiene inspecciones
                    When(Q(num_inspecciones=0), then=F('peso_inicial'))
                )
            )

            #----------------------------------------------------------------------
            # Agregamos 'dif_peso'
            botellas_dif_peso = botellas_peso_inspeccion_inicial.annotate(
                dif_peso=Case(
                    # Excluimos las botellas con 'peso_inspeccion_inicial' = None
                    # Estas son botellas que sí tuvieron consumo, pero no dentro del periodo del reporte
                    When(Q(peso_inspeccion_inicial=None), then=0),
                    # Si 'peso_inspeccion_inicial' es entero, todo OK
                    When(Q(peso_inspeccion_inicial__lte=0) | Q(peso_inspeccion_inicial__gte=0), then=F('peso_inspeccion_inicial') - F('peso_actual')),

                )
            )

            #print('::: BOTELLAS - DIF PESO :::')
            #print(botellas_dif_peso.values('folio', 'producto__ingrediente__nombre', 'peso_inspeccion_inicial', 'peso_actual', 'dif_peso'))

            #----------------------------------------------------------------------
            # Agregamos campo "densidad"
            botellas_densidad = botellas_dif_peso.annotate(
                densidad=ExpressionWrapper(
                    2 - F('producto__ingrediente__factor_peso'),
                    output_field=DecimalField()
                )
            )

            #----------------------------------------------------------------------
            # Agregamos un campo con el consumo en mililitros
            botellas_consumo = botellas_densidad.annotate(
                consumo_ml=ExpressionWrapper(
                    (F('dif_peso') * F('densidad')),
                    output_field=DecimalField()
                )
            )

            #print('::: BOTELLAS - CONSUMO ML :::')
            #print(botellas_consumo.values('folio', 'producto__ingrediente__nombre', 'dif_peso', 'consumo_ml'))

            #----------------------------------------------------------------------
            # Agregamos 'volumen_actual'
            botellas_volumen_actual = botellas_consumo.annotate(
                volumen_actual=ExpressionWrapper(
                    ((F('peso_actual') - F('peso_cristal')) * F('producto__ingrediente__factor_peso')),
                    output_field=DecimalField()
                )
            )

            #print('::: BOTELLAS - VOLUMEN ACTUAL :::')
            #print(botellas_volumen_actual.values('folio', 'producto__ingrediente__nombre', 'volumen_actual'))

            #----------------------------------------------------------------------
            # Agregamos un campo con la diferencia entre 'consumo_ml' y 'volumen_actual'
            botellas_dif_volumen = botellas_volumen_actual.annotate(
                #dif_volumen=F('volumen_actual') - F('consumo_ml')
                dif_volumen=F('consumo_ml') - F('volumen_actual')
            )

            #print('::: BOTELLAS - DIF VOLUMEN :::')
            #print(botellas_dif_volumen.values('folio', 'producto__ingrediente__nombre', 'dif_volumen'))

            # ---------------------------------------------------------------------------

            botellas_reporte = botellas_dif_volumen

            # Creamos una lista para guardar los registros por producto del reporte
            lista_registros = []

            # Creamos una variable para guardar el total de la compra sugerida
            total_acumulado = 0
            #print('TOTAL ACUMULADO INICIAL')
            #print(type(total_acumulado))

            for producto in productos_sucursal:

                # Tomamos las botellas asociadas al producto en cuestion
                botellas_producto = botellas_reporte.filter(producto=producto)

                # Sumamos el volumen actual de las botellas
                volumen_total = botellas_producto.aggregate(volumen_total=Sum('volumen_actual'))
                volumen_total = float(volumen_total['volumen_total'].quantize(Decimal('.01'), rounding=ROUND_UP))

                # Sumamos consumo de las botellas
                consumo_total = botellas_producto.aggregate(consumo_total=Sum('consumo_ml'))
                consumo_total = float(consumo_total['consumo_total'].quantize(Decimal('.01'), rounding=ROUND_UP))

                # Sumamos las diferencias
                diferencia_total = botellas_producto.aggregate(diferencia_total=Sum('dif_volumen'))
                #print('::: DIFERENCIA TOTAL :::')
                #print(diferencia_total)

                # Si la diferencia es negativa, continuamos con el siguiente producto
                # Esto significa que hay suficiente stock para satisfacer el consumo
                diferencia_total = float(diferencia_total['diferencia_total'].quantize(Decimal('.01'), rounding=ROUND_UP))

                if diferencia_total <= 0:
                #if diferencia_total >= 0:
                    continue

                # Calculamos el restock por producto
                unidades_restock = diferencia_total / producto.capacidad
                unidades_restock = math.ceil(unidades_restock)

                # Tomamos el precio unitario
                precio_unitario = float((producto.precio_unitario).quantize(Decimal('.01'), rounding=ROUND_UP))

                # Calculamos el subtotal
                subtotal = float(Decimal(unidades_restock * precio_unitario).quantize(Decimal('.01'), rounding=ROUND_UP))

                # Calculamos el IVA
                iva = subtotal * 0.16
                #print('::: IVA :::')
                #print(iva)

                # Calculamos el Total
                total = subtotal + iva
                total = float(Decimal(total).quantize(Decimal('.01'), rounding=ROUND_UP))
                #print('::: TOTAL :::')
                #print(total)
                #print(type(total))

                # Sumamos al total acumulado
                total_acumulado = total_acumulado + total
                total_acumulado = float(Decimal(total_acumulado).quantize(Decimal('.01'), rounding=ROUND_UP))

                # Construimos el registro del producto
                registro = {
                    'producto': producto.nombre_marca,
                    'stock_ml': volumen_total,
                    'demanda_ml': consumo_total,
                    'faltante': diferencia_total,
                    'compra_sugerida': unidades_restock,
                    'precio_lista': precio_unitario,
                    'subtotal': subtotal,
                    'iva': iva,
                    'total': total  
                }

                lista_registros.append(registro)

            # Tomamos la fecha para el reporte
            fecha_reporte = datetime.date.today()
            fecha_reporte = fecha_reporte.strftime("%d/%m/%Y")

            # Construimos el reporte
            reporte = {
                'status': '1',
                #'sucursal': sucursal.nombre,
                'sucursal': self.magno_brasserie.nombre,
                'fecha': fecha_reporte,
                'costo_total': total_acumulado,
                'data': lista_registros
            }

            #print('::: REPORTE :::')
            #print(reporte)

        
        self.assertEqual(1, 1)
        self.assertAlmostEqual(reporte['costo_total'], 2294.49)

        # Checamos el reporte para HERRADURA BLANCO 700
        self.assertEqual(reporte['data'][0]['producto'], self.producto_herradura_blanco.nombre_marca)
        self.assertAlmostEqual(reporte['data'][0]['stock_ml'], 0.0)
        self.assertAlmostEqual(reporte['data'][0]['demanda_ml'], 698.25)
        self.assertAlmostEqual(reporte['data'][0]['faltante'], 698.25)
        self.assertEqual(reporte['data'][0]['compra_sugerida'], 1)
        self.assertAlmostEqual(reporte['data'][0]['total'], 343.94)

        # Checamos el reporte para JW BLACK 750
        self.assertEqual(reporte['data'][1]['producto'], self.producto_jw_black.nombre_marca)
        self.assertAlmostEqual(reporte['data'][1]['stock_ml'], 676.4)
        self.assertAlmostEqual(reporte['data'][1]['demanda_ml'], 2242.8)
        self.assertAlmostEqual(reporte['data'][1]['faltante'], 1566.4)
        self.assertEqual(reporte['data'][1]['compra_sugerida'], 3)
        self.assertAlmostEqual(reporte['data'][1]['total'], 1950.54)

    
    #-----------------------------------------------------------------------------
    def test_script_reporte_ok(self):

        """
        -----------------------------------------------------------------------
        Testeamos que el script del reporte funcione OK
        -----------------------------------------------------------------------
        """

        # Ejecutamos el reporte
        with freeze_time("2019-06-06"):
            reporte = reporte_restock.calcular_restock(self.magno_brasserie.id)

        #print('::: TEST - RESTOCK :::')
        #print(reporte)
       

        self.assertEqual(reporte['status'], 'success')
        self.assertAlmostEqual(reporte['costo_total'], 2294.49)
        self.assertEqual(len(reporte['data']), 2)

        # Checamos el reporte para HERRADURA BLANCO 700
        self.assertEqual(reporte['data'][0]['producto'], self.producto_herradura_blanco.nombre_marca)
        self.assertAlmostEqual(reporte['data'][0]['stock_ml'], 0.0)
        self.assertAlmostEqual(reporte['data'][0]['demanda_ml'], 698.25)
        self.assertAlmostEqual(reporte['data'][0]['faltante'], 698.25)
        self.assertEqual(reporte['data'][0]['compra_sugerida'], 1)
        self.assertAlmostEqual(reporte['data'][0]['total'], 343.94)

        # Checamos el reporte para JW BLACK 750
        self.assertEqual(reporte['data'][1]['producto'], self.producto_jw_black.nombre_marca)
        self.assertAlmostEqual(reporte['data'][1]['stock_ml'], 676.4)
        self.assertAlmostEqual(reporte['data'][1]['demanda_ml'], 2242.8)
        self.assertAlmostEqual(reporte['data'][1]['faltante'], 1566.4)
        self.assertEqual(reporte['data'][1]['compra_sugerida'], 3)
        self.assertAlmostEqual(reporte['data'][1]['total'], 1950.54)


    #-----------------------------------------------------------------------------
    @patch('analytics.reporte_restock.calcular_restock')
    def test_reporte_ok(self, mock_reporte):

        """
        -----------------------------------------------------------------------
        Test para el endpoint 'get_reporte_restock'
        Testear que el endpoint funciona OK
        -----------------------------------------------------------------------
        """

        mock_reporte.return_value = {'status': 'success',}

        # Construimos el request
        url = reverse('analytics:get-reporte-restock', args=[self.magno_brasserie.id])
        response = self.client.get(url)
        json_response = json.dumps(response.data)

        #print('::: RESPONSE DATA :::')
        #print(response.data)

        #print('::: RESPONSE DATA - JSON :::')
        #print(json_response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


        



        



