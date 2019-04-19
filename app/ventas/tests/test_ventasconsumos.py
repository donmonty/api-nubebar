from django.test import TestCase, Client
from ventas import ventas_consumos
from core import models

import json
import os
import pandas as pd




class VentasConsumosTests(TestCase):

    maxDiff = None

    def setUp(self):

        # Cliente
        self.operadora_magno = models.Cliente.objects.create(nombre='MAGNO BRASSERIE')
        # Sucursal
        self.magno_brasserie = models.Sucursal.objects.create(nombre='MAGNO-BRASSERIE', cliente=self.operadora_magno)
        # Almacen
        self.barra_1 = models.Almacen.objects.create(nombre='BARRA 1', numero=1, sucursal=self.magno_brasserie)
        # Caja
        self.caja_1 = models.Caja.objects.create(numero=1, nombre='CAJA 1', almacen=self.barra_1)

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

    
    def test_output_ok(self):
        """ Testear que el módulo registra las ventas y consumos de forma correcta """

        # Creamos un dataset de prueba para el test
        payload = {
            'sucursal_id': [self.magno_brasserie.id, self.magno_brasserie.id, self.magno_brasserie.id, self.magno_brasserie.id],
            'caja_id': [self.caja_1.id, self.caja_1.id, self.caja_1.id, self.caja_1.id],
            'codigo_pos': ['00050', '00126', '00167', '00081', ],
            'nombre': ['CARAJILLO', 'CT HERRADURA BLANCO', 'CW JOHNNIE WALKER ETIQUETA NEGR A', 'LICOR 43'],
            'unidades': [3, 1, 2, 1],
            'importe': [285, 112, 340, 170]
        }

        df_test = pd.DataFrame(payload)


        # output_esperado = {

        #     "ventas_consumos": [
        #         {
        #             "venta": "RECETA: CARAJILLO - SUCURSAL: MAGNO-BRASSERIE - FECHA: 2019-04-13 - UNIDADES: 3 - IMPORTE: 285 - CAJA: CAJA: 1 - BARRA: BARRA 1",
        #             "consumos": [
        #                 "INGREDIENTE: LICOR 43 - RECETA: CARAJILLO - VENTA: RECETA: CARAJILLO - SUCURSAL: MAGNO-BRASSERIE - FECHA: 2019-04-13 - UNIDADES: 3 - IMPORTE: 285 - CAJA: CAJA: 1 - BARRA: BARRA 1 - FECHA: 2019-04-13 - VOLUMEN 135"
        #             ]
        #         },
        #         {
        #             "venta": "RECETA: HERRADURA BLANCO DERECHO - SUCURSAL: MAGNO-BRASSERIE - FECHA: 2019-04-13 - UNIDADES: 1 - IMPORTE: 112 - CAJA: CAJA: 1 - BARRA: BARRA 1",
        #             "consumos": [
        #                 "INGREDIENTE: HERRADURA BLANCO - RECETA: HERRADURA BLANCO DERECHO - VENTA: RECETA: HERRADURA BLANCO DERECHO - SUCURSAL: MAGNO-BRASSERIE - FECHA: 2019-04-13 - UNIDADES: 1 - IMPORTE: 112 - CAJA: CAJA: 1 - BARRA: BARRA 1 - FECHA: 2019-04-13 - VOLUMEN 60"
        #             ]
        #         },
        #         {
        #             "venta": "RECETA: JW BLACK DERECHO - SUCURSAL: MAGNO-BRASSERIE - FECHA: 2019-04-13 - UNIDADES: 2 - IMPORTE: 340 - CAJA: CAJA: 1 - BARRA: BARRA 1",
        #             "consumos": [
        #                 "INGREDIENTE: JOHNNIE WALKER BLACK - RECETA: JW BLACK DERECHO - VENTA: RECETA: JW BLACK DERECHO - SUCURSAL: MAGNO-BRASSERIE - FECHA: 2019-04-13 - UNIDADES: 2 - IMPORTE: 340 - CAJA: CAJA: 1 - BARRA: BARRA 1 - FECHA: 2019-04-13 - VOLUMEN 120"
        #             ]
        #         },
        #         {
        #             "venta": "RECETA: LICOR 43 DERECHO - SUCURSAL: MAGNO-BRASSERIE - FECHA: 2019-04-13 - UNIDADES: 1 - IMPORTE: 170 - CAJA: CAJA: 1 - BARRA: BARRA 1",
        #             "consumos": [
        #                 "INGREDIENTE: LICOR 43 - RECETA: LICOR 43 DERECHO - VENTA: RECETA: LICOR 43 DERECHO - SUCURSAL: MAGNO-BRASSERIE - FECHA: 2019-04-13 - UNIDADES: 1 - IMPORTE: 170 - CAJA: CAJA: 1 - BARRA: BARRA 1 - FECHA: 2019-04-13 - VOLUMEN 60"
        #             ]
        #         }
        #     ],
        #     "productos_no_registrados": []
        # }

        # Ejecutamos el módulo 'ventas_consumos' con el dataframe de prueba y guardamos el resultado
        resultado = ventas_consumos.registrar(df_test, self.magno_brasserie)
        #print(resultado)
        
        # Convertimos el resultado del módulo en un JSON
        #json_resultado = json.dumps(resultado)
        #print(json_resultado)

        # Convertimos el output esperado en un JSON
        #json_output_esperado = json.dumps(output_esperado)

        # Tomamos las ventas registradas por el móculo
        ventas_registradas = models.Venta.objects.all()
        #print(ventas_registradas)

        # Tomamos los consumos registrados por el módulo
        consumos_registrados = models.ConsumoRecetaVendida.objects.all()
        #print(consumos_registrados)

        # Cotejamos que el módulo registró las 4 ventas esperadas
        self.assertEqual(ventas_registradas.count(), 4)

        # Cotejamos que el módulo registró los 4 consumos esperados
        self.assertEqual(consumos_registrados.count(), 4)
        
        # Cotejamos que el JSON retornado por el módulo sea igual al JSON esperado
        #self.assertEqual(json_resultado, json_output_esperado)


    def test_producto_sin_registro(self):
        """ Testear que se los productos sin registro se manejan de forma adecuada """

        # Creamos un dataset de prueba para el test
        payload = {
            'sucursal_id': [self.magno_brasserie.id, self.magno_brasserie.id],
            'caja_id': [self.caja_1.id, self.caja_1.id],
            'codigo_pos': ['00050', '00457'],
            'nombre': ['CARAJILLO', 'APEROL SPRITZ'],
            'unidades': [3, 1],
            'importe': [285, 125]
        }

        df_test = pd.DataFrame(payload)

        # Ejecutamos el módulo 'ventas_consumos' con el dataframe de prueba y guardamos el resultado
        resultado = ventas_consumos.registrar(df_test, self.magno_brasserie)

        # Tomamos las ventas registradas por el módulo
        ventas_registradas = models.Venta.objects.all()

        # Cotejamos que el módulo registró 1 sola venta
        self.assertEqual(ventas_registradas.count(), 1)

        # Cotejamos que el resultado del módulo contiene 1 producto sin registro
        productos_sin_registro = len(resultado['productos_no_registrados'])
        #print(productos_sin_registro)
        self.assertEqual(productos_sin_registro, 1)






