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
import json
from freezegun import freeze_time



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

        self.producto_jw_black = models.Producto.objects.create(
            folio='Ii0814634647',
            ingrediente=self.jw_black,
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
                estado='0',
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
            estado='0',
        )

        # Creamos una Inspeccion previa
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
                peso_botella = 1212
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

        # Creamos una Inspeccion posterior
        with freeze_time("2019-06-03"):
            
            self.inspeccion_2 = models.Inspeccion.objects.create(
                almacen=self.barra_1,
                sucursal=self.magno_brasserie,
                usuario_alta=self.usuario,
                usuario_cierre=self.usuario,
                estado='1' # CERRADA
                )
            # Creamos los ItemsInspeccion para la Inspeccion previa
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
                peso_botella=800
            )


    
    #--------------------------------------------------------------
    def test_qs_botellas_multi_inspecciones(self):
        """
        Testear los querysets que calculan los consumos de botellas
        que tienen más de una inspección asociada
        """

        items_inspeccion = self.inspeccion_2.items_inspeccionados.all()
        items_inspeccion = items_inspeccion.values('botella__id')

        botellas_inspeccion = models.Botella.objects.filter(id__in=items_inspeccion)

        botellas_count_inspecciones = botellas_inspeccion.annotate(num_inspecciones=Count('inspecciones_botella'))
        botellas_multiples_inspecciones = botellas_count_inspecciones.filter(num_inspecciones__gte=2)
        num_inspecciones_botella_1 = botellas_multiples_inspecciones[0].num_inspecciones


        peso_actual_botellas_multiples_inspecciones = botellas_multiples_inspecciones.annotate(
            peso_actual=Subquery(models.ItemInspeccion.objects
                .filter(botella=OuterRef('pk'))
                .order_by('-timestamp_inspeccion')
                .values('peso_botella')[:1]
            )
        )

        peso_anterior_botellas_multiples_inspecciones = peso_actual_botellas_multiples_inspecciones.annotate(
            peso_anterior=Subquery(models.ItemInspeccion.objects
                .filter(botella=OuterRef('pk'))
                .order_by('timestamp_inspeccion')
                .values('peso_botella')[:1]
            )
        )

        dif_peso_botellas_multiples_inspecciones = peso_anterior_botellas_multiples_inspecciones.annotate(
            dif_peso=F('peso_anterior') - F('peso_actual')
        )


        # densidad_botellas_multiples_inspecciones = dif_peso_botellas_multiples_inspecciones.annotate(
        #     densidad=Case(
        #         When(Q(producto__ingrediente_factor_peso__lt=1), then=2-F('producto__ingrediente_factor_peso')),
        #         When(Q(producto__ingrediente_factor_peso__gt=1), then=2-F('producto__ingrediente_factor_peso')),
        #         output_field=DecimalField()
        #     )
        # )

        densidad_botellas_multiples_inspecciones = dif_peso_botellas_multiples_inspecciones.annotate(
            densidad=ExpressionWrapper(
                2 - F('producto__ingrediente__factor_peso'),
                output_field=DecimalField()
            )
        )

        consumo_botellas_multiples_inspecciones = densidad_botellas_multiples_inspecciones.annotate(
            consumo_ml=ExpressionWrapper(
                (F('dif_peso') * F('densidad')),
                output_field=DecimalField()
            )
        )


        print('::: ITEMS-INSPECCION  :::')
        print(items_inspeccion)

        print('::: BOTELLAS EN LA INSPECCION :::')
        print(botellas_inspeccion)

        print('::: BOTELLAS MULTIPLES INSPECCIONES :::')
        print(botellas_multiples_inspecciones)
        print(num_inspecciones_botella_1)

        print('::: PESO ACTUAL - BOTELLAS MULTIPLES INSPECCIONES :::')
        #print(peso_actual_botellas_multiples_inspecciones)
        print(peso_actual_botellas_multiples_inspecciones[0].peso_actual)

        print('::: PESO ANTERIOR - BOTELLAS MULTIPLES INSPECCIONES :::')
        #print(peso_anterior_botellas_multiples_inspecciones)
        print(peso_anterior_botellas_multiples_inspecciones[0].peso_anterior)
        print(peso_anterior_botellas_multiples_inspecciones[0].peso_actual)

        print('::: DIF PESO - BOTELLAS MULTIPLES INSPECCIONES :::')
        print(dif_peso_botellas_multiples_inspecciones[0].dif_peso)

        print('::: DENSIDAD - BOTELLAS MULTIPLES INSPECCIONES :::')
        print(densidad_botellas_multiples_inspecciones[0].densidad)

        print('::: CONSUMO ML - BOTELLAS MULTIPLES INSPECCIONES :::')
        print(consumo_botellas_multiples_inspecciones[0].consumo_ml)



        self.assertEqual(1, 1)


    #-------------------------------------------------------------------------------------
    #-------------------------------------------------------------------------------------
    def test_qs_botellas_una_inspeccion(self):
        """
        Testear los querysets que calculan los consumos de botellas que tienen
        una sola inspección asociada
        """

        # Tomamos los ItemsInspeccion de la Inspeccion actual
        items_inspeccion = self.inspeccion_2.items_inspeccionados.all()
        items_inspeccion = items_inspeccion.values('botella__id')

        # Tomamos las botellas presentes en la Inspeccion actual
        botellas_inspeccion = models.Botella.objects.filter(id__in=items_inspeccion)

        # Agregamos un campo con el número de inspecciones a todas las botellas
        botellas_count_inspecciones = botellas_inspeccion.annotate(num_inspecciones=Count('inspecciones_botella'))

        # Seleccionamos las botellas que tengan una sola inspección 
        botellas_una_inspeccion = botellas_count_inspecciones.filter(num_inspecciones=1)

        # Agregamos un campo con el peso actual de las botellas
        peso_actual_botellas_una_inspeccion = botellas_una_inspeccion.annotate(
            peso_actual=Subquery(models.ItemInspeccion.objects
                .filter(botella=OuterRef('pk'))
                .order_by('-timestamp_inspeccion')
                .values('peso_botella')[:1]
            )
        )

        # Agregamos un campo con el peso anterior de las botellas
        peso_anterior_botellas_una_inspeccion = peso_actual_botellas_una_inspeccion.annotate(
            peso_anterior=F('peso_inicial')
        )

        # Agregamos un campo con la diferencia de pesos
        dif_peso_botellas_una_inspeccion = peso_anterior_botellas_una_inspeccion.annotate(
            dif_peso=F('peso_anterior') - F('peso_actual')
        )

        # Agregamos un campo con la densidad del ingrediente
        densidad_botellas_una_inspeccion = dif_peso_botellas_una_inspeccion.annotate(
            densidad=ExpressionWrapper(
                2 - F('producto__ingrediente__factor_peso'),
                output_field=DecimalField()
            )
        )

        # Agregamos un campo con el consumo en mililitros
        consumo_botellas_una_inspeccion = densidad_botellas_una_inspeccion.annotate(
            consumo_ml=ExpressionWrapper(
                (F('dif_peso') * F('densidad')),
                output_field=DecimalField()
            )
        )


        #----------------------------------------------------------------
        print('::: NUMERO DE INSPECCIONES :::')
        print(botellas_una_inspeccion[0].num_inspecciones)
        print(botellas_una_inspeccion.values())
       
        print('::: PESO ACTUAL - BOTELLAS UNA INSPECCION :::')
        print(peso_actual_botellas_una_inspeccion[0].peso_actual)
        print(peso_actual_botellas_una_inspeccion.values())

        print('::: PESO ANTERIOR - BOTELLAS UNA INSPECCION :::')
        print(peso_anterior_botellas_una_inspeccion[0].peso_anterior)
        print(peso_anterior_botellas_una_inspeccion.values())

        print('::: DIFERENCIA PESOS - BOTELLAS UNA INSPECCION :::')
        print(dif_peso_botellas_una_inspeccion[0].dif_peso)
        print(dif_peso_botellas_una_inspeccion.values())

        print('::: DENSIDAD - BOTELLAS UNA INSPECCION :::')
        print(densidad_botellas_una_inspeccion[0].densidad)
        print(densidad_botellas_una_inspeccion.values())

        print('::: CONSUMO ML - BOTELLAS UNA INSPECCION :::')
        print(consumo_botellas_una_inspeccion[0].consumo_ml)
        print(consumo_botellas_una_inspeccion.values())


        #-----------------------------------------------------------------

        # Checamos que solo hay una botella con 1 inspección
        self.assertEqual(botellas_una_inspeccion.count(), 1)

        # Checamos que 'num_inspecciones' sea igual a 1
        self.assertEqual(botellas_una_inspeccion[0].num_inspecciones, 1)

        # Checamos el 'peso_actual'
        self.assertEqual(peso_actual_botellas_una_inspeccion[0].peso_actual, self.item_inspeccion_24.peso_botella)

        # Checamos el 'peso_anterior'
        self.assertEqual(peso_anterior_botellas_una_inspeccion[0].peso_anterior, self.botella_jw_black.peso_inicial)

        # Checamos el campo 'dif_peso'
        dif_peso_esperada = self.botella_jw_black.peso_inicial - self.item_inspeccion_24.peso_botella
        self.assertEqual(dif_peso_botellas_una_inspeccion[0].dif_peso, dif_peso_esperada)

        # Checamos el campo 'densidad'
        self.assertAlmostEqual(float(densidad_botellas_una_inspeccion[0].densidad), 1.05)

        # Checamos el campo 'consumo_ml'
        self.assertAlmostEqual(float(consumo_botellas_una_inspeccion[0].consumo_ml), dif_peso_esperada * 1.05)



    #-------------------------------------------------------------------------------------
    #-------------------------------------------------------------------------------------
    def test_qs_botellas_sin_inspecciones(self):
        """
        Testear los querysets que calculan los consumos de botellas que no tienen
        inspecciones asociadas
        """

        # :::  Tomamos las botellas con las siguientes características:
        # - Almacén actual
        # - Estado = VACÍA
        # - Fecha de alta > fecha inspección previa 
        
        botellas_vacias_sin_inspecciones = models.Botella.objects.filter(
            almacen=self.barra_1,
            estado='0',
            fecha_registro__gt=self.inspeccion_1.fecha_alta,
            fecha_registro__lt=self.inspeccion_2.fecha_alta
        )

        # Agregamos un campo con el número de inspecciones a todas las botellas
        botellas_vacias_sin_inspecciones = botellas_vacias_sin_inspecciones.annotate(num_inspecciones=Count('inspecciones_botella'))

        # Agregamos un campo con el peso actual de las botellas
        peso_actual_botellas_vacias_sin_inspecciones = botellas_vacias_sin_inspecciones.annotate(
            peso_actual=F('peso_cristal')   
        )

        # Agregamos un campo con el peso anterior de las botellas
        peso_anterior_botellas_vacias_sin_inspecciones = peso_actual_botellas_vacias_sin_inspecciones.annotate(
            peso_anterior=F('peso_inicial')
        )

        # Agregamos un campo con la diferencia de pesos
        dif_peso_botellas_vacias_sin_inspecciones = peso_anterior_botellas_vacias_sin_inspecciones.annotate(
            dif_peso=F('peso_anterior') - F('peso_actual')
        )

        # Agregamos un campo con la densidad del ingrediente
        densidad_botellas_vacias_sin_inspecciones = dif_peso_botellas_vacias_sin_inspecciones.annotate(
            densidad=ExpressionWrapper(
                2 - F('producto__ingrediente__factor_peso'),
                output_field=DecimalField()
            )
        )

        # Agregamos un campo con el consumo en mililitros
        consumo_botellas_vacias_sin_inspecciones = densidad_botellas_vacias_sin_inspecciones.annotate(
            consumo_ml=ExpressionWrapper(
                (F('dif_peso') * F('densidad')),
                output_field=DecimalField()
            )
        )


        #-----------------------------------------------------------------

        print('::: QUERYSET - BOTELLAS VACIAS SIN INSPECCIONES :::')
        print(botellas_vacias_sin_inspecciones)

        print('::: NUM INSPECCIONES - BOTELLAS VACIAS SIN INSPECCIONES :::')
        print(botellas_vacias_sin_inspecciones.values())
        print(botellas_vacias_sin_inspecciones[0].num_inspecciones)

        print('::: PESO ACTUAL - BOTELLAS VACIAS SIN INSPECCIONES :::')
        print(peso_actual_botellas_vacias_sin_inspecciones.values())
        print(peso_actual_botellas_vacias_sin_inspecciones[0].peso_actual)

        print('::: PESO ANTERIOR - BOTELLAS VACIAS SIN INSPECCIONES :::')
        print(peso_anterior_botellas_vacias_sin_inspecciones.values())
        print(peso_anterior_botellas_vacias_sin_inspecciones[0].peso_anterior)

        print('::: DIF PESOS - BOTELLAS VACIAS SIN INSPECCIONES :::')
        print(dif_peso_botellas_vacias_sin_inspecciones.values())
        print(dif_peso_botellas_vacias_sin_inspecciones[0].dif_peso)

        print(' ::: DENSIDAD - BOTELLAS VACIAS SIN INSPECCIONES :::')
        print(densidad_botellas_vacias_sin_inspecciones.values())
        print(densidad_botellas_vacias_sin_inspecciones[0].densidad)

        print('::: CONSUMO ML - BOTELLAS VACIAS SIN INSPECCIONES :::')
        print(consumo_botellas_vacias_sin_inspecciones.values())
        print(consumo_botellas_vacias_sin_inspecciones[0].consumo_ml)


        #-----------------------------------------------------------------

        # Checamos que la botella vacía esté en el queryset
        self.assertIn(self.botella_jw_black_2, botellas_vacias_sin_inspecciones)

        # Checamos que 'num_inspecciones' sea igual a 0
        self.assertEqual(botellas_vacias_sin_inspecciones[0].num_inspecciones, 0)

        # Checamos el 'peso_actual'
        self.assertEqual(peso_actual_botellas_vacias_sin_inspecciones[0].peso_actual, self.botella_jw_black_2.peso_cristal)

        # Checamos el 'peso_anterior'
        self.assertEqual(peso_anterior_botellas_vacias_sin_inspecciones[0].peso_anterior, self.botella_jw_black_2.peso_inicial)

        # Checamos 'dif_pesos'
        dif_peso_esperada = self.botella_jw_black_2.peso_inicial - self.botella_jw_black_2.peso_cristal
        self.assertEqual(dif_peso_botellas_vacias_sin_inspecciones[0].dif_peso, dif_peso_esperada)

        # Checamos 'densidad'
        self.assertAlmostEqual(float(densidad_botellas_vacias_sin_inspecciones[0].densidad), 1.05)

        # Checamos el campo 'consumo_ml'
        self.assertAlmostEqual(float(consumo_botellas_vacias_sin_inspecciones[0].consumo_ml), dif_peso_esperada * 1.05)







        




