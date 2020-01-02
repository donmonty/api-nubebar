from rest_framework import viewsets, mixins
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, action, permission_classes, authentication_classes
from rest_framework.authentication import TokenAuthentication
#from inventarios.permissions import PermisoSucursal
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from django.db.models import F, Q, QuerySet, Avg, Count, Sum, Subquery, OuterRef, Exists, Func, ExpressionWrapper, DecimalField, Case, When
from django.core.exceptions import ObjectDoesNotExist
#from django.db.models import F, Q, QuerySet, Avg, Count, Sum, Subquery, OuterRef, Exists
#from django.shortcuts import get_object_or_404
#import math
import json
import datetime
from analytics import serializers
from analytics import reporte_costo_stock as cs
from analytics import reporte_mermas as rm
from analytics import reporte_stock as rs
from analytics import reporte_restock as restock
from analytics import reporte_productos_sin_registro as r_sin_registro
from core import models


"""
-----------------------------------------------------------------------------------
Endpoint para crear un Reporte de Mermas
-----------------------------------------------------------------------------------
"""
@api_view(['POST'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def crear_reporte_mermas(request):

    if request.method == 'POST':

        # Tomamos los IDs de la inspeccion y el almacen del reporte
        inspeccion_id = request.data['inspeccion']
        inspeccion = models.Inspeccion.objects.get(id=inspeccion_id)
        almacen_id = inspeccion.almacen.id

        payload = {
            'inspeccion': inspeccion_id,
            'almacen': almacen_id
        }

        # Alimentamos el serializer con el payload de forma parcial
        serializer = serializers.ReporteMermasCreateSerializer(data=payload, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------------------------------------
Endpoint para ver un Reporte de Mermas especifico
-----------------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def get_reporte_mermas(request, reporte_id):

    if request.method == 'GET':

        # Tomamos el id dek reporte a consultar
        reporte_id = int(reporte_id)
        # Tomamos el reporte a consultar
        reporte = models.ReporteMermas.objects.get(id=reporte_id)
        # Serializamos el reporte
        serializer = serializers.ReporteMermasDetalleSerializer(reporte)
        # Retornamos el reporte de mermas serializado
        return Response(serializer.data)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


"""
---------------------------------------------------------------------------------
Endpoint para ver los reportes de mermas de un almacen
----------------------------------------------------------------------------------
"""
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def get_lista_reportes_mermas(request, almacen_id):

    if request.method == 'GET':

        #inspeccion_id = int(inspeccion_id)
        almacen = int(almacen_id)
        almacen = models.Almacen.objects.get(id=almacen_id)
        usuario = request.user

        sucursal_id = almacen.sucursal.id
        sucursales_usuario = usuario.sucursales.all()
        lista_sucursales = [sucursal.id for sucursal in sucursales_usuario]

        if sucursal_id in lista_sucursales:
            queryset = models.ReporteMermas.objects.filter(almacen=almacen).order_by('-fecha_registro')
            serializer = serializers.ReporteMermasListSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            mensaje = {'mensaje': 'No estas autorizado para consultar reportes de esta sucursal.'}
            return Response(mensaje)

    else: 
        Response(status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------------------------------------
Endpoint para ver un Reporte de Costo de Stock para un almacen
-----------------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def get_reporte_costo_stock(request, almacen_id):

    if request.method == 'GET':

        # Tomamos el id del almacen a consultar
        almacen_id = int(almacen_id)
        # Tomamos el reporte a consultar
        almacen = models.Almacen.objects.get(id=almacen_id)

        # Ejecutamos el reporte
        reporte = cs.get_costo_stock(almacen)

        # Si no hay botellas en el almacen, notificamos al cliente
        if reporte['status'] == '0':
            mensaje = 'Este almacen no cuenta con botellas registradas.'
            return Response(mensaje)

        else:
            return Response(reporte)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------------------------------------
Endpoint para ver el detalle de ventas de una merma dentro de un Reporte de Mermas
-----------------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def get_detalle_ventas_merma(request, merma_id):

    if request.method == 'GET':

        # Ejecutamos el script para obtener el detalle de ventas
        detalle_ventas = rm.get_ventas_merma(merma_id)

        # Si hay un error notificamos al cliente
        if detalle_ventas['status'] == '0':
            return Response(detalle_ventas, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response(detalle_ventas)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------------------------------------
Endpoint para ver un Reporte de Stock para una sucursal
-----------------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def get_reporte_stock(request, sucursal_id):

    if request.method == 'GET':

        # Tomamos el id de la sucursal a consultar
        sucursal_id = int(sucursal_id)
        # Tomamos la sucursal a consultar
        sucursal = models.Sucursal.objects.get(id=sucursal_id)

        # Ejecutamos el reporte
        reporte = rs.get_stock(sucursal)

        # Retornamos el response
        return Response(reporte)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------------------------------------
Endpoint para ver el detalle de un item en el Reporte de Stock
-----------------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def get_detalle_stock(request, producto_id, sucursal_id):

    if request.method == 'GET':

        # Tomamos los ids de la sucursal y producto a consultar
        sucursal_id = int(sucursal_id)
        producto_id = int(producto_id)

        # Ejecutamos el reporte
        reporte = rs.get_stock_detalle(producto_id, sucursal_id)

        # Retornamos el response
        return Response(reporte)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------------------------------------
Endpoint para ver el Reporte de Productos Sin Registro
-----------------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def get_reporte_productos_sin_registro(request, sucursal_id):

    if request.method == 'GET':

        # Tomamos la sucursal
        #sucursal_id = int(sucursal_id)
        sucursal = models.Sucursal.objects.get(id=sucursal_id)

        # Ejecutamos el reporte
        reporte = r_sin_registro.get_productos_sin_registro(sucursal)

        # Retornamos el response
        return Response(reporte)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------------------------------------
Endpoint para ver todas las instancias de un ProductoSinRegistro
-----------------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def get_detalle_sin_registro(request, codigo_pos, sucursal_id):

    if request.method == 'GET':

        # Ejecutamos el reporte
        reporte = r_sin_registro.get_detalle_sin_registro(codigo_pos, sucursal_id)

        return Response(reporte)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------------------------------------
Endpoint para el Reporte de Restock
-----------------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def get_reporte_restock(request, sucursal_id):

    if request.method == 'GET':

        # Ejecutamos el reporte
        reporte = restock.calcular_restock(sucursal_id)

        return Response(reporte)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)



"""
-----------------------------------------------------------------------------------
Endpoint para el Detalle de Botellas de Merma
-----------------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def get_botellas_merma(request, merma_id):

    if request.method == 'GET':

        # Ejecutamos el reporte
        reporte = rm.get_botellas_merma(merma_id)

        return Response(reporte)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)



