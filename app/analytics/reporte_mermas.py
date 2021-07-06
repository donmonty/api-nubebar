from django.db.models import F, Q, QuerySet, Avg, Count, Sum, Subquery, OuterRef, Exists, Func, ExpressionWrapper, DecimalField, BooleanField, CharField, DateTimeField, Case, When, IntegerField, Value
from django.db.models.functions import Greatest
from core import models
from decimal import Decimal, ROUND_UP

import datetime
from django.utils.timezone import make_aware
from django.core.exceptions import ObjectDoesNotExist


def calcular_consumos(inspeccion, fecha_inicial, fecha_final):

    # Tomamos el almacen
    almacen = inspeccion.almacen

    # Tomamos los ItemsInspeccion de la Inspeccion actual
    items_inspeccion = inspeccion.items_inspeccionados.all()

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
    # Subquery: Selección de 'peso_botella' de la última inspeccion
    sq_peso_ultima_inspeccion = Subquery(models.ItemInspeccion.objects
                                    .filter(botella=OuterRef('pk'))
                                    .order_by('-timestamp_inspeccion')
                                    .values('peso_botella')[:1]
                                )

    # Lista de ingredientes presentes en la Inspeccion
    items_inspeccion_2 = inspeccion.items_inspeccionados.all()
    items_inspeccion_2 = items_inspeccion_2.values('botella__producto__ingrediente__id')
    ingredientes_inspeccion = models.Ingrediente.objects.filter(id__in=items_inspeccion_2)

    # print('::: INGREDIENTES INSPECCION :::')
    # print(ingredientes_inspeccion)

    #----------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------

    # Seleccionamos todas las botellas cuyo ingrediente sea parte de la lista de ingredientes a inspeccionar
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
    #print(botellas_peso_anterior.values('peso_inicial', 'peso_actual', 'peso_anterior'))


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
    # Agregamos campo "densidad"
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
            fecha__gte=fecha_inicial,
            fecha__lte=fecha_final,
            venta__caja__almacen=almacen
        )
        consumo_ventas = consumos_recetas.aggregate(consumo_ventas=Sum('volumen'))

        # Consolidamos los ingredientes, su consumo de ventas y consumo real en una lista
        ingrediente_consumo = (ingrediente, consumo_ventas, consumo_real)
        consumos.append(ingrediente_consumo)


    #print('::: CONSUMO INGREDIENTES :::')
    #print(consumos)

    return consumos


"""
-----------------------------------------------------------------------------------
Esta funcion retorna el las ventas asociadas a una merma y su detalle
-----------------------------------------------------------------------------------
"""
def get_ventas_merma(merma_id):

    # Tomamos el ingrediente a analizar de la merma
    try:
        merma = models.MermaIngrediente.objects.get(id=merma_id)

    # Si la merma no existe, retornamos un status de error
    except ObjectDoesNotExist:
        data = {
            'status': '0',
            'mensaje': 'La merma solicitada no existe.'
        }
        return data

    else: 
        ingrediente = merma.ingrediente

        # Tomamos las ventas asociadas al ingrediente de la MermaIngrediente
        consumos = models.ConsumoRecetaVendida.objects.filter(
            ingrediente=ingrediente,
            fecha__gte=merma.fecha_inicial,
            fecha__lte=merma.fecha_final,
            venta__caja__almacen=merma.almacen
        )

        consumos = consumos.values('venta')

        ventas = models.Venta.objects.filter(id__in=consumos)

        # Agregamos el volumen del ingrediente especificado en la receta del trago
        sq_volumen_receta = Subquery(models.IngredienteReceta.objects.filter(receta=OuterRef('receta'), ingrediente=ingrediente).values('volumen'))
        ventas_volumen_receta = ventas.annotate(volumen_receta=sq_volumen_receta)

        # Agregamos el volumen vendido total
        ventas_volumen_vendido = ventas_volumen_receta.annotate(volumen_vendido=F('unidades') * F('volumen_receta'))

        # Convertimos el queryset en una lista de objectos
        lista_ventas = list(ventas_volumen_vendido.values('id', 'receta__nombre', 'unidades', 'receta__codigo_pos', 'fecha', 'caja__nombre', 'importe', 'volumen_receta', 'volumen_vendido'))

        # Convertimos las fechas a formato legible
        for venta in lista_ventas:
            venta['fecha'] = venta['fecha'].strftime("%d/%m/%Y")

        # Guardamos la info en un objecto, incluyendo el nombre del ingrediente y el status de exito
        data = {
            'status': '1',
            'ingrediente': merma.ingrediente.nombre,
            'detalle_ventas': lista_ventas
        }

        return data


"""
-----------------------------------------------------------------------------------
Esta funcion retorna el las botellas inspeccionadas de un ingrediente
-----------------------------------------------------------------------------------
"""
def get_botellas_merma(merma_id):

    # Tomamos la merma analizada
    merma = models.MermaIngrediente.objects.get(id=merma_id)

    # Tomamos las botellas presentes en la Inspeccion analizada
    inspeccion = merma.reporte.inspeccion
    items_inspeccion = inspeccion.items_inspeccionados
    botellas_items_inspeccion = items_inspeccion.values('botella__id')
    botellas_inspeccion = models.Botella.objects.filter(id__in=botellas_items_inspeccion)

    # Tomamos el ingrediente
    ingrediente = merma.ingrediente

    # Tomamos las botellas del ingrediente seleccionado presentes en la Inspeccion
    botellas = botellas_inspeccion.filter(producto__ingrediente=ingrediente)

    

    """
    ------------------------------------------------------
    SUBQUERIES UTILES
    ------------------------------------------------------
    """
    # SUBQUERY: Las inspecciones cuyo 'peso_botella' = None
    sq_inspecciones_none = Subquery(models.ItemInspeccion.objects
                                .filter(botella=OuterRef('pk'), peso_botella=None)
                                .order_by()
                                .values('peso_botella')[:1]
    )

    # SUBQUERY: El numero de inspecciones que cuyo 'peso_botella' = None
    sq_inspeccion_none_count = Subquery(models.ItemInspeccion.objects
                                    .filter(botella=OuterRef('pk'))
                                    .exclude(~Q(peso_botella=None))
                                    .values('botella__pk')
                                    .order_by('-timestamp_inspeccion')
                                    .annotate(inspeccion_none=Count('id'))
                                    .values('inspeccion_none')[:1]
    )

    # SUBQUERY: El número de inspecciones con 'peso_botella' = None
    sq_peso_botella_none = Subquery(models.ItemInspeccion.objects
                            .filter(botella=OuterRef('pk'))
                            .exclude(~Q(peso_botella=None))
                            .values('botella__pk')
                            .annotate(inspeccion_peso_none=Count('id'))
                            .values('inspeccion_peso_none')
    )

    # SUBQUERY: Fecha de la inspeccion con 'peso_botella' = None
    sq_fecha_inspeccion_none = Subquery(models.ItemInspeccion.objects
                                    .filter(botella=OuterRef('pk'))
                                    .exclude(~Q(peso_botella=None))
                                    .order_by('-timestamp_inspeccion')
                                    .values('timestamp_inspeccion')[:1]

    )

    # SUBQUERY: Fecha de la inspeccion con 'peso_botella' = OK
    sq_fecha_inspeccion_ok = Subquery(models.ItemInspeccion.objects
                                    .filter(botella=OuterRef('pk'))
                                    .exclude(peso_botella=None)
                                    .order_by('-timestamp_inspeccion')
                                    .values('timestamp_inspeccion')[:1]

    )

    # SUBQUERY: Peso de la botella en su inspección más reciente, descartando pesos = None
    sq_peso_ultima_inspeccion = Subquery(models.ItemInspeccion.objects
                                    .filter(botella=OuterRef('pk'))
                                    .order_by('-timestamp_inspeccion')
                                    .exclude(peso_botella=None)
                                    .values('peso_botella')[:1]
    )


    # SUBQUERY: Peso anterior de la botella (el peso registrado en el penúltimo ItemInspeccion)
    sq_peso_anterior = Subquery(models.ItemInspeccion.objects
                                .filter(botella=OuterRef('pk'))
                                .order_by('-timestamp_inspeccion')
                                .exclude(peso_botella=None)
                                .values('peso_botella')[1:2]
    )

    # SUBQUERY: La cantidad de inspecciones cuyo 'peso_botella' está OK (es decir, distinto a None)
    sq_peso_botella_ok = Subquery(models.ItemInspeccion.objects
                            .filter(botella=OuterRef('pk'))
                            .exclude(peso_botella=None)
                            .values('botella__pk')
                            .annotate(inspeccion_peso_ok=Count('id'))
                            .values('inspeccion_peso_ok')
    )

    #---------------------------------------------------------------------
    # Agregamos el estado de la botella (pero con texto, no números)
    botellas_estado = botellas.annotate(
        estado_botella=Case(

            # CASO: Botella nueva
            When(Q(estado='2'), then=ExpressionWrapper(Value('NUEVA'), output_field=CharField())),

            # CASO: Botella usada
            When(Q(estado='1'), then=ExpressionWrapper(Value('USADA'), output_field=CharField())),

            # CASO: Botella vacía
            When(Q(estado='0'), then=ExpressionWrapper(Value('SIN LIQUIDO'), output_field=CharField()))
        )
    )
    print('::: BOTELLAS - ESTADO :::')
    print(botellas_estado.values('folio', 'producto__ingrediente__nombre', 'estado_botella'))

    #---------------------------------------------------------------------
    # Agregamos 'inspecciones_none_check': Es True si la botella tiene al menos una inspección con 'peso_botella'= None
    #botellas_status_none = botellas_estado.annotate(inspecciones_none_check=ExpressionWrapper(Exists(sq_inspecciones_none), output_field=BooleanField()))

    #print('::: BOTELLAS - NONE CHECK :::')
    #print(botellas_status_none.values('folio', 'producto__ingrediente__nombre', 'inspecciones_none_check'))

    #---------------------------------------------------------------------
    # Agregamos el número de inspecciones de cada botella
    botellas_inspecciones = botellas_estado.annotate(num_inspecciones=Count('inspecciones_botella'))
    #botellas_inspecciones = botellas_status_none.annotate(num_inspecciones=Count('inspecciones_botella'))

    #---------------------------------------------------------------------
    # Agregamos el 'inspecciones_ok_count': el Numero de inspecciones cuyo 'peso_botella' está OK
    botellas_inspecciones_peso_ok = botellas_inspecciones.annotate(inspecciones_peso_ok_count=ExpressionWrapper(sq_peso_botella_ok, output_field=IntegerField()))

    #---------------------------------------------------------------------
    # Agregamos 'inspeccion_none_count': el numero de inspecciones con 'peso_botella' = None
    botellas_inspeccion_none = botellas_inspecciones_peso_ok.annotate(inspeccion_none_count=ExpressionWrapper(sq_peso_botella_none, output_field=IntegerField()))

    print('::: BOTELLAS - NONE COUNT :::')
    print(botellas_inspeccion_none.values('folio', 'producto__ingrediente__nombre', 'inspeccion_none_count'))
    #---------------------------------------------------------------------
    # Agregamos 'fecha_inspeccion_none': la fecha de la inspeccion cuyo 'peso_botella' = None
    botellas_fecha_inspeccion_none = botellas_inspeccion_none.annotate(fecha_inspeccion_none=ExpressionWrapper(sq_fecha_inspeccion_none, output_field=DateTimeField()))

    print('::: BOTELLAS - FECHA INSPECCION NONE :::')
    print(botellas_fecha_inspeccion_none.values('folio', 'fecha_inspeccion_none'))
    #---------------------------------------------------------------------
    # Agregamos 'fecha_inspeccion_ok' la fecha de la inspeccion cuyo 'peso_botella' = OK
    botellas_fecha_inspeccion_ok = botellas_fecha_inspeccion_none.annotate(fecha_inspeccion_ok=ExpressionWrapper(sq_fecha_inspeccion_ok, output_field=DateTimeField()))

    print('::: BOTELLAS - FECHA INSPECCION OK :::')
    print(botellas_fecha_inspeccion_ok.values('folio', 'fecha_inspeccion_ok'))
    #---------------------------------------------------------------------
    # Agregamos 'inspeccion_mas_reciente': la fecha de la inspeccion más reciente
    #botellas_inspeccion_mas_reciente = botellas_fecha_inspeccion_ok.annotate(inspeccion_mas_reciente=Greatest('fecha_inspeccion_none', 'fecha_inspeccion_ok'))

    #---------------------------------------------------------------------
    # Agregamos el 'peso_anterior' de la botella. 
    botellas_peso_anterior = botellas_fecha_inspeccion_ok.annotate(
        peso_anterior=Case(

            # CASO: La botella tiene 2 inspecciones, la más reciente tiene 'peso_botella' = None
            #When(Q(num_inspecciones=2) & Q(inspecciones_none_check=True) & Q(fecha_inspeccion_none__gt=F('fecha_inspeccion_ok')), then=(sq_peso_ultima_inspeccion)),
            When(Q(num_inspecciones=2) & Q(inspeccion_none_count=1) & Q(fecha_inspeccion_none__gt=F('fecha_inspeccion_ok')), then=(sq_peso_ultima_inspeccion)),

            # CASO: La botella tiene 2 inspecciones, la más reciente tiene 'peso_botella' = OK
            #When(Q(num_inspecciones=2) & Q(inspecciones_none_check=True) & Q(fecha_inspeccion_none__lt=F('fecha_inspeccion_ok')), then=F('peso_inicial')),
            When(Q(num_inspecciones=2) & Q(inspeccion_none_count=1) & Q(fecha_inspeccion_none__lt=F('fecha_inspeccion_ok')), then=F('peso_inicial')),

            # CASO: La botella tiene más de 2 inspecciones, al menos una tiene 'peso_botella' OK
            When(Q(num_inspecciones__gt=2) & Q(inspecciones_peso_ok_count__gte=1), then=(sq_peso_anterior)),

            # CASO: La botella tiene al menos 2 inspecciones, ninguna tiene 'peso_botella' OK
            When(Q(num_inspecciones__gt=1) & Q(inspecciones_peso_ok_count=None), then=F('peso_inicial')),

            # CASO: La botella tiene solo una inspeccion
            When(Q(num_inspecciones=1), then=F('peso_inicial')), 

        )
    )
    print('::: BOTELLAS - PESO ANTERIOR :::')
    print(botellas_peso_anterior.values('folio', 'producto__ingrediente__nombre', 'peso_anterior'))

    #---------------------------------------------------------------------
    # Agregamos 'volumen_actual'
    botellas_volumen_actual = botellas_peso_anterior.annotate(
        volumen_actual=ExpressionWrapper(
            (F('peso_actual') - F('peso_cristal')) * (2 - F('producto__ingrediente__factor_peso')),
            output_field=DecimalField()
        )
    )

    #---------------------------------------------------------------------
    # Agregamos 'volumen_anterior"
    botellas_volumen_anterior = botellas_volumen_actual.annotate(
        volumen_anterior=ExpressionWrapper(
            (F('peso_anterior') - F('peso_cristal')) * (2 - F('producto__ingrediente__factor_peso')),
            output_field=DecimalField()
        )
    )

    #---------------------------------------------------------------------
    # Agregamos 'diferencia_ml'
    botellas_diferencia_ml = botellas_volumen_anterior.annotate(
        diferencia_ml=ExpressionWrapper(
            F('volumen_anterior') - F('volumen_actual'), output_field=DecimalField()
        )
    )

    #---------------------------------------------------------------------
    # Agregamos 'diferencia_tragos'
    botellas_diferencia_tragos = botellas_diferencia_ml.annotate(
        diferencia_tragos=ExpressionWrapper(F('diferencia_ml') / 60, output_field=DecimalField())
        #diferencia_tragos=Case(

            # CASO: Si la diferencia es mayor a 10ml, calculamos los tragos
            #When(Q(diferencia_ml__gte=5), then=ExpressionWrapper(F('diferencia_ml') / 60, output_field=DecimalField())),

            # CASO: Si la diferencia es menor a 5ml, tragos = 0
            #When(Q(diferencia_ml__lt=5), then=ExpressionWrapper(F(0), output_field=DecimalField())),
        #)
    )
    print('::: BOTELLAS - DIFERENCIA TRAGOS :::')
    print(botellas_diferencia_tragos.values('folio', 'producto__ingrediente__nombre', 'volumen_actual', 'volumen_anterior', 'diferencia_ml', 'diferencia_tragos'))

    #---------------------------------------------------------------------
    # Calculamos la diferencia total en mililitros
    diferencia_total_ml = botellas_diferencia_tragos.aggregate(Sum('diferencia_ml'))
    diferencia_total_ml = round(float(diferencia_total_ml['diferencia_ml__sum'].quantize(Decimal('.01'), rounding=ROUND_UP)))

    print('::: BOTELLAS - DIFERENCIA TOTAL ML :::')
    print(diferencia_total_ml)

    #---------------------------------------------------------------------
    # Calculamos la diferencia total en tragos
    diferencia_total_tragos = botellas_diferencia_tragos.aggregate(Sum('diferencia_tragos'))
    diferencia_total_tragos = float(diferencia_total_tragos['diferencia_tragos__sum'].quantize(Decimal('.01'), rounding=ROUND_UP))

    # Ordenamos el queryset por 'estado_botella'
    botellas_diferencia_tragos.order_by('-estado_botella')

    """
    ---------------------------------------------------------------------
    Preparamos los datos del queryset para construir el reporte
    ---------------------------------------------------------------------
    """

    lista_botellas = list(botellas_diferencia_tragos.values('folio', 'estado_botella', 'volumen_actual', 'volumen_anterior', 'diferencia_ml', 'diferencia_tragos'))

    # Ordenamos la lista de botellas por su estado
    lista_botellas = sorted(lista_botellas, key=lambda x: x['estado_botella'], reverse=True)

    print('::: LISTA - BOTELLAS ORDENADAS :::')
    print(lista_botellas)

    for botella in lista_botellas:

        botella['volumen_actual'] = round(float(botella['volumen_actual'].quantize(Decimal('.01'), rounding=ROUND_UP)))
        botella['volumen_anterior'] = round(float(botella['volumen_anterior'].quantize(Decimal('.01'), rounding=ROUND_UP)))
        botella['diferencia_ml'] = round(float(botella['diferencia_ml'].quantize(Decimal('.01'), rounding=ROUND_UP)))
        botella['diferencia_tragos'] = float(botella['diferencia_tragos'].quantize(Decimal('.01'), rounding=ROUND_UP))

    
    # Construimos el reporte

    reporte = {
        'status': 'success',
        'data': {
            'diferencia_total_ml': diferencia_total_ml,
            'diferencia_total_tragos': diferencia_total_tragos,
            'botellas': lista_botellas
        }
    }

    print('::: REPORTE :::')
    print(reporte)

    return reporte


    





    
