




def setUp(self):

        # Cliente
        operadora_magno = models.Cliente.objects.create(nombre='MAGNO BRASSERIE')

        # Sucursal
        magno_brasserie = models.Sucursal.objects.create(nombre='MAGNO-BRASSERIE', cliente=operadora_magno)

        # Almacen
        barra_1 = models.Almacen.objects.create(nombre='BARRA 1', numero=1, sucursal=magno_brasserie)

        # Caja
        caja_1 = models.Caja.objects.create(numero=1, nombre='CAJA 1', almacen=barra_1)

        # Categorías
        categoria_licor = models.Categoria.objects.create(nombre='LICOR')
        categoria_tequila = models.Categoria.objects.create(nombre='TEQUILA')
        categoria_whisky = models.Categoria.objects.create(nombre='WHISKY')

        # Ingredientes
        licor_43 = models.Ingrediente.objects.create(
            codigo='LICO001',
            nombre='LICOR 43',
            categoria=categoria_licor,
            factor_peso=1.05
        )
        herradura_blanco = models.Ingrediente.objects.create(
            codigo='TEQU001',
            nombre='HERRADURA BLANCO',
            categoria=categoria_tequila,
            factor_peso=0.95
        )
        jw_black = models.Ingrediente.objects.create(
            codigo='WHIS001',
            nombre='JOHNNIE WALKER BLACK',
            categoria=categoria_whisky,
            factor_peso=0.95
        )

        # Recetas
        trago_licor_43 = models.Receta.objects.create(
            codigo_pos='00081',
            nombre='LICOR 43 DERECHO',
            sucursal=magno_brasserie
        )
        trago_herradura_blanco = models.Receta.objects.create(
            codigo_pos='00126',
            nombre='HERRADURA BLANCO DERECHO',
            sucursal=magno_brasserie
        )
        trago_jw_black = models.Receta.objects.create(
            codigo_pos= '00167',
            nombre='JW BLACK DERECHO',
            sucursal=magno_brasserie
        )
        carajillo = models.Receta.objects.create(
            codigo_pos='00050',
            nombre='CARAJILLO',
            sucursal=magno_brasserie
        )

        # Ingredientes-Recetas
        ir_licor_43 = models.IngredienteReceta.objects.create(receta=trago_licor_43, ingrediente=licor_43, volumen=60)
        ir_herradura_blanco = models.IngredienteReceta.objects.create(receta=trago_herradura_blanco, ingrediente=herradura_blanco, volumen=60)
        ir_jw_black = models.IngredienteReceta.objects.create(receta=trago_jw_black, ingrediente=jw_black, volumen=60)
        ir_carajillo = models.IngredienteReceta.objects.create(receta=carajillo, ingrediente=licor_43, volumen=45)
