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
from decimal import Decimal
import json
from freezegun import freeze_time
from analytics import reporte_mermas



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
    #----------------------------------------------------------------------------------
    def test_qs_macro(self):
        """
        Testear el queryset maestro del reporte
        """

        # Actalizamos los datos de la botella JW Black 3 y JW Black 4 para simular su traspaso a la BARRA 1
        # Asignamos (fecha de baja > fecha inspeccion anterior) AND (fecha de baja < fecha inspeccion actual)
        with freeze_time("2019-06-02"):

            # Manejamos el tema del naive datetime
            naive_datetime = datetime.datetime.now()
            aware_datetime = make_aware(naive_datetime)

            #------ AJUSTES PARA BOTELLA JW BLACK 3---------------------

            # Asignamos la fecha de baja
            self.botella_jw_black_3.fecha_baja = aware_datetime
            # Asignamos un nuevo peso a la botella 
            self.botella_jw_black_3.peso_actual = 500
            # Cambiamos el estado a VACIA
            self.botella_jw_black_3.estado = '0'
            # Actualizamos el almacen
            self.botella_jw_black_3.almacen = self.barra_1
            # Guardamos los cambios
            self.botella_jw_black_3.save()
            self.botella_jw_black_3.refresh_from_db()

            #------ AJUSTES PARA BOTELLA JW BLACK 4---------------------

            # Asignamos la fecha de baja
            self.botella_jw_black_4.fecha_baja = aware_datetime
            # Asignamos un nuevo peso a la botella 
            self.botella_jw_black_4.peso_actual = 500
            # Cambiamos el estado a VACIA
            self.botella_jw_black_4.estado = '0'
            # Actualizamos el almacen
            self.botella_jw_black_4.almacen = self.barra_1
            # Guardamos los cambios
            self.botella_jw_black_4.save()
            self.botella_jw_black_4.refresh_from_db()

        # Tomamos el almacen
        almacen = self.inspeccion_2.almacen

        # Definimos la fecha_inicial y fecha_final
        fecha_inicial = self.inspeccion_1.timestamp_alta
        fecha_final = self.inspeccion_2.timestamp_alta

        # Tomamos los ItemsInspeccion de la Inspeccion actual
        items_inspeccion = self.inspeccion_2.items_inspeccionados.all()
        
        # Excluimos las Botellas cuyo ItemInspecion.peso_botella = 'None'
        items_inspeccion_peso_none = items_inspeccion.filter(peso_botella=None)
        items_inspeccion.exclude(peso_botella=None)

        # Generamos un Queryset con los 'botella__id'
        items_inspeccion = items_inspeccion.values('botella__id')

        # Seleccionamos todas las botellas del almacén
        botellas = models.Botella.objects.filter(almacen=almacen)


        """
        -------------------------------------------------------------------------
        Snippets útiles

        -------------------------------------------------------------------------
        """
        # Subquery: Selección de 'peso_botella' de la penúltima inspeccion
        sq_peso_penultima_inspeccion = Subquery(models.ItemInspeccion.objects
                                            .filter(botella=OuterRef('pk'))
                                            .order_by('-timestamp_inspeccion')
                                            .values('peso_botella')[1:2]
                                        )

        sq_peso_ultima_inspeccion = Subquery(models.ItemInspeccion.objects
                                        .filter(botella=OuterRef('pk'))
                                        .order_by('-timestamp_inspeccion')
                                        .values('peso_botella')[:1]
                                    )
        
        # Lista de ingredientes presentes en la Inspeccion
        items_inspeccion_2 = self.inspeccion_2.items_inspeccionados.all()
        items_inspeccion_2 = items_inspeccion_2.values('botella__producto__ingrediente__id')
        ingredientes_inspeccion = models.Ingrediente.objects.filter(id__in=items_inspeccion_2)


        #----------------------------------------------------------------------------------
        #----------------------------------------------------------------------------------

        # Seleccionamos todas las botellas cuyo ingrediente sea parte de los ingredientes a inspeccionar
        botellas = botellas.filter(producto__ingrediente__in=ingredientes_inspeccion)

        # Agregamos 'num_inspecciones'
        botellas_num_inspecciones = botellas.annotate(num_inspecciones=Count('inspecciones_botella'))

        #print('::: BOTELLAS CON INGREDIENTES A INSPECCIONAR :::')
        #print(botellas_num_inspecciones.values())

        #----------------------------------------------------------------------
        # Agregamos 'peso_anterior'
        botellas_peso_anterior = botellas_num_inspecciones.annotate(
            peso_anterior=Case(
                # Botellas presentas en la la inspección y con múltiples inspecciones
                When(Q(id__in=items_inspeccion) & Q(num_inspecciones__gt=1), then=sq_peso_penultima_inspeccion),
                # Botellas presentes en la Inspección con 1 inspección
                When(Q(id__in=items_inspeccion) & Q(num_inspecciones=1), then=F('peso_inicial')),
                # Botellas VACIAS pero cuyo ingrediente es parte de los ingredientes a inspeccionar
                # y que se ingresaron y consumieron entre la inspección previa y la actual
                When(Q(estado='0') & Q(fecha_registro__gte=fecha_inicial, fecha_registro__lte=fecha_final), then=F('peso_inicial')),
                # Botellas VACIAS cuyo ingrediente es parte de los ingredientes a inspeccionar,
                # que se consumieron entre ambas inspecciones, pero que ya estaban registradas desde antes y tienen minimo 1 inspeccion
                When(Q(estado='0') & Q(fecha_baja__gte=fecha_inicial, fecha_baja__lte=fecha_final, fecha_registro__lte=fecha_inicial) & Q(num_inspecciones__gt=0), then=sq_peso_ultima_inspeccion),
                # Botellas VACIAS cuyo ingrediente es parte de los ingredientes a inspeccionar,
                # que se consumieron entre ambas inspecciones, pero que ya estaban registradas desde antes y tienen cero inspecciones
                When(Q(estado='0') & Q(fecha_baja__gte=fecha_inicial, fecha_baja__lte=fecha_final, fecha_registro__lte=fecha_inicial) & Q(num_inspecciones=0), then=F('peso_inicial'))
            )
        )

        #print('::: BOTELLAS - PESO ANTERIOR :::')
        #print(botellas_peso_anterior.values())

        #----------------------------------------------------------------------
        # Seleccionamos unicamente las botellas cuyo 'peso_anterior' no sea None
        # O lo que es lo mismo, excluimos del queryset todas aquellas botellas cuyo 'peso_anterior' sea None
        botellas_peso_anterior_ok = botellas_peso_anterior.exclude(peso_anterior=None)

        #print('::: PESO ANTERIOR OK :::')
        #print(botellas_peso_anterior_ok.values('folio', 'ingrediente', 'num_inspecciones', 'peso_inicial', 'peso_actual', 'peso_anterior'))


        #----------------------------------------------------------------------
        # Agregamos un campo 'dif_peso'
        dif_peso_botellas = botellas_peso_anterior_ok.annotate(
            dif_peso=F('peso_anterior') - F('peso_actual')
        )

        #print('::: DIF PESO :::')
        #print(dif_peso_botellas.values('folio', 'ingrediente', 'num_inspecciones', 'peso_inicial', 'peso_anterior', 'peso_actual', 'dif_peso'))

        #----------------------------------------------------------------------
        #Agregamos campo "densidad"
        densidad_botellas = dif_peso_botellas.annotate(
            densidad=ExpressionWrapper(
                2 - F('producto__ingrediente__factor_peso'),
                output_field=DecimalField()
            )
        )

        #print('::: DENSIDAD :::')
        #print(densidad_botellas.values('folio', 'ingrediente', 'num_inspecciones', 'peso_inicial', 'peso_anterior', 'peso_actual', 'dif_peso', 'densidad'))

        #----------------------------------------------------------------------
        # Agregamos un campo con el consumo en mililitros
        consumo_botellas = densidad_botellas.annotate(
            consumo_ml=ExpressionWrapper(
                (F('dif_peso') * F('densidad')),
                output_field=DecimalField()
            )
        )

        #consumo_real_ingredientes = densidad_botellas.annotate(consumo_ml=ExpressionWrapper(F('dif_peso') * F('densidad'), output_field=DecimalField())).annotate(_suma_consumos=Sum('consumo_ml')).values('ingrediente', '_suma_consumos').annotate(suma_consumos=F('_suma_consumos')).values('ingrediente', 'suma_consumos').order_by('ingrediente')

        #print('::: CONSUMO :::')
        #print(consumo_botellas.values('folio', 'ingrediente', 'num_inspecciones', 'peso_inicial', 'peso_anterior', 'peso_actual', 'dif_peso', 'densidad', 'consumo_ml'))

        """
        -----------------------------------------------------------------
        Calculamos el CONSUMO DE VENTAS y CONSUMO REAL por ingrediente
        -----------------------------------------------------------------
        """
        consumos = []
        for ingrediente in ingredientes_inspeccion:
            # Sumamos el consumo real por ingrediente
            botellas_ingrediente = consumo_botellas.filter(producto__ingrediente__id=ingrediente.id)
            consumo_real = botellas_ingrediente.aggregate(consumo_real=Sum('consumo_ml'))

            # Sumamos el consumo de ventas por ingrediente
            consumos_recetas = models.ConsumoRecetaVendida.objects.filter(
                ingrediente=ingrediente,
                fecha__gte=self.inspeccion_1.fecha_alta,
                fecha__lt=self.inspeccion_2.fecha_alta,
                venta__caja__almacen=self.barra_1
            )
            consumo_ventas = consumos_recetas.aggregate(consumo_ventas=Sum('volumen'))

            # Consolidamos los ingredientes, su consumo de ventas y consumo real en una lista
            ingrediente_consumo = (ingrediente, consumo_ventas, consumo_real)
            consumos.append(ingrediente_consumo)


        print('::: CONSUMO INGREDIENTES :::')
        print(consumos)


        # Checamos el consumo de ventas y consumo real de LICOR 43
        self.assertEqual(self.cr_licor43.volumen, consumos[0][1]['consumo_ventas'])   
        self.assertAlmostEqual(float(consumos[0][2]['consumo_real']), 402.80)

        # Checamos el consumo de ventas y consumo real de HERRADURA BLANCO
        self.assertEqual(self.cr_herradura_blanco.volumen, consumos[1][1]['consumo_ventas'])   
        self.assertAlmostEqual(float(consumos[1][2]['consumo_real']), 173.25)

        # Checamos el consumo de ventas y consumo real de JW BLACK
        self.assertEqual(self.cr_jw_black.volumen, consumos[2][1]['consumo_ventas'])   
        self.assertAlmostEqual(float(consumos[2][2]['consumo_real']), 2242.80)


    #----------------------------------------------------------------------
    #----------------------------------------------------------------------
    def test_reporte_ok(self):
        """
        Testear que el reporte de mermas funciona OK
        """

        # Actalizamos los datos de la botella JW Black 3 y JW Black 4 para simular su traspaso a la BARRA 1
        # Asignamos (fecha de baja > fecha inspeccion anterior) AND (fecha de baja < fecha inspeccion actual)
        with freeze_time("2019-06-02"):

            # Manejamos el tema del naive datetime
            naive_datetime = datetime.datetime.now()
            aware_datetime = make_aware(naive_datetime)

            #------ AJUSTES PARA BOTELLA JW BLACK 3---------------------

            # Asignamos la fecha de baja
            self.botella_jw_black_3.fecha_baja = aware_datetime
            # Asignamos un nuevo peso a la botella 
            self.botella_jw_black_3.peso_actual = 500
            # Cambiamos el estado a VACIA
            self.botella_jw_black_3.estado = '0'
            # Actualizamos el almacen
            self.botella_jw_black_3.almacen = self.barra_1
            # Guardamos los cambios
            self.botella_jw_black_3.save()
            self.botella_jw_black_3.refresh_from_db()

            #------ AJUSTES PARA BOTELLA JW BLACK 3---------------------

            # Asignamos la fecha de baja
            self.botella_jw_black_4.fecha_baja = aware_datetime
            # Asignamos un nuevo peso a la botella 
            self.botella_jw_black_4.peso_actual = 500
            # Cambiamos el estado a VACIA
            self.botella_jw_black_4.estado = '0'
            # Actualizamos el almacen
            self.botella_jw_black_4.almacen = self.barra_1
            # Guardamos los cambios
            self.botella_jw_black_4.save()
            self.botella_jw_black_4.refresh_from_db() 

            # print('::: ALMACEN BOTELLA TRASPASADA  :::')
            # print(self.botella_jw_black_3.almacen.nombre)
            # print(self.botella_jw_black_4.almacen.nombre)

            # print('::: PESO ACTUAL BOTELLA TRASPASADA :::')
            # print(self.botella_jw_black_3.peso_actual)
            # print(self.botella_jw_black_4.peso_actual)

            # print('::: FECHA BAJA BOTELLA TRASPASADA :::')
            # print(self.botella_jw_black_3.fecha_baja)
            # print(self.botella_jw_black_4.fecha_baja)

            # print('::: FECHA BAJA BOTELLA TRASPASADA :::')
            # print(self.botella_jw_black_3.fecha_baja)
            # print(self.botella_jw_black_4.fecha_baja)

            # print('::: ESTADO BOTELLA TRASPASADA :::')
            # print(self.botella_jw_black_3.estado)
            # print(self.botella_jw_black_4.estado)

        # Ejecutamos el Reporte de Mermas
        consumos = reporte_mermas.calcular_consumos(self.inspeccion_2,  self.inspeccion_1.timestamp_alta, self.inspeccion_2.timestamp_alta)

        # print('::: TEST - DATA CONSUMOS :::')
        # print(consumos)

        # print('::: TIMESTAMP ALTA - INSPECCION 1 :::')
        # print(self.inspeccion_1.timestamp_alta)

        # print('::: FECHA ALTA - INSPECCION 1 :::')
        # print(self.inspeccion_1.fecha_alta)

        # print('::: TIMESTAMP ALTA - INSPECCION 2 :::')
        # print(self.inspeccion_2.timestamp_alta)

        # print('::: FECHA ALTA - INSPECCION 2 :::')
        # print(self.inspeccion_2.fecha_alta)

        # print('::: CR LICOR 43 - FECHA :::')
        # print(self.cr_licor43.fecha)

        # consumos_licor_43 = models.ConsumoRecetaVendida.objects.filter(
        #     ingrediente=self.licor_43,
        #     fecha__gte=self.inspeccion_1.timestamp_alta,
        #     fecha__lte=self.inspeccion_2.timestamp_alta,
        #     venta__caja__almacen=self.barra_1
        # )

        # print('::: CONSUMOS LICOR 43 :::')
        # print(consumos_licor_43.values())

        # Checamos el consumo de ventas y consumo real de LICOR 43
        self.assertEqual(self.cr_licor43.volumen, consumos[0][1]['consumo_ventas'])   
        self.assertAlmostEqual(float(consumos[0][2]['consumo_real']), 402.80)

        # Checamos el consumo de ventas y consumo real de HERRADURA BLANCO
        self.assertEqual(self.cr_herradura_blanco.volumen, consumos[1][1]['consumo_ventas'])   
        self.assertAlmostEqual(float(consumos[1][2]['consumo_real']), 173.25)

        # Checamos el consumo de ventas y consumo real de JW BLACK
        self.assertEqual(self.cr_jw_black.volumen, consumos[2][1]['consumo_ventas'])   
        self.assertAlmostEqual(float(consumos[2][2]['consumo_real']), 2242.80)


    #----------------------------------------------------------------------
    #----------------------------------------------------------------------
    def test_reporte_barra3_ok(self):
        """
        ----------------------------------------------------------------------
        Testear que el reporte de mermas para la Barra 3 funciona OK

        - Las inspecciones de la Barra 3 fueron hechas en dias consecutivos

        ----------------------------------------------------------------------
        """

        # Ejecutamos el Reporte de Mermas
        consumos = reporte_mermas.calcular_consumos(self.inspeccion_barra3_2,  self.inspeccion_barra3_1.timestamp_alta, self.inspeccion_barra3_2.timestamp_alta)

        #print('::: CONSUMO INGREDIENTES BARRA 3 :::')
        #print(consumos)
        
        # Checamos el consumo de ventas y consumo real de MAESTRO DOBEL
        self.assertEqual(self.cr_maestro_dobel.volumen, consumos[0][1]['consumo_ventas'])   
        self.assertAlmostEqual(float(consumos[0][2]['consumo_real']), 432.60)
