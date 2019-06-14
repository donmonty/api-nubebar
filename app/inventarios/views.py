from rest_framework import viewsets, mixins
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, action, permission_classes, authentication_classes
from rest_framework.authentication import TokenAuthentication
from inventarios.permissions import PermisoSucursal
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, Q, QuerySet, Avg, Count, Sum, Subquery, OuterRef, Exists
from django.shortcuts import get_object_or_404
import math
import json

from inventarios import serializers
from inventarios import scrapper
from core import models




"""
------------------------------------------------------------------
Crea una nueva Inspección y le adjunta sus ItemInspeccion
correspondientes.
------------------------------------------------------------------
"""
class InspeccionViewSet(viewsets.ModelViewSet):

    serializer_class = serializers.InspeccionPostSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    #queryset = models.Inspeccion.objects.all()

    def get_queryset(self):
        sucursal_id = self.request.data['sucursal']
        almacen_id = self.request.data['almacen']
        usuario = self.request.user
        sucursales_usuario = usuario.sucursales.all()
        lista_sucursales = [sucursal.id for sucursal in sucursales_usuario]

        if sucursal_id in lista_sucursales:
            inspecciones = models.Inspeccion.objects.filter(sucursal__id=sucursal_id, almacen__id=almacen_id)

        return inspecciones


    def checar_ultima_inspeccion(self):
        """
        Retorna los datos de la última inspección realizada en la sucursal y almacén
        del request
        """

        sucursal_id = self.request.data['sucursal']
        almacen_id = self.request.data['almacen']

        # Si existe al menos una inspección registrada en la base de datos, tomamos su fecha y estado
        if models.Inspeccion.objects.filter(sucursal__id=sucursal_id, almacen__id=almacen_id).exists():
            ultima_inspeccion = models.Inspeccion.objects.filter(sucursal__id=sucursal_id, almacen__id=almacen_id).latest('fecha_alta')
            fecha_ultima_inspeccion = ultima_inspeccion.fecha_alta
            estado_ultima_inspeccion = ultima_inspeccion.estado

            return {
                        'sucursal_id': sucursal_id,
                        'almacen_id': almacen_id,
                        'fecha': fecha_ultima_inspeccion,
                        'estado': estado_ultima_inspeccion
                    }
        
        return None

    #----------------------------------------------------------------------------------
    def get_ultimos_consumos(self):
        """
        Retorna un queryset con los últimos consumos registrados en la sucursal y almacén del request
        """

        info_ultima_inspeccion = self.checar_ultima_inspeccion()

        # Si existe una inspección previa
        if info_ultima_inspeccion is not None:

            fecha_ultima_inspeccion = info_ultima_inspeccion['fecha']
            sucursal_id = info_ultima_inspeccion['sucursal_id']
            almacen_id = info_ultima_inspeccion['almacen_id']

            # Checamos si hay consumos registrados después de la última inspección
            try:
                models.ConsumoRecetaVendida.objects.filter(
                    venta__caja__almacen__id=almacen_id,
                    fecha__gte=fecha_ultima_inspeccion
                )

            except ObjectDoesNotExist:
                return None

            else:
                ultimos_consumos = models.ConsumoRecetaVendida.objects.filter(
                    venta__caja__almacen__id=almacen_id,
                    fecha__gte=fecha_ultima_inspeccion
                )

                return ultimos_consumos

        """
        Si no hay inspecciones previas registradas, retornamos todos los consumos registrados
        para el almacén del request. Significa que apenas se va a realizar la primera inspección ever.
        """
        try:
            almacen_id = self.request.data['almacen']
            models.ConsumoRecetaVendida.objects.filter(venta__caja__almacen__id=almacen_id)

        # Si no hay consumos registrados, entonces retornamos None
        except ObjectDoesNotExist:
            return None

        else:
            ultimos_consumos = models.ConsumoRecetaVendida.objects.filter(venta__caja__almacen__id=almacen_id)

            return ultimos_consumos 

    #----------------------------------------------------------------------------------
    def get_botellas_inspeccionar(self):
        """
        Esta función construye una lista con todas las botellas a inspeccionar
        en la sucursal y almacén del request
        """
        sucursal_id = self.request.data['sucursal']
        almacen_id = self.request.data['almacen']

        # Tomamos los datos de la última inspección
        #info_ultima_inspeccion = self.checar_ultima_inspeccion()

        """
        Si existe al menos una inspección registrada:

        - Tomamos sus datos
        - Tomamos los últimos consumos registrados después de la última inspección
        - Tomamos los ingredientes de dichos consumos
        - Generamos una lista de las botellas que contienen los ingredientes consumidos

        """


        # if info_ultima_inspeccion is not None:
        #     fecha_ultima_inspeccion = info_ultima_inspeccion['fecha']
        #     sucursal_id = info_ultima_inspeccion['sucursal_id']
        #     almacen__id = info_ultima_inspeccion['almacen_id']

        # Tomamos los consumos registrados después de la última inspección
        ultimos_consumos = self.get_ultimos_consumos()

        # Si hay consumos registrados después de la última inspección:
        if ultimos_consumos is not None:
            # Tomamos los ingredientes de dichos consumos y los guardamos en una lista
            lista_ingredientes = [consumo.ingrediente for consumo in ultimos_consumos]
            # Creamos un set con ingredientes únicos
            ingredientes_unicos = set(lista_ingredientes)

            # Tomamos las botellas del almacén que contengan los ingredientes consumidos
            botellas = []
            for ingrediente in ingredientes_unicos:
                # Seleccionamos las botellas del ingrediente en cuestión
                qs_botellas_ingrediente = models.Botella.objects.filter(sucursal__id=sucursal_id, almacen__id=almacen_id, producto__ingrediente__id=ingrediente.id)
                # Excluimos las botellas VACIAS
                qs_botellas_ingrediente = qs_botellas_ingrediente.exclude(estado='0')
                # Excluimos las botellas PERDIDAS
                qs_botellas_ingrediente = qs_botellas_ingrediente.exclude(estado='3')
                # Guardamos las botellas del ingrediente en una lista
                botellas_ingrediente = [botella for botella in qs_botellas_ingrediente]
                # Agregamos las botellas a la lista maestra de botellas
                botellas += botellas_ingrediente

            return botellas

        # Si no hay consumos registrados, no retornamos ninguna botella (no hay nada que inspeccionar)
        return None
    #----------------------------------------------------------------------------------
    
    def get_serializer_context(self):
        """
        Información incluida en el contexto para el serializador:

        - Usuario del request
        - Lista de botellas a inspeccionar
        - Fecha de la última inspección
        - Estado de la última inspección

        """
        # Checamos si hay una inspección previa
        info_ultima_inspeccion = self.checar_ultima_inspeccion()

        """
        Si existe una inspección previa, tomamos sus datos, las botellas y el usuario 
        del request y guardamos todo en el contexto (para el serializador)
        """        
        if info_ultima_inspeccion is not None:
            context = super(InspeccionViewSet, self).get_serializer_context()
            fecha_ultima_inspeccion = info_ultima_inspeccion['fecha']
            estado_ultima_inspeccion = info_ultima_inspeccion['estado']
            botellas = self.get_botellas_inspeccionar()
            usuario_actual = self.request.user
            context.update(
                {
                    'lista_botellas_inspeccionar': botellas,
                    'fecha_ultima_inspeccion': fecha_ultima_inspeccion,
                    'estado_ultima_inspeccion': estado_ultima_inspeccion,
                    'usuario': usuario_actual
                }
            )

            return context

        """ Si no hay inspecciones previas, agregamos al contexto la lista de botellas y el usuario del request """
        botellas = self.get_botellas_inspeccionar()
        usuario_actual = self.request.user
        context = super(InspeccionViewSet, self).get_serializer_context()
        context.update(
            {
                'fecha_ultima_inspeccion': None,
                'lista_botellas_inspeccionar': botellas,
                'usuario': usuario_actual
            }
        )

        return context


# """
# --------------------------------------------------------------------------
# Esta clase se encarga de desplegar las diversas vistas de las inspecciones:

# - Lista de inspecciones
# - Detalle de inspección (incluyendo lista de ItemInspeccion asociados)

# --------------------------------------------------------------------------
# """
# class InspeccionDisplayViewSet(viewsets.ModelViewSet):

#     authentication_classes = (TokenAuthentication,)
#     permission_classes = (IsAuthenticated,)
#     #queryset = models.Inspeccion.objects.all()

#     def get_queryset(self):

#         if self.action == 'retrieve':
#             queryset = models.Inspeccion.objects.all()
#             return queryset

#         if self.action == 'list':
#             queryset = models.Inspeccion.objects.all()
#             sucursal_id = self.request.query_params.get('sucursal')
#             almacen_id = self.request.query_params.get('almacen')
#             usuario = self.request.user
#             sucursales_usuario = usuario.sucursales.all()
#             lista_sucursales = [sucursal.id for sucursal in sucursales_usuario]

#             if int(sucursal_id) in lista_sucursales:
#                 queryset = queryset.filter(almacen__id=int(almacen_id))

#             return queryset

    
#     def get_serializer_class(self):
#         """ Selecciona el serializer adecuado según el tipo de request """

#         if self.action == 'list':
#             return serializers.InspeccionListSerializer

#         elif self.action == 'retrieve':
#             return serializers.InspeccionDetalleSerializer 


"""
--------------------------------------------------------------------------
Esta clase despliega la lista de inspecciones de un almacén
--------------------------------------------------------------------------
"""

class ListaInspeccionesView(viewsets.GenericViewSet, mixins.ListModelMixin):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.InspeccionListSerializer

    def get_queryset(self):
        queryset = models.Inspeccion.objects.all()
        #sucursal_id = self.kwargs['sucursal_id']
        almacen_id = self.kwargs['almacen_id']
        almacen = models.Almacen.objects.get(id=almacen_id)
        sucursal_id = almacen.sucursal.id
        usuario = self.request.user
        sucursales_usuario = usuario.sucursales.all()
        lista_sucursales = [sucursal.id for sucursal in sucursales_usuario]

        if sucursal_id in lista_sucursales:
            queryset = queryset.filter(almacen__id=almacen_id).order_by('-fecha_alta')
            return queryset

        else:
            queryset = models.Inspeccion.objects.none()
            return queryset


"""
---------------------------------------------------------------------------------
Esta endpoint despliega la lista de inspecciones DIARIAS o TOTALES de un almacén
----------------------------------------------------------------------------------
"""
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def get_lista_inspecciones(request, almacen_id, tipo_id):

    if request.method == 'GET':

        almacen_id = int(almacen_id)
        tipo_id = tipo_id
        usuario = request.user

        almacen = models.Almacen.objects.get(id=almacen_id)
        sucursal_id = almacen.sucursal.id
        sucursales_usuario = usuario.sucursales.all()
        lista_sucursales = [sucursal.id for sucursal in sucursales_usuario]

        if sucursal_id in lista_sucursales:
            queryset = models.Inspeccion.objects.filter(almacen__id=almacen_id, tipo=tipo_id).order_by('-fecha_alta')
            serializer = serializers.InspeccionListSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            mensaje = {'mensaje': 'No estás autorizado para consultar las inspecciones de esta sucursal.'}
            return Response(mensaje)

    else: 
        Response(status=status.HTTP_400_BAD_REQUEST)


"""
--------------------------------------------------------------------------
Despliega el detalle de una inspección

INPUTS: 
- ID de la Inspeccion deseada
--------------------------------------------------------------------------
"""
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def get_inspeccion(request, inspeccion_id):

    if request.method == 'GET':
        
        # Tomamos el usuario del request
        usuario = request.user
        # Tomamos todas las sucursales asignadas al usuario
        sucursales_usuario = usuario.sucursales.all()
        lista_sucursales = [sucursal.id for sucursal in sucursales_usuario]

        # Checamos que la inspección exista
        inspeccion_id = int(inspeccion_id)
        inspeccion = get_object_or_404(models.Inspeccion, id=inspeccion_id)

        """
        Si la inspección existe, tomamos el id de la sucursal
        a la que pertenece
        """
        if inspeccion:
            #print(' --- SÍ HAY INSPECCION ---')
            sucursal_id = inspeccion.sucursal.id

            """
            Si la sucursal de la inspección está en la lista de 
            sucursales autorizadas para el usuario, retornar los datos de la inspección
            """
            if sucursal_id in lista_sucursales:
                serializer = serializers.InspeccionDetalleSerializer(inspeccion)
                return Response(serializer.data)
            
            """
            Si la sucursal de la inspección no está en la lista de 
            sucursales autorizadas para el usuario, negar el acceso
            """
            
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Si la inspección no existe, mostrarmos un status 404
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)



"""
--------------------------------------------------------------------------
Despliega el detalle de una inspección
--------------------------------------------------------------------------
"""

class DetalleInspeccionView(viewsets.GenericViewSet, mixins.RetrieveModelMixin):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.InspeccionDetalleSerializer
    queryset = models.Inspeccion.objects.all()

    # def get_object(self):
    #     queryset = self.get_queryset()
    #     # Tomamos el usuario del request
    #     usuario = self.request.user
    #     # Tomamos todas las sucursales asignadas al usuario
    #     sucursales_usuario = usuario.sucursales.all()
    #     lista_sucursales = [sucursal.id for sucursal in sucursales_usuario]
    #     # Tomamos el id de la inspección del request
    #     #inspeccion_id = self.kwargs['inspeccion_id']
    #     inspeccion_id = self.request.query_params.get('inspeccion_id')
    #     # Tomamos la inspección. Si no existe, retornamos un 404
    #     inspeccion = get_object_or_404(queryset, id=inspeccion_id)

    #     """
    #     Si la inspección existe, tomamos el id de la sucursal
    #     a la que pertenece
    #     """
    #     if inspeccion:
    #         print(' --- SÍ HAY INSPECCION ---')
    #         sucursal_id = inspeccion.sucursal.id

    #         """
    #         Si la sucursal de la inspección no está en la lista de 
    #         sucursales autorizadas para el usuario, negar el acceso
    #         """
    #         if sucursal_id in lista_sucursales:
    #             return inspeccion
            
    #         else:
    #             return Response(status=status.HTTP_403_FORBIDDEN)

    #     # Si la inspección no existe, mostrarmos un status 404
    #     else:
    #         return inspeccion


"""
--------------------------------------------------------------------------
Despliega la vista de resumen de una inspeccion

Ejemplo:

LICOR (4)
- Licor 43 (3)
- Campari (1)

TEQUILA (2)
- Herradura Blanco (1)
- Don Julio Blanco (1)
--------------------------------------------------------------------------
"""
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def resumen_inspeccion(request, inspeccion_id):

    inspeccion_id = int(inspeccion_id)

    if request.method == 'GET':
        # Tomamos la Inspeccion a visualizar
        inspeccion_1 = models.Inspeccion.objects.get(id=inspeccion_id)

        #---------------------------------------------------------------
        # Definimos los querysets a utilizar
        #---------------------------------------------------------------

        # QUERYSET 1: Cantidad de items a inspeccionar por tipo de ingrediente
        queryset_1 = models.Ingrediente.objects.annotate(
            items_inspeccion=Subquery(models.ItemInspeccion.objects
                .filter(inspeccion=inspeccion_1, botella__producto__ingrediente=OuterRef('pk'))
                .values('botella__producto__ingrediente')
                .annotate(count=Count('botella__producto__ingrediente'))
                .values('count')
            )
        )

        # QUERYSET 2: Categorías que contienen items a inspeccionar
        queryset_2 = models.Categoria.objects.annotate(
            items_inspeccion=Exists(models.ItemInspeccion.objects
                .filter(inspeccion=inspeccion_1, botella__producto__ingrediente__categoria=OuterRef('pk'))
                .values('botella__producto__ingrediente__categoria')
                .annotate(count=Count('botella__producto__ingrediente__categoria'))
                .values('count')
            )
        ).filter(items_inspeccion=True)

        # QUERYSET 2A: Numero de items a inspeccionar por categoría
        queryset_2a = queryset_2.annotate(
            items_inspeccion=Subquery(models.ItemInspeccion.objects
                .filter(inspeccion=inspeccion_1, botella__producto__ingrediente__categoria=OuterRef('pk'))
                .values('botella__producto__ingrediente__categoria')
                .annotate(count=Count('botella__producto__ingrediente__categoria'))
                .values('count')
            )
        )

        #---------------------------------------------------------------
        # Construimos el JSON del response
        #---------------------------------------------------------------

        # Tomamos las categorías que contienen items a inspeccionar
        categorias = queryset_2a
        # Tomamos los ingredientes que contienen items a inspeccionar
        ingredientes = queryset_1 

        # Una lista donde guardaremos el output a renderearse por el Response
        resumen_inspeccion = []

        # Iteramos por el queryset de las categorias
        for categoria in categorias:
            # Creamos un objecto en donde guardaremos la categoría y sus items a inspeccionar
            obj = {}
            lista_ingredientes = []
            # Tomamos el nombre de la categoria
            nombre_categoria = categoria.nombre
            # Tomamos el total de items a inspeccionar de la categoria
            total_items_inspeccion = categoria.items_inspeccion
            # Guardamos las variables en un diccionario
            obj['categoria'] = nombre_categoria
            obj['total_botellas'] = total_items_inspeccion

            # Iteramos por el queryset de los ingredientes
            for ingrediente in ingredientes:
                obj_ingrediente = {}
                # Si la categoría del ingrediente es igual a la categoría del loop:
                if ingrediente.categoria.id == categoria.id:
                    # Tomamos el nombre del ingrediente y sus items inspeccion
                    nombre_ingrediente = ingrediente.nombre
                    cantidad = ingrediente.items_inspeccion
                    # Los guardamos en un diccionario
                    obj_ingrediente['ingrediente'] = nombre_ingrediente
                    obj_ingrediente['cantidad'] = cantidad
                    # Guardamos el diccionario en una lista de ingredientes
                    lista_ingredientes.append(obj_ingrediente)
            
            # Guardamos la lista de ingredientes en la categoría actual
            obj['botellas'] = lista_ingredientes
            # Guardamos el objecto en la lista del output del Response
            resumen_inspeccion.append(obj)
        
        #---------------------------------------------------------------
        # Construimos el Response
        #---------------------------------------------------------------

        return Response(resumen_inspeccion)

    else:
        Response(status=status.HTTP_400_BAD_REQUEST)


"""
--------------------------------------------------------------------------------
Muestra la cantidad de botellas contadas y no contadas de una Inspeccion

EJEMPLO:

- CONTADAS: 0
- NO CONTADAS: 40
--------------------------------------------------------------------------------
"""
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def resumen_botellas_conteo(request, inspeccion_id):

    if request.method == 'GET':

        # Tomamos el id de la Inspección del URL
        inspeccion_id = int(inspeccion_id) 

        #items_inspeccionar = models.ItemInspeccion.objects.filter(inspeccion__id=inspeccion_id).count()

        # QUERYSET 1: Botellas no contadas
        no_contados = models.ItemInspeccion.objects.filter(inspeccion__id=inspeccion_id, inspeccionado=False).count()
        # QUERYSET 2: Botellas contadas
        contados = models.ItemInspeccion.objects.filter(inspeccion__id=inspeccion_id, inspeccionado=True).count()

        # Creamos un objeto para guardar la cantidad de botellas contadas y no contadas
        resumen_botellas = {}

        # Guardamos la cantidad de botellas contadas y no contadas en el objecto
        resumen_botellas['botellas_contadas'] = contados
        resumen_botellas['botellas_no_contadas'] = no_contados

        # Creamos un response con la info
        return Response(resumen_botellas)

    else:
        Response(status=status.HTTP_400_BAD_REQUEST)


"""
--------------------------------------------------------------------------
Despliega la vista de resumen de una inspeccion (BOTELLAS NO CONTADAS)

Ejemplo:

LICOR (4)
- Licor 43 (3)
- Campari (1)

TEQUILA (2)
- Herradura Blanco (1)
- Don Julio Blanco (1)
--------------------------------------------------------------------------
"""
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def resumen_inspeccion_no_contado(request, inspeccion_id):

    inspeccion_id = int(inspeccion_id)

    if request.method == 'GET':
        # Tomamos la Inspeccion a visualizar
        inspeccion_1 = models.Inspeccion.objects.get(id=inspeccion_id)

        #---------------------------------------------------------------
        # Definimos los querysets a utilizar
        #---------------------------------------------------------------

        # QUERYSET: ItemsInspeccion que pertenecen a nuestra Inspeccion
        items = models.ItemInspeccion.objects.filter(inspeccion=inspeccion_1)

        # QUERYSET: ItemsInspeccion NO CONTADOS/NO INSPECCIONADOS (excluimos los CONTADOS)
        items = items.exclude(inspeccionado=True)

        # QUERYSET 1: Cantidad de items a inspeccionar por tipo de ingrediente
        queryset_1 = models.Ingrediente.objects.annotate(
            items_inspeccion=Subquery(items
                .filter(botella__producto__ingrediente=OuterRef('pk'))
                .values('botella__producto__ingrediente')
                .annotate(count=Count('botella__producto__ingrediente'))
                .values('count')
            )
        )

        # QUERYSET 2: Categorías que contienen items a inspeccionar
        queryset_2 = models.Categoria.objects.annotate(
            has_items_inspeccion=Exists(items
                .filter(botella__producto__ingrediente__categoria=OuterRef('pk'))
                .values('botella__producto__ingrediente__categoria')
                .annotate(count=Count('botella__producto__ingrediente__categoria'))
                .values('count')
            )
        ).filter(has_items_inspeccion=True)

        # QUERYSET 2A: Numero de items a inspeccionar por categoría
        queryset_2a = queryset_2.annotate(
            items_inspeccion=Subquery(items
                .filter(botella__producto__ingrediente__categoria=OuterRef('pk'))
                .values('botella__producto__ingrediente__categoria')
                .annotate(count=Count('botella__producto__ingrediente__categoria'))
                .values('count')
            )
        )

        #---------------------------------------------------------------
        # Construimos el JSON del response
        #---------------------------------------------------------------

        # Checamos que haya categorías con botellas pendientes de inspeccion
        if queryset_2.exists():

            # Tomamos las categorías que contienen items a inspeccionar
            categorias = queryset_2a
            # Tomamos los ingredientes que contienen items a inspeccionar
            ingredientes = queryset_1 

            # Una lista donde guardaremos el output que enviaremos en el Response
            resumen_inspeccion = []

            # Iteramos por el queryset de las categorias
            for categoria in categorias:
                # Creamos un objecto en donde guardaremos la categoría y sus items a inspeccionar
                obj = {}
                lista_ingredientes = []
                # Tomamos el nombre de la categoria
                nombre_categoria = categoria.nombre
                # Tomamos el total de items a inspeccionar de la categoria
                total_items_inspeccion = categoria.items_inspeccion
                # Guardamos las variables en un diccionario
                obj['categoria'] = nombre_categoria
                obj['total_botellas'] = total_items_inspeccion

                # Iteramos por el queryset de los ingredientes
                for ingrediente in ingredientes:
                    obj_ingrediente = {}
                    # Si la categoría del ingrediente es igual a la categoría del loop:
                    if ingrediente.categoria.id == categoria.id:
                        # Tomamos el nombre del ingrediente y sus items inspeccion
                        ingrediente_id = ingrediente.id
                        nombre_ingrediente = ingrediente.nombre
                        cantidad = ingrediente.items_inspeccion
                        # Los guardamos en un diccionario
                        obj_ingrediente['ingrediente_id'] = ingrediente_id
                        obj_ingrediente['ingrediente'] = nombre_ingrediente
                        obj_ingrediente['cantidad'] = cantidad
                        # Guardamos el diccionario en una lista de ingredientes
                        lista_ingredientes.append(obj_ingrediente)
                
                # Guardamos la lista de ingredientes en la categoría actual
                obj['botellas'] = lista_ingredientes
                # Guardamos el objecto en la lista del output del Response
                resumen_inspeccion.append(obj)
            
            #---------------------------------------------------------------
            # Construimos el Response
            #---------------------------------------------------------------

            return Response(resumen_inspeccion)
        
        # Si no hay botellas pendientes de inspección, enviamos un reponse con el mensaje
        else:
            return Response({'mensaje: No hay botellas pendientes de inspección.'})

    else:
        Response(status=status.HTTP_400_BAD_REQUEST)


"""
--------------------------------------------------------------------------
Despliega la vista de resumen de una inspeccion (BOTELLAS CONTADAS)

Ejemplo:

LICOR (4)
- Licor 43 (3)
- Campari (1)

TEQUILA (2)
- Herradura Blanco (1)
- Don Julio Blanco (1)
--------------------------------------------------------------------------
"""
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def resumen_inspeccion_contado(request, inspeccion_id):

    inspeccion_id = int(inspeccion_id)

    if request.method == 'GET':
        # Tomamos la Inspeccion a visualizar
        inspeccion_1 = models.Inspeccion.objects.get(id=inspeccion_id)

        #---------------------------------------------------------------
        # Definimos los querysets a utilizar
        #---------------------------------------------------------------

        # QUERYSET: ItemsInspeccion que pertenecen a nuestra Inspeccion
        items = models.ItemInspeccion.objects.filter(inspeccion=inspeccion_1)

        # QUERYSET: ItemsInspeccion CONTADOS/INSPECCIONADOS (excluimos los NO CONTADOS)
        items = items.exclude(inspeccionado=False)

        # QUERYSET 1: Cantidad de items a inspeccionar por tipo de ingrediente
        queryset_1 = models.Ingrediente.objects.annotate(
            items_inspeccion=Subquery(items
                .filter(botella__producto__ingrediente=OuterRef('pk'))
                .values('botella__producto__ingrediente')
                .annotate(count=Count('botella__producto__ingrediente'))
                .values('count')
            )
        )

        # QUERYSET 2: Categorías que contienen items a inspeccionar
        queryset_2 = models.Categoria.objects.annotate(
            has_items_inspeccion=Exists(items
                .filter(botella__producto__ingrediente__categoria=OuterRef('pk'))
                .values('botella__producto__ingrediente__categoria')
                .annotate(count=Count('botella__producto__ingrediente__categoria'))
                .values('count')
            )
        ).filter(has_items_inspeccion=True)

        # QUERYSET 2A: Numero de items a inspeccionar por categoría
        queryset_2a = queryset_2.annotate(
            items_inspeccion=Subquery(items
                .filter(botella__producto__ingrediente__categoria=OuterRef('pk'))
                .values('botella__producto__ingrediente__categoria')
                .annotate(count=Count('botella__producto__ingrediente__categoria'))
                .values('count')
            )
        )

        #---------------------------------------------------------------
        # Construimos el JSON del response
        #---------------------------------------------------------------

        # Checamos si existen categorías con ItemsInspeccion YA CONTADOS
        if queryset_2.exists():

            # Tomamos las categorías que contienen items a inspeccionar
            categorias = queryset_2a
            # Tomamos los ingredientes que contienen items a inspeccionar
            ingredientes = queryset_1 

            # Una lista donde guardaremos el output a renderearse por el Response
            resumen_inspeccion = []

            # Iteramos por el queryset de las categorias
            for categoria in categorias:
                # Creamos un objecto en donde guardaremos la categoría y sus items a inspeccionar
                obj = {}
                lista_ingredientes = []
                # Tomamos el nombre de la categoria
                nombre_categoria = categoria.nombre
                # Tomamos el total de items a inspeccionar de la categoria
                total_items_inspeccion = categoria.items_inspeccion
                # Guardamos las variables en un diccionario
                obj['categoria'] = nombre_categoria
                obj['total_botellas'] = total_items_inspeccion

                # Iteramos por el queryset de los ingredientes
                for ingrediente in ingredientes:
                    obj_ingrediente = {}
                    # Si la categoría del ingrediente es igual a la categoría del loop:
                    if ingrediente.categoria.id == categoria.id:
                        # Tomamos el nombre del ingrediente y sus items inspeccion
                        ingrediente_id = ingrediente.id
                        nombre_ingrediente = ingrediente.nombre
                        cantidad = ingrediente.items_inspeccion
                        # Los guardamos en un diccionario
                        obj_ingrediente['ingrediente'] = nombre_ingrediente
                        obj_ingrediente['ingrediente'] = nombre_ingrediente
                        obj_ingrediente['cantidad'] = cantidad
                        # Guardamos el diccionario en una lista de ingredientes
                        lista_ingredientes.append(obj_ingrediente)
                
                # Guardamos la lista de ingredientes en la categoría actual
                obj['botellas'] = lista_ingredientes
                # Guardamos el objecto en la lista del output del Response
                resumen_inspeccion.append(obj)
            
            #---------------------------------------------------------------
            # Construimos el Response
            #---------------------------------------------------------------

            return Response(resumen_inspeccion)

        # Si no hay categorías con ItemsInspeccion YA CONTADOS
        else: 
            return Response({'mensaje': 'Aún no hay botellas contadas.'})

    else:
        Response(status=status.HTTP_400_BAD_REQUEST)



"""
--------------------------------------------------------------------------
Endpoint que muestra las botellas de un ingrediente que están pendientes de
inspección.

Nota: La lista que muestra en realidad NO son botellas, sino ItemsInspeccion

EJEMPLO:

- LICOR 43 (Ii0000000001)
- LICOR 43 (Ii0000000002)
- LICOR 43 (Ii0000000003)

INPUTS:

- ID de Inspeccion
- ID de Ingrediente
--------------------------------------------------------------------------
"""
# class ListaBotellasNoContadasView(viewsets.GenericViewSet, mixins.ListModelMixin):

#     authentication_classes = (TokenAuthentication,)
#     permission_classes = (IsAuthenticated,)
#     serializer_class = serializers.ItemInspeccionDetalleSerializer

#     def get_queryset(self):
#         inspeccion_id = self.kwargs['inspeccion_id']
#         ingrediente_id = self.kwargs['ingrediente_id']
#         items_inspeccion = models.ItemInspeccion.objects.filter(inspeccion__id=inspeccion_id, botella__producto__ingrediente__id=ingrediente_id, inspeccionado=False)

#         return items_inspeccion


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def lista_botellas_no_contadas(request, inspeccion_id, ingrediente_id):

    if request.method == 'GET':

        inspeccion_id = int(inspeccion_id)
        ingrediente_id = int(ingrediente_id)

        queryset = models.ItemInspeccion.objects.filter(inspeccion__id=inspeccion_id, botella__producto__ingrediente__id=ingrediente_id, inspeccionado=False)
        serializer = serializers.ItemInspeccionDetalleSerializer(queryset, many=True)

        return Response(serializer.data)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------------------------------
Este endpoint hace lo mismo que el anterior, solo que muestra las botellas
ya inspeccionadas
-----------------------------------------------------------------------------
"""
@api_view(['GET'])
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def lista_botellas_contadas(request, inspeccion_id, ingrediente_id):

    if request.method == 'GET':

        inspeccion_id = int(inspeccion_id)
        ingrediente_id = int(ingrediente_id)

        queryset = models.ItemInspeccion.objects.filter(inspeccion__id=inspeccion_id, botella__producto__ingrediente__id=ingrediente_id, inspeccionado=True)

        serializer = serializers.ItemInspeccionDetalleSerializer(queryset, many=True)

        return Response(serializer.data)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------------------------------
Endpoint que muestra la ficha técnica de una botella y su historial
de inspecciones
-----------------------------------------------------------------------------
"""
# class InspeccionesBotellaViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):

#     authentication_classes = (TokenAuthentication,)
#     permission_classes = (IsAuthenticated,)
#     serializer_class = serializers.BotellaItemInspeccionSerializer
#     lookup_field = 'folio'

#     def get_queryset(self):
#         usuario = self.request.user
#         sucursales_usuario = usuario.sucursales.all()

#         almacenes_usuario = []
#         for sucursal in sucursales_usuario:
#             almacenes_sucursal = sucursal.almacenes.all()
#             almacenes_usuario.append(almacenes_sucursal)

#         botellas_almacenes = models.Botella.objects.filter(almacen__in=almacenes_usuario)

#         return botellas_almacenes

"""
-----------------------------------------------------------------------------
Endpoint que muestra la ficha técnica de una botella y su historial
de inspecciones

(Igual que el anterior pero en formato de función)
-----------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def lista_inspecciones_botella(request, folio_id):

    if request.method == 'GET':

        botella = get_object_or_404(models.Botella, folio=folio_id)
        serializer = serializers.BotellaItemInspeccionSerializer(botella)
        return Response(serializer.data)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------------------------------
Endpoint que muestra el detalle de una botella cuando se escanea con la app
durante una Inspeccion.

Nota:
Si el folio de la botella no está asociado a ningún ItemInspeccion de la
Inspección en curso, se notifica que la botella no es parte de la Inpección.
-----------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def detalle_botella_inspeccion(request, inspeccion_id, folio_id):

    if request.method == 'GET':

        inspeccion_id = int(inspeccion_id)

        # Checamos que la botella escaneada pertenezca a la Inspección en curso
        if models.ItemInspeccion.objects.filter(inspeccion__id=inspeccion_id, botella__folio=folio_id).exists():
            item_inspeccion = models.ItemInspeccion.objects.get(inspeccion__id=inspeccion_id, botella__folio=folio_id)
             
            # Si la botella escaneada no ha sido inspeccionada, mostramos su ficha técnica
            if item_inspeccion.inspeccionado == False:
                serializer = serializers.ItemInspeccionDetalleSerializer(item_inspeccion)
                return Response(serializer.data)
            
            # Si la botella ya fue inspecionada, notificamos al usuario
            else:
                return Response({'mensaje': 'Esta botella ya fue inspeccionada.'})

        # Si la botella no pertenece a la Inspección en curso, notificamos al usuario
        else:
            return Response({'mensaje': 'Esta botella no es parte de la inspección.'})



"""
-----------------------------------------------------------------------------
Endpoint que muestra la lista de sucursales del Cliente. El usuario solamente
puede accesar a aquellas sucursales que tiene asignadas.
-----------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def lista_sucursales(request):

    if request.method == 'GET':

        # Tomamos la lista de sucursales asignadas al usuario
        sucursales_usuario = request.user.sucursales.all()
        # Serializamos la lista de sucursales
        serializer = serializers.SucursalSerializer(sucursales_usuario, many=True)
        # Creamos el response con al lista de sucursales
        return Response(serializer.data)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------------------------------
Endpoint que muestra la lista de Sucursales y Almacenes de un cliente.
El usuario solamente puede accesar a aquellas sucursales que tiene asignadas.
-----------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def lista_sucursales_almacenes(request):

    if request.method == 'GET':

        # Tomamos la lista de sucursales asignadas al usuario
        sucursales_usuario = request.user.sucursales.all()
        # Serializamos la lista de sucursales
        serializer = serializers.SucursalDetalleSerializer(sucursales_usuario, many=True)
        # Creamos el response con al lista de sucursales
        return Response(serializer.data)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)



"""
-----------------------------------------------------------------------------
Endpoint que actualiza el peso de una botella cuando se inspecciona
----------------------------------------------------------------------------- 
"""
@api_view(['PATCH'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def update_peso_botella(request):

    if request.method == 'PATCH':
        
        # Tomamos las variables del request
        item_inspeccion_id =  request.data['item_inspeccion']
        peso_botella = request.data['peso_botella']
        estado_botella = request.data['estado']

        # Creamos el payload del request
        payload = {
            'peso_botella': peso_botella,
            'inspeccionado': True,
            'botella': {'estado': estado_botella}
        }

        # Tomamos el ItemInspeccion que deseamos actualizar
        item = models.ItemInspeccion.objects.get(id=item_inspeccion_id)
        # Deserializamos los datos para actualizar nuestro ItemInspeccion
        serializer = serializers.ItemInspeccionUpdateSerializer2(item, data=payload, partial=True)

        if serializer.is_valid():
            # Actualizamos los datos de nuestro ItemInspeccion
            serializer.save()
            # Creamos el response
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            # Si hay un error con los datos, lo notificamos
            Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Si el request no es PATCH, notificamos error
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------------------------------
Endpoint que modifica el estado de una Inspeccion a 'CERRADA'
-----------------------------------------------------------------------------
"""
@api_view(['PATCH'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def cerrar_inspeccion(request):

    if request.method == 'PATCH':

        # Tomamos el id de la Inspección del request
        inspeccion_id = request.data['inspeccion']
        # Tomamos el usuario del request
        usuario_cierre = request.user
        # Tomamos la Inspeccion a modificar
        inspeccion = models.Inspeccion.objects.get(id=inspeccion_id)

        # Deserializamos los datos
        payload = {
            'estado': '1',
            'usuario_cierre': usuario_cierre.id,
        }
        serializer = serializers.InspeccionUpdateSerializer(inspeccion, data=payload, partial=True)

        # Verificamos que los datos a deserializar sean válidos
        if serializer.is_valid():
            # Actualizamos los datos de nuestro ItemInspeccion
            serializer.save()
            # Creamos el response
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            # Si hay un error con los datos, lo notificamos
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Si el request no es PATCH, notificamos error
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    


"""
-----------------------------------------------------------------------------------
Endpoint que modifica el estado de una botella inspeccionada a 'VACIA' o 'NUEVA' y
modifica su peso ad hoc
-----------------------------------------------------------------------------------
"""
@api_view(['PATCH'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def update_botella_nueva_vacia(request):

    if request.method == 'PATCH':

        # Tomamos las variables del request
        item_inspeccion_id =  request.data['item_inspeccion']
        estado_botella = request.data['estado']

        # Tomamos el ItemInspeccion que deseamos actualizar
        item = models.ItemInspeccion.objects.get(id=item_inspeccion_id)

        # Tomamos la Botella asociada al ItemInspeccion
        botella = item.botella
        # Tomamos el Producto asociado a la Botella
        producto = botella.producto
        # Tomamos el Ingrediente asociado a la Botella y el Producto
        ingrediente = producto.ingrediente

        # Si queremos declarar la botella como VACIA
        if estado_botella == '0':
            # Calculamos el peso de la botella vacía
            peso_botella = producto.peso_cristal
        # Si queremos declarar la botella como NUEVA
        elif estado_botella == '2':
            # Calculamos el peso de la botella nueva
            peso_botella = producto.peso_cristal + int(round(producto.capacidad * ingrediente.factor_peso))

       # Creamos el payload para el serializer
        payload = {
            'peso_botella': peso_botella,
            'inspeccionado': True,
            'botella': {'estado': estado_botella}
        }

        # Deserializamos el payload
        serializer = serializers.ItemInspeccionBotellaUpdateSerializer(item, data=payload, partial=True)
        # Verificamos que los datos a deserializar sean válidos
        if serializer.is_valid():
            # Actualizamos los datos de nuestro ItemInspeccion
            serializer.save()
            # Creamos el response
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        else:
            # Si hay un error con los datos, lo notificamos
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Si el request no es PATCH, notificamos error
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)    


"""
-----------------------------------------------------------------------------------
Endpoint que toma los datos del marbete del SAT

NOTAS:
- Utiliza el scrapper
- Despliega los datos del marbete, pero no registra la botella
- Si el marbete no especifica el ingrediente, el response lo deja en blanco

-----------------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def get_marbete_sat(request, folio_id):

    """
    -------------------------------------------------------------------------
    Esta función toma los primeros 7 dígitos del folio y busca Productos
    que hagan match
    -------------------------------------------------------------------------
    """
    def search_patron_folio(folio):
        # Tomamos los primeros 7 dígitos del folio
        patron = folio[0:6]
        # Checamos si hay Productos con folios que hagan match con el patrón
        try:
            productos = models.Producto.objects.filter(folio__istartswith=patron)
            # Tomamos le Producto con la fecha de registro más reciente
            producto = productos.latest('fecha_registro')
            # Retornamos el Producto
            return producto

        except ObjectDoesNotExist:
            # Si no hay Productos que hagan match con el patrón, retornamos None
            return None

    """
    -------------------------------------------------------------------------
    Esta función toma el 'NOMBRE DE MARCA' del marbete y busca Productos en
    la base de datos que hagan match
    -------------------------------------------------------------------------
    """
    def search_nombre_marca(nombre_marca):
        # Checamos si hay Productos que hagan match con el nombre de marca
        try:
            productos = models.Producto.objects.filter(nombre_marca__iexact=nombre_marca)
            # Tomamos le Producto con la fecha de registro más reciente
            producto = productos.latest('fecha_registro')
            return producto

        except ObjectDoesNotExist:
            # Si no hay Productos que hagan match con el patrón, retornamos None
            return None

    #--------------------------------------------------------------------------------
    #--------------------------------------------------------------------------------
    #--------------------------------------------------------------------------------


    if request.method == 'GET':
        
        # Tomamos las variables del request
        folio = folio_id
        #almacen_id = request.data['almacen']11

        # Obtenemos los datos del marbete del SAT usando el scrapper
        #data_marbete = scrapper.get_data_sat(folio)
        #folio_sat = data_marbete['folio']
        
        # Checamos si la botella ya está registrada en la base de datos
        try: 
            botella = models.Botella.objects.get(folio=folio)
            #botella = models.Botella.objects.get(folio=folio_sat)
            mensaje = {'mensaje': 'Esta botella ya es parte del inventario.'}
            return Response(mensaje)

        # Si la botella no está registrada, OK y continuamos
        except ObjectDoesNotExist:
            # Obtenemos los datos del marbete del SAT usando el scrapper
            data_marbete = scrapper.get_data_sat(folio)

            # Si el scrapper tuvo problemas para conectarse al SAT, notificamos error.
            if data_marbete['status'] == '0':
                mensaje = {'mensaje': 'Hubo problemas al conectarse con el SAT. Intente de nuevo más tarde.'}
                return Response(mensaje) 

            # Si no hubo probelmas para conectarse con el SAT, continuamos:
            folio_sat = data_marbete['marbete']['folio']

            # Checamos si hay Productos registrados que hagan match con el patrón del folio
            producto_folio = search_patron_folio(folio_sat)

            """
            Si existe un match de Producto (patrón de folio):
            - Construimos un objecto con los datos del marbete y el Producto (incluyendo su Ingrediente asociado)
            """
            if producto_folio is not None:
                # Construimos un diccionario con los datos del marbete
                serializer = serializers.ProductoIngredienteSerializer(producto_folio)
                # Construimos un objecto con los datos del marbete y el Producto
                output = {
                    'data_marbete': data_marbete['marbete'],
                    'producto': serializer.data
                }
                # Retornamos el output
                return Response(output)

            """
            Si no existe un match de Producto (patrón de folio):
            - Checamos si existe un match con el patrón de nombre
            """
            #else:
            producto_nombre_marca = search_nombre_marca(data_marbete['marbete']['nombre_marca'])
            # Si existe un match, retornamos un objecto con los datos del marbete y el Producto
            if producto_nombre_marca is not None:
                serializer = serializers.ProductoIngredienteSerializer(producto_nombre_marca)
                output = {
                    'data_marbete': data_marbete['marbete'],
                    'producto': serializer.data
                }
                return Response(output)

            # Si no existe un match, retornamos los datos del marbete disponibles y el Producto en blanco
            # else:
            #     output = {
            #         'data_marbete': data_marbete['marbete'],
            #         'producto': None
            #     }
            #     return Response(output)

            """
            Si no existe un match de nombre, retornamos una advertencia y le pedimos
            al usuario que nos contacte para registrar la botella
            """
            #else:
            mensaje = {'mensaje': 'No se pudo identificar el producto.'}
            return Response(mensaje)



    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)



"""
-----------------------------------------------------------------------------------
Endpoint que muestra la lista de Categorías de destilados disponibles
-----------------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def get_categorias(request):

    if request.method == 'GET':
        # Tomamos todas las categorías
        queryset = models.Categoria.objects.all()
        # Serializamos las categorías
        serializer = serializers.CategoriaSerializer(queryset, many=True)
        # Retornamos las categorías serializadas
        return Response(serializer.data)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------------------------------------
Endpoint que muestra la lista de Ingredientes de una Categoría específica
-----------------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def get_ingredientes_categoria(request, categoria_id):

    if request.method == 'GET':

        # Tomamos el id de la Categoria
        categoria_id = int(categoria_id)
        # Tomamos la categoría con el id especificado
        categoria = models.Categoria.objects.get(id=categoria_id)
        # Tomamos todos los ingredientes de la categoría
        #ingredientes_categoria = categoria.ingredientes.all()
        # serializamos los ingredientes
        serializer = serializers.CategoriaIngredientesSerializer(categoria)
        # Retornamos la categoría serializada con sus ingredientes asociados
        return Response(serializer.data)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)
        


"""
-----------------------------------------------------------------------------------
Endpoint para crear una Botella nueva, especificando su Producto asociado en el request
-----------------------------------------------------------------------------------
"""
@api_view(['POST'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def crear_botella(request):

    if request.method == 'POST':

        payload = {}
        # Tomamos los datos de la Botella del request
        payload['folio'] = request.data['folio'] # REQUERIDO
        payload['tipo_marbete'] = request.data['tipo_marbete'] 
        payload['fecha_elaboracion_marbete'] = request.data['fecha_elaboracion_marbete']
        payload['lote_produccion_marbete'] = request.data['lote_produccion_marbete']
        payload['url'] = request.data['url']

        #payload['producto'] = request.data['producto'] # REQUERIDO

        payload['nombre_marca'] = request.data['nombre_marca']
        payload['tipo_producto'] = request.data['tipo_producto']
        payload['graduacion_alcoholica'] = request.data['graduacion_alcoholica']
        payload['capacidad'] = request.data['capacidad']
        payload['origen_del_producto'] = request.data['origen_del_producto']
        payload['fecha_importacion'] = request.data['fecha_importacion']
        payload['nombre_fabricante'] = request.data['nombre_fabricante']
        payload['rfc_fabricante'] = request.data['rfc_fabricante']

        # DATOS QUE NO SON PARTE DEL MARBETE
        payload['producto'] = request.data['producto'] # REQUERIDO
        payload['usuario_alta'] = request.user.id
        payload['sucursal'] = request.data['sucursal'] # REQUERIDO
        payload['almacen'] = request.data['almacen'] # REQUERIDO
        payload['proveedor'] = request.data['proveedor'] # REQUERIDO

        payload['peso_inicial'] = request.data['peso_inicial'] # REQUERIDO

        serializer = serializers.BotellaPostSerializer(data=payload)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)



"""
-----------------------------------------------------------------------------------
Endpoint que toma los datos del marbete del SAT y los muestra antes de registrar un Producto

NOTAS:
- Utiliza el scrapper
- Despliega los datos del marbete del SAT, pero no registra el Producto
- Los campos de ingrediente, peso_cristal y precio_unitario los deja en blanco

-----------------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def get_marbete_sat_producto(request, folio_id):

    if request.method == 'GET':

        folio = folio_id
        # Ejecutamos el scrapper y tomamos los datos del marbete
        data_marbete = scrapper.get_data_sat(folio)

        # Si el scrapper tuvo problemas con el SAT, notificar error
        if data_marbete['status'] == '0':
            mensaje = {'mensaje': 'Hubo un error al conectarse con el SAT. Intente de nuevo más tarde.'}
            return Response(mensaje)

        # Si el scrapper funcionó OK, retornamos los datos del marbete
        else:
            return Response(data_marbete)



"""
-----------------------------------------------------------------------------------
Endpoint para crear y actualizar Productos

- Los campos de 'peso_cristal', 'precio_unitario' e 'ingrediente' son requeridos
-----------------------------------------------------------------------------------
"""
class ProductoViewSet(viewsets.ModelViewSet):

    serializer_class = serializers.ProductoWriteSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = models.Producto.objects.all()



"""
------------------------------------------------------------------------------------------------------
Endpoint para crear una nueva Inspeccion Diaria o Total (inspeccionar todas las botellas del almacén)

- Total: Todas las botellas del inventario
- Diaria: Solo aquellas botellas con ingredientes vendidos

::: INPUTS ::::

Un payload con las variables:

- almacen: el ID del almacen (integer)
- sucursal: el ID de la sucursal (integer)
- tipo_inspeccion:
    -- 'TOTAL' para crear una inspección de todas las botellas del inventario
    -- 'DIARIA' para crear una inspección con solo las botellas de ingredientes vendidos 

------------------------------------------------------------------------------------------------------
"""
class InspeccionTotalViewSet(viewsets.ModelViewSet):

    serializer_class = serializers.InspeccionPostSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    #queryset = models.Inspeccion.objects.all()

    def get_queryset(self):
        sucursal_id = self.request.data['sucursal']
        almacen_id = self.request.data['almacen']
        usuario = self.request.user
        sucursales_usuario = usuario.sucursales.all()
        lista_sucursales = [sucursal.id for sucursal in sucursales_usuario]

        if sucursal_id in lista_sucursales:
            inspecciones = models.Inspeccion.objects.filter(sucursal__id=sucursal_id, almacen__id=almacen_id)
            return inspecciones

        else:
            queryset = models.Inspeccion.objects.none()
            return queryset


    #----------------------------------------------------------------------------------
    def checar_ultima_inspeccion(self):
        """
        Esta función retorna los datos de la última inspección realizada en la sucursal y almacén
        del request
        """

        sucursal_id = self.request.data['sucursal']
        almacen_id = self.request.data['almacen']

        # Si existe al menos una inspección registrada en la base de datos, tomamos su fecha y estado
        if models.Inspeccion.objects.filter(sucursal__id=sucursal_id, almacen__id=almacen_id).exists():
            ultima_inspeccion = models.Inspeccion.objects.filter(sucursal__id=sucursal_id, almacen__id=almacen_id).latest('fecha_alta')
            fecha_ultima_inspeccion = ultima_inspeccion.fecha_alta
            estado_ultima_inspeccion = ultima_inspeccion.estado

            return {
                        'sucursal_id': sucursal_id,
                        'almacen_id': almacen_id,
                        'fecha': fecha_ultima_inspeccion,
                        'estado': estado_ultima_inspeccion
                    }
        
        return None

    
    #----------------------------------------------------------------------------------
    def get_ultimos_consumos(self):
        """
        Retorna un queryset con los últimos consumos registrados en la sucursal y almacén del request
        """

        info_ultima_inspeccion = self.checar_ultima_inspeccion()

        # Si existe una inspección previa
        if info_ultima_inspeccion is not None:

            fecha_ultima_inspeccion = info_ultima_inspeccion['fecha']
            sucursal_id = info_ultima_inspeccion['sucursal_id']
            almacen_id = info_ultima_inspeccion['almacen_id']

            # Checamos si hay consumos registrados después de la última inspección
            try:
                models.ConsumoRecetaVendida.objects.filter(
                    venta__caja__almacen__id=almacen_id,
                    fecha__gte=fecha_ultima_inspeccion
                )

            except ObjectDoesNotExist:
                return None

            else:
                ultimos_consumos = models.ConsumoRecetaVendida.objects.filter(
                    venta__caja__almacen__id=almacen_id,
                    fecha__gte=fecha_ultima_inspeccion
                )

                return ultimos_consumos

        """
        Si no hay inspecciones previas registradas, retornamos todos los consumos registrados
        para el almacén del request. Significa que apenas se va a realizar la primera inspección ever.
        """
        try:
            almacen_id = self.request.data['almacen']
            models.ConsumoRecetaVendida.objects.filter(venta__caja__almacen__id=almacen_id)

        # Si no hay consumos registrados, entonces retornamos None
        except ObjectDoesNotExist:
            return None

        else:
            ultimos_consumos = models.ConsumoRecetaVendida.objects.filter(venta__caja__almacen__id=almacen_id)

            return ultimos_consumos 

    #----------------------------------------------------------------------------------
    def get_botellas_inspeccionar(self):
        """
        Esta función construye una lista con todas las botellas a inspeccionar
        en en el almacén especificado
        """
        sucursal_id = self.request.data['sucursal']
        almacen_id = self.request.data['almacen']
        tipo_inspeccion = self.request.data['tipo_inspeccion']

        """
        Si el tipo de inspección solicitada es 'TOTAL', retornamos todas las botellas del almacén:
        """
        if tipo_inspeccion == 'TOTAL':
            
            # Checamos si hay botellas registradas en el almacén
            try:

                botellas = models.Botella.objects.filter(almacen__id=almacen_id)
                botellas = botellas.exclude(estado='0')
                botellas = botellas.exclude(estado='3')
                return botellas

            # Si no hay botellas registradas en el almacén, no retornamos ninguna botella
            except ObjectDoesNotExist:
                return None

        """
        Si el tipo de inspección solicitada es 'DIARIA', retornamos solo las botellas de ingredientes vendidos
        """
        #else:

        # Tomamos los consumos registrados después de la última inspección
        ultimos_consumos = self.get_ultimos_consumos()

        # Si hay consumos registrados después de la última inspección:
        if ultimos_consumos is not None:
            # Tomamos los ingredientes de dichos consumos y los guardamos en una lista
            lista_ingredientes = [consumo.ingrediente for consumo in ultimos_consumos]
            # Creamos un set con ingredientes únicos
            ingredientes_unicos = set(lista_ingredientes)

            # Tomamos las botellas del almacén que contengan los ingredientes consumidos
            botellas = []
            for ingrediente in ingredientes_unicos:
                # Seleccionamos las botellas del ingrediente en cuestión
                qs_botellas_ingrediente = models.Botella.objects.filter(sucursal__id=sucursal_id, almacen__id=almacen_id, producto__ingrediente__id=ingrediente.id)
                # Excluimos las botellas VACIAS
                qs_botellas_ingrediente = qs_botellas_ingrediente.exclude(estado='0')
                # Excluimos las botellas PERDIDAS
                qs_botellas_ingrediente = qs_botellas_ingrediente.exclude(estado='3')
                # Guardamos las botellas del ingrediente en una lista
                botellas_ingrediente = [botella for botella in qs_botellas_ingrediente]
                # Agregamos las botellas a la lista maestra de botellas
                botellas += botellas_ingrediente

            return botellas

        # Si no hay consumos registrados, no retornamos ninguna botella (no hay nada que inspeccionar)
        return None

    #----------------------------------------------------------------------------------
    def get_serializer_context(self):
        """
        Información incluida en el contexto para el serializador:

        - Lista de botellas a inspeccionar
        - Fecha de la última inspección
        - Estado de la última inspección

        """
        # Checamos si hay una inspección previa
        info_ultima_inspeccion = self.checar_ultima_inspeccion()

        """
        Si existe una inspección previa, tomamos sus datos, las botellas y el usuario 
        del request y guardamos todo en el contexto (para el serializador)
        """        
        if info_ultima_inspeccion is not None:
            context = super(InspeccionTotalViewSet, self).get_serializer_context()
            fecha_ultima_inspeccion = info_ultima_inspeccion['fecha']
            estado_ultima_inspeccion = info_ultima_inspeccion['estado']
            botellas = self.get_botellas_inspeccionar()
            #usuario_actual = self.request.user
            context.update(
                {
                    'lista_botellas_inspeccionar': botellas,
                    'fecha_ultima_inspeccion': fecha_ultima_inspeccion,
                    'estado_ultima_inspeccion': estado_ultima_inspeccion,
                    #'usuario': usuario_actual
                }
            )

            return context

        """ Si no hay inspecciones previas, agregamos al contexto la lista de botellas y el usuario del request """
        botellas = self.get_botellas_inspeccionar()
        #usuario_actual = self.request.user
        context = super(InspeccionTotalViewSet, self).get_serializer_context()
        context.update(
            {
                'fecha_ultima_inspeccion': None,
                'lista_botellas_inspeccionar': botellas,
                #'usuario': usuario_actual
            }
        )

        return context

    #----------------------------------------------------------------------------------
    def perform_create(self, serializer):
        #serializer.save(usuario_alta=self.request.user)

        tipo_inspeccion = self.request.data['tipo_inspeccion']

        if tipo_inspeccion == 'DIARIA':
            serializer.save(usuario_alta=self.request.user, tipo='0')

        else:
            serializer.save(usuario_alta=self.request.user, tipo='1')




"""
-----------------------------------------------------------------------------------
Endpoint para consultar el detalle de una Botella del inventario
-----------------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def consultar_botella(request, folio_id):

    if request.method == 'GET':

        folio = folio_id

        # Checamos que el folio esté registrado en la base de datos
        try:
            botella = models.Botella.objects.get(folio=folio)

        except ObjectDoesNotExist:
            mensaje = {'mensaje': 'Esta botella no está registrada en el inventario.'}
            return Response(mensaje)

        else:
            botella = models.Botella.objects.get(folio=folio)

            # Serializamos la botella
            serializer = serializers.BotellaConsultaSerializer(botella)
            return Response(serializer.data)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------------------------------------
Endpoint para crear un Traspaso
-----------------------------------------------------------------------------------
"""
@api_view(['POST'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def crear_traspaso(request):

    if request.method == 'POST':

        # Tomamos las variables requeridas del request
        folio_id = request.data['folio']
        almacen_id = request.data['almacen']

        # Construimos los parametros extras
        almacen = models.Almacen.objects.get(id=almacen_id)
        sucursal_id = almacen.sucursal.id

        # Checamos que el folio esté registrado en la base de datos
        try:
            botella = models.Botella.objects.get(folio=folio_id)

        except ObjectDoesNotExist:
            mensaje = {'mensaje': 'No se puede hacer el traspaso porque la botella no está registrada.'}
            return Response(mensaje)

        else: 
            botella = models.Botella.objects.get(folio=folio_id)
            botella_id = botella.id
            #print('::: ALMACEN ID :::')
            #print(botella.almacen.id)
            #usuario_id = request.user.id

            # Checamos que el estado de la botella no sea VACIA ni PERDIDA
            if botella.estado == '0':
                mensaje = {'mensaje': 'Esta botella está registrada como VACIA.'}
                return Response(mensaje)

            elif botella.estado == '3':
                mensaje = {'mensaje': 'Esta botella está registrada como PERDIDA.'}
                return Response(mensaje)

            # Checamos que la botella no sea parte del almacén al que se quiere traspasar
            elif botella.almacen.id == almacen.id:
                #print('::: ALMACEN ID :::')
                #print(botella.almacen.id)
                mensaje = {'mensaje': 'Esta botella ya es parte de este almacén.'}
                return Response(mensaje)

            else:
                # Construimos el payload para el serializer
                payload = {
                    'almacen': almacen_id,
                    'sucursal': sucursal_id,
                    'botella': botella_id,
                    #'usuario': usuario_id
                }

                # deserializamos el payload
                serializer = serializers.TraspasoWriteSerializer(data=payload)

                # Validamos el payload y guardamos el nuevo Traspaso en la base de datos
                if serializer.is_valid():
                    #print('::: VALIDATED DATA :::')
                    #print(serializer.validated_data)
                    #print('::: SERIALIZER ERRORS :::')
                    #print(serializer.errors)
                    serializer.save(usuario=request.user)

                return Response(serializer.data, status=status.HTTP_201_CREATED)


    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------------------------------------
Endpoint para crear un Ingrediente
-----------------------------------------------------------------------------------
"""
@api_view(['POST'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def crear_ingrediente(request):

    if request.method == 'POST':

        codigo = request.data['codigo']
        nombre = request.data['nombre']
        categoria = request.data['categoria']
        factor_peso = request.data['factor_peso']

        # Deserializamos los datos y guardamos el Ingrediente en la base de datos
        payload = {
            'codigo': codigo,
            'nombre': nombre,
            'categoria': categoria,
            'factor_peso': factor_peso
        }

        serializer = serializers.IngredienteWriteSerializer(data=payload)
        if serializer.is_valid():
            serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

        
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------------------------------------
Endpoint para desplegar la lista de proveedores
-----------------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def get_proveedores(request):

    if request.method == 'GET':

        queryset = models.Proveedor.objects.all()
        serializer = serializers.ProveedorSerializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)


"""
-----------------------------------------------------------------------------------
Endpoint que despliega la lista de SERVICIOS disponibles para el usuario
-----------------------------------------------------------------------------------
"""
@api_view(['GET'],)
@permission_classes((IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def get_servicios_usuario(request):

    if request.method == 'GET':

        usuario = request.user
        servicios_superuser = {
            'Movimientos': ['Alta Botella', 'Traspaso Botella', 'Baja Botella'],
            'Inspecciones': ['Inventario Total', 'Inventario Rápido'],
            'Consultas': ['Inventario', 'Botella'],
            'Ingrediente Nuevo': 'Ingrediente Nuevo',
            'Producto Nuevo': 'Producto Nuevo'        
        }
        servicios_user = {
            'Movimientos': ['Alta Botella', 'Traspaso Botella'],
            'Inspecciones': ['Inventario Total', 'Inventario Rápido'],
            'Consultas': ['Inventario', 'Botella']   
        }
        
        if usuario.is_superuser:
            return Response(servicios_superuser, status=status.HTTP_200_OK)

        else:
            return Response(servicios_user, status=status.HTTP_200_OK)

    else:
        return Response(status=status.HTTP_400_BAD_REQUEST)

