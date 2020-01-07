from django.db.models import F, Q, QuerySet, Avg, Count, Sum, Subquery, OuterRef, Exists, Func, ExpressionWrapper, DecimalField, IntegerField, Case, When
from core import models
from decimal import Decimal, ROUND_UP

import datetime
import math

from django.utils.timezone import make_aware
from django.core.exceptions import ObjectDoesNotExist


def calcular_restock(sucursal_id):

    # Tomamos la sucursal
    sucursal = models.Sucursal.objects.get(id=sucursal_id)

    # Definimos las fechas del reporte
    fecha_final = datetime.date.today()
    fecha_inicial = fecha_final - datetime.timedelta(days=7)

    # Tomamos los Productos asociados a la sucursal
    botellas_sucursal = models.Botella.objects.filter(sucursal=sucursal).values('producto').distinct()
    productos_sucursal = models.Producto.objects.filter(id__in=botellas_sucursal).order_by('nombre_marca')

    # Tomamos las botellas relevantes para el periodo del análisis:
    # - Las que ya estaban antes y no han salido
    # - Las que ya estaban antes y salieron
    # - Las que entraron y salieron en el periodo
    # - Las que entraron en el periodo y no han salido
    
    #botellas_periodo = models.Botella.objects.filter(
    botellas_periodo = botellas_sucursal.filter(

        Q(fecha_registro__lte=fecha_inicial, fecha_baja=None) |
        Q(fecha_registro__lte=fecha_inicial, fecha_baja__gte=fecha_inicial, fecha_baja__lte=fecha_final) |
        Q(fecha_registro__gte=fecha_inicial, fecha_baja__lte=fecha_final) |
        Q(fecha_registro__gte=fecha_inicial, fecha_baja=None)
    )

    # Agregamos el numero de inspecciones por botella
    botellas_periodo = botellas_periodo.annotate(num_inspecciones=Count('inspecciones_botella'))

    """
    --------------------------------------------------------
    SUBQUERIES UTILES
    --------------------------------------------------------
    """

    # Subquery: Selección de 'peso_botella' de la primera inspeccion del periodo analizado
    sq_peso_primera_inspeccion = Subquery(models.ItemInspeccion.objects
                                    .filter(botella=OuterRef('pk'), timestamp_inspeccion__gte=fecha_inicial, timestamp_inspeccion__lte=fecha_final)
                                    .order_by('timestamp_inspeccion')
                                    #.exclude(peso_botella=None)
                                    .values('peso_botella')[:1]
    )
    # Subquery: Igual que la anterior, pero esta excluye las inspecciones con 'peso_botella' = None
    sq_peso_inspeccion_inicial = Subquery(models.ItemInspeccion.objects
                                    .filter(botella=OuterRef('pk'), timestamp_inspeccion__gte=fecha_inicial, timestamp_inspeccion__lte=fecha_final)
                                    .order_by('timestamp_inspeccion')
                                    .exclude(peso_botella=None)
                                    .values('peso_botella')[:1]
    )
    # Subquery: La cantidad de inspecciones cuyo 'peso_botella' está OK (es decir, distinto a None)
    sq_peso_botella_ok = Subquery(models.ItemInspeccion.objects
                    .filter(botella=OuterRef('pk'), timestamp_inspeccion__gte=fecha_inicial, timestamp_inspeccion__lte=fecha_final)
                    .exclude(peso_botella=None)
                    .values('botella__pk')
                    .annotate(inspeccion_peso_ok=Count('id'))
                    .values('inspeccion_peso_ok')
    )
    # Subquery: Cantidad de inspecciones por botella que caen dentro del periodo de análisis
    sq_inspeccion_inside = Subquery(models.ItemInspeccion.objects
                                .filter(botella=OuterRef('pk'), timestamp_inspeccion__gte=fecha_inicial, timestamp_inspeccion__lte=fecha_final)
                                #.exclude(peso_botella=None)
                                .values('botella__pk')
                                .annotate(inspeccion_count_inside=Count('id'))
                                .values('inspeccion_count_inside')
    )
    #----------------------------------------------------------------------

    #----------------------------------------------------------------------
    # Agregamos el 'peso_inspeccion_inicial'
    # botellas_peso_inspeccion_inicial = botellas_periodo.annotate(
    #     peso_inspeccion_inicial=Case(
    #         # CASO 1: La botella tiene más de 1 inspeccion
    #         When(Q(num_inspecciones__gt=1), then=sq_peso_inspeccion_inicial)
    #         # CASO 2: La botella tiene solo 1 inspeccion
    #         When(Q(num_inspecciones=1), then=F('peso_inicial')),
    #         # CASO 2: La botella no tiene inspecciones
    #         When(Q(num_inspecciones=0), then=F('peso_inicial'))
    #     )
    # )

    #----------------------------------------------------------------------
    # Agregamos 'inspecciones_ok_count': El numero de inspecciones que que son parte del periodo de análisis
    botellas_inspecciones_ok = botellas_periodo.annotate(inspecciones_ok_count=ExpressionWrapper(sq_inspeccion_inside, output_field=IntegerField()))

    #print('::: BOTELLAS - INSPECCIONES OK COUNT :::')
    #print(botellas_inspecciones_ok.values('folio', 'producto__ingrediente__nombre', 'inspecciones_ok_count'))

    #----------------------------------------------------------------------
    # Agregamos 'inspecciones_peso_ok_count': El numero de inspecciones con 'peso_botella' != None
    botellas_inspecciones_peso_ok = botellas_inspecciones_ok.annotate(inspecciones_peso_ok_count=ExpressionWrapper(sq_peso_botella_ok, output_field=IntegerField()))

    #print('::: BOTELLAS - PESO OK COUNT :::')
    #print(botellas_inspecciones_peso_ok.values('folio', 'producto__ingrediente__nombre', 'inspecciones_peso_ok_count'))

    #----------------------------------------------------------------------
    # Agregamos el peso de la última inspección para más adelante checar si es None
    botellas_peso_primera_inspeccion = botellas_inspecciones_peso_ok.annotate(peso_primera_inspeccion=ExpressionWrapper(sq_peso_primera_inspeccion, output_field=IntegerField()))

    #print('::: BOTELLAS - PESO PRIMERA INSPECCION :::')
    #print(botellas_peso_primera_inspeccion.values('folio', 'producto__ingrediente__nombre', 'peso_primera_inspeccion'))



    #----------------------------------------------------------------------
    # Agregamos el 'peso_inspeccion_inicial'
    botellas_peso_inspeccion_inicial = botellas_peso_primera_inspeccion.annotate(
        peso_inspeccion_inicial=Case(

            # CASO 1: La botella tiene más de 1 inspeccion, pero ninguna ocurrió en el periodo de análisis
            When(Q(num_inspecciones__gt=1) & Q(inspecciones_ok_count=None), then=F('peso_actual')),

            # CASO 1A: La botella tiene más de una inspeccion, al menos 2 ocurrieron en el periodo analizado, al menos 1 tiene 'peso_botella' != None, pero la primera tiene 'peso_botella' = None
            When(Q(num_inspecciones__gt=1) & Q(inspecciones_ok_count__gt=1) & Q(inspecciones_peso_ok_count__gt=0) & Q(peso_primera_inspeccion=None), then=sq_peso_inspeccion_inicial),

            # CASO 1B: La botella tiene más de una inspección, al menos una ocurrió en el periodo analizado, y al menos una tiene 'peso_botella' != None
            When(Q(num_inspecciones__gt=1) & Q(inspecciones_ok_count__gt=0) & Q(inspecciones_peso_ok_count__gt=0), then=sq_peso_inspeccion_inicial),

            # CASO 1C: La botella tiene más de una inspección, al menos una ocurrió en el periodo analizado, pero ninguna tiene 'peso_botella' != None
            When(Q(num_inspecciones__gt=1) & Q(inspecciones_ok_count__gt=0) & Q(inspecciones_peso_ok_count=None), then=F('peso_actual')),

            # CASO 1D: La botella tiene más de 1 inspección, al menos una ocurrió en el periodo analizado
            When(Q(num_inspecciones__gt=1) & Q(inspecciones_ok_count__gt=0), then=sq_peso_inspeccion_inicial),

            # CASO 2: La botella tiene solo 1 inspeccion, pero esta ocurrió fuera del periodo analizado
            When(Q(num_inspecciones=1) & Q(inspecciones_ok_count=None), then=F('peso_actual')),

            # CASO 2A: la botella tiene solo 1 inspeccion, esta ocurrio dentro del periodo analizado y su 'peso_botella' != None
            When(Q(num_inspecciones=1) & Q(inspecciones_ok_count=1) & Q(inspecciones_peso_ok_count__gt=0), then=F('peso_inicial')),

            # CASO 2B: La botella tiene solo 1 inspeccion, ocurrió dentro del periodo analizado, pero su 'peso_botella' es None
            When(Q(num_inspecciones=1) & Q(inspecciones_ok_count=1) & Q(inspecciones_peso_ok_count=None), then=F('peso_inicial')),

            # CASO 2C: la botella tiene solo 1 inspeccion, esta ocurrio dentro del periodo analizado 
            When(Q(num_inspecciones=1) & Q(inspecciones_ok_count=1), then=F('peso_inicial')),

            # CASO 3: La botella no tiene inspecciones
            When(Q(num_inspecciones=0), then=F('peso_inicial')),
        )
    )

    #----------------------------------------------------------------------
    # Agregamos 'dif_peso'
    # botellas_dif_peso = botellas_peso_inspeccion_inicial.annotate(
    #     dif_peso=Case(
    #         # Excluimos las botellas con 'peso_inspeccion_inicial' = None
    #         # Estas son botellas que sí tuvieron consumo, pero no dentro del periodo del reporte
    #         When(Q(peso_inspeccion_inicial=None), then=0),
    #         # Si 'peso_inspeccion_inicial' es entero, todo OK
    #         When(Q(peso_inspeccion_inicial__lte=0) | Q(peso_inspeccion_inicial__gte=0), then=F('peso_inspeccion_inicial') - F('peso_actual')),

    #     )
    # )

    #----------------------------------------------------------------------
    # Agregamos 'dif_peso'
    botellas_dif_peso = botellas_peso_inspeccion_inicial.annotate(
        dif_peso=F('peso_inspeccion_inicial') - F('peso_actual')
    )



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

    #----------------------------------------------------------------------
    # Agregamos 'volumen_actual'
    botellas_volumen_actual = botellas_consumo.annotate(
        volumen_actual=ExpressionWrapper(
            #((F('peso_actual') - F('peso_cristal')) * F('producto__ingrediente__factor_peso')),
            (F('peso_actual') - F('peso_cristal')) * (2 - F('producto__ingrediente__factor_peso')),
            output_field=DecimalField()
        )
    )

    #----------------------------------------------------------------------
    # Agregamos un campo con la diferencia entre 'consumo_ml' y 'volumen_actual'
    botellas_dif_volumen = botellas_volumen_actual.annotate(
        #dif_volumen=F('volumen_actual') - F('consumo_ml')
        dif_volumen=F('consumo_ml') - F('volumen_actual')
    )

    #----------------------------------------------------------------------
    #----------------------------------------------------------------------
    #----------------------------------------------------------------------
    
    # botellas_reporte = botellas_dif_volumen

    # # Creamos una lista para guardar los registros por producto del reporte
    # lista_registros = []

    # # Creamos una variable para guardar el total de la compra sugerida
    # total_acumulado = 0
    # #print('TOTAL ACUMULADO INICIAL')
    # #print(type(total_acumulado))

    # # Iteramos por cada uno de los productos asociados a la sucursal
    # for producto in productos_sucursal:

    #     # Tomamos las botellas asociadas al producto en cuestion
    #     botellas_producto = botellas_reporte.filter(producto=producto)

    #     # Sumamos el volumen actual de las botellas
    #     volumen_total = botellas_producto.aggregate(volumen_total=Sum('volumen_actual'))
    #     volumen_total = float(volumen_total['volumen_total'].quantize(Decimal('.01'), rounding=ROUND_UP))

    #     # Sumamos consumo de las botellas
    #     consumo_total = botellas_producto.aggregate(consumo_total=Sum('consumo_ml'))
    #     consumo_total = float(consumo_total['consumo_total'].quantize(Decimal('.01'), rounding=ROUND_UP))

    #     # Sumamos las diferencias
    #     diferencia_total = botellas_producto.aggregate(diferencia_total=Sum('dif_volumen'))
    #     #print('::: DIFERENCIA TOTAL :::')
    #     #print(diferencia_total)

    #     diferencia_total = float(diferencia_total['diferencia_total'].quantize(Decimal('.01'), rounding=ROUND_UP))

    #     # Si la diferencia es negativa, continuamos con el siguiente producto
    #     # Esto significa que hay suficiente stock para satisfacer el consumo
    #     if diferencia_total <= 0:
    #         continue

    #     # Calculamos el restock por producto
    #     unidades_restock = diferencia_total / producto.capacidad
    #     unidades_restock = math.ceil(unidades_restock)

    #     # Tomamos el precio unitario
    #     precio_unitario = float((producto.precio_unitario).quantize(Decimal('.01'), rounding=ROUND_UP))

    #     # Calculamos el subtotal
    #     subtotal = float(Decimal(unidades_restock * precio_unitario).quantize(Decimal('.01'), rounding=ROUND_UP))

    #     # Calculamos el IVA
    #     iva = subtotal * 0.16
    #     iva = float(Decimal(iva).quantize(Decimal('.01'), rounding=ROUND_UP))
    #     #print('::: IVA :::')
    #     #print(iva)

    #     # Calculamos el Total
    #     total = subtotal + iva
    #     total = float(Decimal(total).quantize(Decimal('.01'), rounding=ROUND_UP))
    #     #print('::: TOTAL :::')
    #     #print(total)
    #     #print(type(total))

    #     # Sumamos al total acumulado
    #     total_acumulado = total_acumulado + total
    #     total_acumulado = float(Decimal(total_acumulado).quantize(Decimal('.01'), rounding=ROUND_UP))

    #     # Construimos el registro del producto
    #     registro = {
    #         'producto': producto.nombre_marca,
    #         'stock_ml': volumen_total,
    #         'demanda_ml': consumo_total,
    #         'faltante': diferencia_total,
    #         'compra_sugerida': unidades_restock,
    #         'precio_lista': precio_unitario,
    #         'subtotal': subtotal,
    #         'iva': iva,
    #         'total': total  
    #     }

    #     lista_registros.append(registro)

    #-------------------------------------------------------------
    #-------------------------------------------------------------
    #-------------------------------------------------------------

    botellas_reporte = botellas_dif_volumen

    # Creamos un generator para calcular los totales de las botellas para cada producto
    def generator_restock(productos, botellas_reporte):

        total_acumulado = 0

        # Ordenamos los Productos por 'nombre_marca'
        productos = productos.order_by('nombre_marca')
        lista_de_productos = list(productos.values('nombre_marca'))

        #print('::: PRODUCTOS :::')
        #print(lista_de_productos)

        #print('::: PRODUCTOS SUCURSAL :::')
        print('::: BOTELLAS PRODUCTO :::')

        for producto in productos:

            
            #print(producto.nombre_marca)

            # Si NO hay botellas asociadas a ese producto, continuamos con el siguiente producto
            if not botellas_reporte.filter(producto=producto).exists():
                continue

            # Tomamos las botellas asociadas al producto en cuestion
            botellas_producto = botellas_reporte.filter(producto=producto)
            #print(list(botellas_producto.values('folio')))

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
            iva = float(Decimal(iva).quantize(Decimal('.01'), rounding=ROUND_UP))
            #print('::: IVA :::')
            #print(iva)

            # Calculamos el Total
            total = subtotal + iva
            total = float(Decimal(total).quantize(Decimal('.01'), rounding=ROUND_UP))
            #print('::: TOTAL :::')
            #print(total)
            #print(type(total))

            # Sumamos al total acumulado
            #total_acumulado = total_acumulado + total
            #total_acumulado = float(Decimal(total_acumulado).quantize(Decimal('.01'), rounding=ROUND_UP))

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

            #lista_registros.append(registro)
            yield registro

    # Guardamos el generator en una variable
    restock_producto = generator_restock(productos_sucursal, botellas_reporte)

    # Creamos otro generator para iterar por el primer generator
    lista_restock = (registro for registro in restock_producto)

    # Convertimos los resultados del nuevo generator en una lista
    lista_restock = list(lista_restock)
    #lista_restock = list(lista_restock['registro'])
    #total_acumulado = lista_restock['total_acumulado']

    # Orenamos la lista de restock por 'compra_sugerida' de mayor a menor
    lista_restock = sorted(lista_restock, key=lambda x: x['compra_sugerida'], reverse=True)

    #print('::: LISTA RESTOCK :::')
    #print(lista_restock)

    # Si no hubo comsumo de productos notificamos al cliente
    if len(lista_restock) == 0:
        response = {
            'status': 'error',
            'message': 'No se consumió ningún producto en los últimos 7 días.'
        }
        return response

    # Creamos una funcion para iterar por el output del generator y calcular el 'total_acumulado'
    def calcular_costo_total(lista_restock):

        total_acumulado = 0

        for item in lista_restock:

            total = item['total']
            total_acumulado = total + total_acumulado

        total_acumulado = float(Decimal(total_acumulado).quantize(Decimal('.01'), rounding=ROUND_UP))

        return total_acumulado

    # Ejecutamos la función
    costo_total = calcular_costo_total(lista_restock)

    #print('::: COSTO TOTAL :::')
    #print(costo_total)

    # Tomamos la fecha para el reporte
    fecha_reporte = datetime.date.today()
    fecha_reporte = fecha_reporte.strftime("%d/%m/%Y")

    # Construimos el reporte
    reporte = {
        'status': 'success',
        #'sucursal': sucursal.nombre,
        'sucursal': sucursal.nombre,
        'fecha': fecha_reporte,
        'costo_total': costo_total,
        'data': lista_restock
    }

    return reporte



