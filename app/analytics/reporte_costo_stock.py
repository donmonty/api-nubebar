from django.db.models import F, Q, QuerySet, Avg, Count, Sum, Subquery, OuterRef, Exists, Func, ExpressionWrapper, DecimalField, Case, When
from core import models
from decimal import Decimal
import decimal
import datetime
from decimal import Decimal, ROUND_UP


def get_costo_stock(almacen):

    # Si no hay botellas registradas en el almacen, entonces status = 0
    if almacen.botellas_almacen.all().count() == 0:
        return {'status': '0'}

    # Tomamos todas las botellas del almacen
    botellas = models.Botella.objects.filter(almacen=almacen)

    # Excluimos las botellas vacias
    botellas = botellas.exclude(estado='0')

    #----------------------------------------------------------------------
    # Agregamos el campo 'volumen_ml'
    volumen_botellas = botellas.annotate(
        volumen_ml=ExpressionWrapper(
            (F('peso_actual') - F('peso_cristal')) * F('producto__ingrediente__factor_peso'),
            output_field=DecimalField()
        )
    )

    #----------------------------------------------------------------------
    # Agregamos el campo 'costo_ml'
    costo_ml_botellas = volumen_botellas.annotate(
        costo_ml=ExpressionWrapper(
            F('precio_unitario') / F('capacidad'),
            output_field=DecimalField()
        )
    )

    #----------------------------------------------------------------------
    # Agregamos el campo 'costo_botella'
    costo_botellas = costo_ml_botellas.annotate(
        costo_botella=ExpressionWrapper(
            F('costo_ml') * F('volumen_ml'),
            output_field=DecimalField()
        )
    )

    #----------------------------------------------------------------------
    # Calculamos el costo total del stock
    costo_total = costo_botellas.aggregate(Sum('costo_botella', output_field=DecimalField()))


    print('COSTO BOTELLAS')
    print(costo_botellas.values('folio', 'ingrediente', 'capacidad', 'precio_unitario', 'peso_actual', 'volumen_ml', 'costo_ml', 'costo_botella'))

    lista_costos = list(costo_botellas.values('folio', 'ingrediente', 'capacidad', 'precio_unitario', 'peso_actual', 'volumen_ml', 'costo_ml', 'costo_botella'))

    for item in lista_costos:
        item['precio_unitario'] = float(item['precio_unitario'].quantize(Decimal('.01'), rounding=ROUND_UP))
        item['volumen_ml'] = float(item['volumen_ml'].quantize(Decimal('.01'), rounding=ROUND_UP))
        item['costo_ml'] = float(item['costo_ml'].quantize(Decimal('.01'), rounding=ROUND_UP))
        item['costo_botella'] = float(item['costo_botella'].quantize(Decimal('.01'), rounding=ROUND_UP))
        #print(costo)

    print('::: LISTA COSTOS :::')
    print(lista_costos)

    fecha = datetime.date.today()
    fecha = fecha.strftime("%d/%m/%Y")

    costo_total = float(costo_total['costo_botella__sum'].quantize(Decimal('.01'), rounding=ROUND_UP))

    print("::: COSTO TOTAL STOCK :::")
    print(costo_total)

    reporte = {
        'status': '1',
        'almacen_id': almacen.id,
        'nombre_almacen': almacen.nombre,
        'sucursal': almacen.sucursal.nombre,
        'fecha': fecha,
        'costo_total': costo_total,
        'data': lista_costos
    }

    return reporte

