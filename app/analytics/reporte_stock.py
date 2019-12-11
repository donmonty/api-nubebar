from django.db.models import F, Q, QuerySet, Avg, Count, Sum, Subquery, OuterRef, Exists, Func, ExpressionWrapper, DecimalField, IntegerField, Case, When
from core import models
from decimal import Decimal
import decimal
import datetime
from decimal import Decimal, ROUND_UP
from django.core.exceptions import ObjectDoesNotExist

def get_stock(sucursal):

    """
    Esta función retorna la lista de productos y el número de unidades en stock 
    para una sucursal específica.

    INPUTS:
    - Sucursal
    

    -------------------------------------------------------------------------------
    PRODUCTO							UNIDADES		CATEGORIA           
    -------------------------------------------------------------------------------
    LICOR 43 750						2				LICOR						
    ...............................................................................

    Folio		    Capacidad   Almacen     PRECIO      ML      COSTO ML    COSTO
    ------------------------------------------------------------------------------
    Ii9999999999	750         BARRA 1     $347.50     750     
    Ii0000000000	750         BODEGA      $347.50     300

    -------------------------------------------------------------------------------

    """

    # Si no hay botellas registradas en la sucursal, retornamos error:
    if sucursal.botellas_sucursal.all().count() == 0:
        return {
            'status': 'error',
            'message': 'Esta sucursal no tiene botellas registradas.'
        }

    # Tomamos todas las botellas de la sucursal
    botellas = models.Botella.objects.filter(sucursal=sucursal)
    # Excluimos las botellas vacías y perdidas
    botellas = botellas.exclude(estado='0')
    botellas = botellas.exclude(estado='3')
    # Creamos una lista con los ids de los productos asociados a las botellas
    botellas = botellas.values('producto')

    # Tomamos solo los productos que tienen botellas nuevas o usadas 
    productos = models.Producto.objects.filter(id__in=botellas).values('id', 'nombre_marca', 'ingrediente__categoria__nombre')

    # Tomamos todos los blueprints
    #productos = models.Producto.objects.all().values('id', 'nombre_marca', 'ingrediente__categoria__nombre')
    #print('::: QUERYSET PRODUCTOS - CATEGORIA :::')
    #print(productos)
    
    # Agregamos el campo 'unidades' que indique el numero de botellas por blueprint y excluimos aquellos con cero unidades
    #productos = productos.annotate(unidades=Count('botellas')).exclude(unidades=0)

    sq_num_botellas_producto = Subquery(models.Botella.objects
                                    .filter(producto=OuterRef('pk'), sucursal=sucursal)
                                    .exclude(Q(estado='0') | Q(estado='3'))
                                    .values('producto__pk')
                                    .annotate(num_botellas=Count('id'))
                                    .values('num_botellas')
    )

    productos = productos.annotate(unidades=sq_num_botellas_producto)
    productos = productos.exclude(unidades=0)

    # Ordenamos los productos del queryset por nombre
    productos = productos.order_by('nombre_marca')

    #print('::: QUERYSET PRODUCTOS - COUNT BOTELLAS :::')
    #print(productos.values('ingrediente__nombre', 'unidades'))

    # Creamos una lista con todos los productos
    lista_productos = list(productos)
    #print('::: LISTA DE PRODUCTOS :::')
    #print(lista_productos)

    # Calculamos el número total de productos en la sucursal
    total_productos = productos.aggregate(Sum('unidades', output_field=IntegerField()))
    #print('::: TOTAL PRODUCTOS :::')
    #print(total_productos)

    # Tomamos la fecha
    fecha = datetime.date.today()
    fecha = fecha.strftime("%d/%m/%Y")
    #print('::: FECHA :::')
    #print(fecha)

    # Construimos el reporte
    reporte = {
        'status': 'success',
        'data': {
            'sucursal': sucursal.nombre,
            'fecha': fecha,
            'total_botellas': total_productos,
            'botellas': lista_productos
        }
    }

    return reporte


"""
-------------------------------------------------------------------------
Esta funcion retorna una lista de botellas asociadas a un producto para
una sucursal específica. Es la vista de detalle de la función anterior.

INPUTS:
- ID del producto
- ID de la sucursal
-------------------------------------------------------------------------
"""
def get_stock_detalle(producto_id, sucursal_id):

    # Checamos si existen la Sucursal y el Producto del request
    try:

        producto = models.Producto.objects.get(id=producto_id)
        sucursal = models.Sucursal.objects.get(id=sucursal_id)

    # Si no existe la sucursal o el producto, notificamos al cliente
    except ObjectDoesNotExist:

        response = {
            'status': 'error',
            'message': 'El producto y/o sucursal indicados no existen'
        }

        return response

    # Si la sucursal y el producto del request existen, continuamos
    else:

        # Tomamos las botellas del producto y sucursal indicados en el request
        botellas = models.Botella.objects.filter(sucursal=sucursal, producto=producto).values('folio', 'capacidad', 'almacen__nombre', 'precio_unitario', 'peso_actual')

        # Excluimos las botellas vacías y perdidas
        botellas = botellas.exclude(estado='0')
        botellas = botellas.exclude(estado='3')

        # Si el numero de botellas == 0, notificamos al cliente
        if botellas.count() == 0:
            response = {
                'status': 'error',
                'message': 'No hay botellas asociadas a este producto.'
            }

        #----------------------------------------------------------------------
        # Agregamos el campo 'volumen_ml'
        botellas = botellas.annotate(
            volumen_ml=ExpressionWrapper(
                #(F('peso_actual') - F('peso_cristal')) * F('producto__ingrediente__factor_peso'),
                (F('peso_actual') - F('peso_cristal')) * (2 - F('producto__ingrediente__factor_peso')),
                output_field=DecimalField()
            )   
        )

        #----------------------------------------------------------------------
        # Agregamos el campo 'costo_ml'
        botellas = botellas.annotate(
            costo_ml=ExpressionWrapper(
                F('precio_unitario') / F('capacidad'),
                output_field=DecimalField()
            )
        )

        #----------------------------------------------------------------------
        # Agregamos el campo 'costo_botella'
        botellas = botellas.annotate(
            costo_botella=ExpressionWrapper(
                F('costo_ml') * F('volumen_ml'),
                output_field=DecimalField()
            )
        )

        # Ordenamos las botellas por volumen contenido
        botellas = botellas.order_by('volumen_ml')

        # Creamos una lista con las botellas 
        lista_botellas = list(botellas)

        # Procesamos los decimales para poder mostrarlos en el response
        for item in lista_botellas:
            item['precio_unitario'] = float(item['precio_unitario'].quantize(Decimal('.01'), rounding=ROUND_UP))
            item['volumen_ml'] = float(item['volumen_ml'].quantize(Decimal('.01'), rounding=ROUND_UP))
            item['costo_ml'] = float(item['costo_ml'].quantize(Decimal('.01'), rounding=ROUND_UP))
            item['costo_botella'] = float(item['costo_botella'].quantize(Decimal('.01'), rounding=ROUND_UP))
            #print(costo)

        #print('::: LISTA BOTELLAS - DECIMALES OK :::')
        #print(lista_botellas)

        # Construimos el reporte
        reporte = {
            'status': 'success',
            'data': lista_botellas
        }

        return reporte








