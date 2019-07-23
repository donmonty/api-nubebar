from django.contrib.auth import get_user_model
from rest_framework import serializers
from core import models
import datetime
from django.utils.timezone import make_aware


class ItemInspeccionPostSerializer(serializers.ModelSerializer):
    """ Serializador para crear los ItemInspeccion de una Inspeccion """

    #botella = serializers.PrimaryKeyRelatedField(read_only=False, queryset=models.Botella.objects.all())
    botella = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.ItemInspeccion
        fields = ('botella', 'peso_botella')
        #exclude = ('inspeccion',)


class InspeccionPostSerializer(serializers.ModelSerializer):
    """ Crea una Inspeccion """

    #items_inspeccionados = ItemInspeccionPostSerializer(many=True)
    #items_inspeccionados = ItemInspeccionPostSerializer(many=True, read_only=True)
    almacen = serializers.PrimaryKeyRelatedField(read_only=False, queryset=models.Almacen.objects.all())
    sucursal = serializers.PrimaryKeyRelatedField(read_only=False, queryset=models.Sucursal.objects.all())
    #usuario_alta = serializers.PrimaryKeyRelatedField(read_only=False, queryset=get_user_model().objects.all())

    class Meta:
        model = models.Inspeccion
        fields = (
            'id',
            'almacen',
            'sucursal',
            #'usuario_alta',
            'fecha_alta',
            'timestamp_alta',
            'estado',
            #'items_inspeccionados'
        )

    def create(self, validated_data):

        """
        :::: IMPORTANTE ::::
        Antes que nada checamos que haya botellas para inpseccionar. Esto
        significa que SI hubo consumo de alcohol.
        Si no hubo consumo, no hay botellas para inspeccionar y no hacemos ninguna
        inspección, sin importar cualquier cosa.
        """
        botellas = self.context['lista_botellas_inspeccionar']
        if botellas is not None:

            """
            Si existe una inspección previa registrada
            """
            # Checamos si existe una inspección previa registrada
            if self.context['fecha_ultima_inspeccion'] is not None:
                # Tomamos la información extra del contexto
                fecha_hoy = datetime.date.today()
                #print('::: FECHA DE HOY ::::')
                #print(fecha_hoy)
                estado_ultima_inspeccion = self.context['estado_ultima_inspeccion']
                fecha_ultima_inspeccion = self.context['fecha_ultima_inspeccion']
                botellas = self.context['lista_botellas_inspeccionar']
                #usuario = self.context['usuario']
                #print('::: ESTADO INSPECCION ANTERIOR :::')
                #print(estado_ultima_inspeccion)
                #print('::: FECHA INSPECCION ANTERIOR :::')
                #print(fecha_ultima_inspeccion)
                #print('::: FECHA HOY > FECHA ANTERIOR? :::')
                #print(fecha_hoy > fecha_ultima_inspeccion)
                #print('::: USUARIO INSPECCION PREVIA :::')
                #print(usuario)
                #print('::: LISTA DE BOTELLAS :::')
                #print(botellas)

                """
                SI la inspección previa está cerrada y la fecha de hoy es mayor que 
                que la fecha de ésta, creamos una nueva inspección.
                """
                if (estado_ultima_inspeccion == '1') and (fecha_hoy > fecha_ultima_inspeccion):
                    #inspeccion = models.Inspeccion.objects.create(usuario_alta=usuario, **validated_data)
                    inspeccion = models.Inspeccion.objects.create(**validated_data)
                    #print('::: CREAMOS UNA INSPECCION :::')
                    #print(inspeccion)

                    #print('::: LISTA DE BOTELLAS :::')
                    #print(botellas)

                    # Creamos los ItemInspeccion
                    for botella in botellas:
                        # Tomamos el id de la botella
                        botella_id = botella.id
                        # Creamos el ItemInspeccion
                        ii = models.ItemInspeccion.objects.create(inspeccion=inspeccion, botella=botella)
                        #print('::: ITEM INSPECCION :::')
                        #print(ii)

                    #print(inspeccion.items_inspeccionados.all())
                    #print(inspeccion.items_inspeccionados.count())

                    return inspeccion

                # Si la fecha de hoy es igual o menor que la de la inspección previa, marcar error
                elif estado_ultima_inspeccion == '1' and fecha_hoy <= fecha_ultima_inspeccion:
                    raise serializers.ValidationError('Solo es posible realizar una inspección al día.')

                # Si la inspección previa está abierta, marcar error
                elif estado_ultima_inspeccion == '0':
                    raise serializers.ValidationError('No es posible hacer una nueva inspección si la anterior no se ha cerrado')

            """
            SI no hay inspecciones registradas, creamos una nueva inspección
            (creamos la primera inspección ever)
            """
        
            inspeccion = models.Inspeccion.objects.create(**validated_data)
            #print('::: NO HAY INSPECCIONES REGISTRADAS :::')
            #print(inspeccion)
            # Tomamos la información extra del contexto
            botellas = self.context['lista_botellas_inspeccionar']
            #usuario = self.context['usuario']

            #print('::: LISTA DE BOTELLAS (no hay inspecciones previas) :::')
            #print(botellas)


            # Creamos los ItemInspeccion
            for botella in botellas:
                botella_id = botella.id
                models.ItemInspeccion.objects.create(inspeccion=inspeccion, botella=botella)

            return inspeccion

        """
        Si no hay botellas que inspeccionar, NO hacemos ninguna inspección
        """
        #print('::: NO HAY BOTELLAS QUE INSPECCIONAR :::')
        raise serializers.ValidationError('No se puede crear una nueva inspección porque no hubo consumo de alcohol.')



#-----------------------------------------------------------------

class InspeccionListSerializer(serializers.ModelSerializer):
    """ 
    Arroja la lista de Inspecciones de un almacén
    """
    class Meta:
        model = models.Inspeccion
        fields = (
            'id',
            'almacen',
            'sucursal',
            'fecha_alta',
            'estado'
        )


class BotellaDetalleSerializer(serializers.ModelSerializer):
    """ Detalle de Botella """

    class Meta:
        model = models.Botella
        fields = '__all__'
        depth = 1
        # fields = (
        #     'folio',
        #     'estado',
        #     'ingrediente',
        #     'categoria'
        # )


class ItemInspeccionDetalleSerializer(serializers.ModelSerializer):
    """ Detalle de ItemInspeccion """

    botella = BotellaDetalleSerializer()

    class Meta:
        model = models.ItemInspeccion
        fields = ('id', 'botella', 'peso_botella', 'inspeccionado')

#------------------------------------------------------------------


class InspeccionDetalleSerializer(serializers.ModelSerializer):
    """ Arroja una Inspeccion con el detalle de sus ItemInspeccion """

    items_inspeccionados = ItemInspeccionDetalleSerializer(many=True)

    class Meta:
        model = models.Inspeccion
        fields = (
            'id',
            'almacen',
            'sucursal',
            'estado',
            'fecha_alta',
            'usuario_alta',
            'items_inspeccionados'
        )

#------------------------------------------------------------------
class ItemInspeccionSerializer(serializers.ModelSerializer):
    """ Despliega el detalle de un ItemInspeccion """

    class Meta:
        model = models.ItemInspeccion
        fields = ('id', 'peso_botella', 'timestamp_inspeccion')



class BotellaItemInspeccionSerializer(serializers.ModelSerializer):
    """ Despliega una botella con su lista de ItemsInspeccion """

    inspecciones_botella = ItemInspeccionSerializer(many=True)

    class Meta:
        model = models.Botella
        fields = (
            'folio',
            'ingrediente',
            'categoria',
            'peso_inicial',
            'peso_actual',
            'precio_unitario',
            'proveedor',
            'fecha_registro',
            'inspecciones_botella'
        )

#------------------------------------------------------------------
class SucursalSerializer(serializers.ModelSerializer):
    """ Despliega una sucursal, excepto el CLiente """

    class Meta:
        model = models.Sucursal
        fields = (
            'id',
            'nombre',
            'razon_social',
            'rfc',
            'direccion',
            'ciudad',
            'latitud',
            'longitud',
            'codigo_postal',
            'slug'
        )

#------------------------------------------------------------------
class AlmacenSerializer(serializers.ModelSerializer):
    """ Despliega un Almacen """
     
    class Meta:
        model = models.Almacen
        fields = (
            'id',
            'nombre',
            'numero',
        )

#------------------------------------------------------------------
class SucursalDetalleSerializer(serializers.ModelSerializer):
    """ Despliega una sucursal con sus sucursales asociadas """

    almacenes = AlmacenSerializer(many=True)

    class Meta:
        model = models.Sucursal
        fields = (
            'id',
            'nombre',
            'razon_social',
            'rfc',
            'direccion',
            'ciudad',
            'latitud',
            'longitud',
            'codigo_postal',
            'slug',
            'almacenes',
        )

    # class Meta:
    #     model = models.Sucursal
    #     fields = '__all__'
    #     depth = 1

#------------------------------------------------------------------
class ItemInspeccionUpdateSerializer(serializers.ModelSerializer):
    """ Actualiza el peso_botella y el status de un ItemInspeccion """

    class Meta:
        model = models.ItemInspeccion
        fields = ('id', 'peso_botella', 'timestamp_inspeccion', 'inspeccionado')

   


#------------------------------------------------------------------
class InspeccionUpdateSerializer(serializers.ModelSerializer):

    usuario_cierre = serializers.PrimaryKeyRelatedField(read_only=False, queryset=get_user_model().objects.all())

    class Meta:
        model = models.Inspeccion
        fields = (
            'id',
            'almacen',
            'sucursal',
            'estado',
            'fecha_alta',
            'usuario_alta',
            'usuario_cierre',
            'fecha_update',
            'timestamp_update',
        )

#------------------------------------------------------------------
class BotellaUpdateEstadoSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Botella
        fields = (
            'folio',
            'ingrediente',
            'categoria',
            'peso_inicial',
            'peso_actual',
            'precio_unitario',
            'proveedor',
            'fecha_registro',
            'fecha_baja',
            'estado',
        )


class ItemInspeccionBotellaUpdateSerializer(serializers.ModelSerializer):

    botella = BotellaUpdateEstadoSerializer()

    class Meta:
        model = models.ItemInspeccion
        fields = (
            'id',
            'botella',
            'peso_botella',
            'timestamp_inspeccion',
            'inspeccionado'
        )

    def update(self, instance, validated_data):
        # Tomamos los datos validados para actualizar nuestra Botella
        data_botella = validated_data.pop('botella')
        # Actualizamos los datos de nuestro ItemInspeccion
        instance.peso_botella = validated_data.get('peso_botella', instance.peso_botella)
        instance.inspeccionado = True
        # Actualizamos la instancia de nuestra Botella (estado y peso y 'peso_actual')
        botella = instance.botella
        botella.estado = data_botella['estado']
        botella.peso_actual = validated_data.get('peso_botella', None)

        # Si el estado de la botella es 'VACIA', asignamos la fecha de baja:
        if data_botella['estado'] == '0':
            # Asignamos la fecha de baja a la botella, evitando asignar un naive datetime
            naive_datetime = datetime.datetime.now()
            aware_datetime = make_aware(naive_datetime)
            botella.fecha_baja = aware_datetime 
        #instance.botella.estado = data_botella['estado']

        # Guardamos los cambios en nuestras instancias de Botella e ItemInspeccion
        botella.save()
        instance.save()
        return instance



class ItemInspeccionUpdateSerializer2(serializers.ModelSerializer):
    """ Actualiza el peso_botella y el status de un ItemInspeccion y su Botella asociada """

    botella = BotellaUpdateEstadoSerializer()

    class Meta:
        model = models.ItemInspeccion
        fields = ('id', 'peso_botella', 'timestamp_inspeccion', 'inspeccionado', 'botella')
        depth = 1

    def update(self, instance, validated_data):
        # Tomamos los datos validados para actualizar nuestra Botella
        data_botella = validated_data.pop('botella')
        # Actualizamos los datos de nuestro ItemInspeccion
        instance.peso_botella = validated_data.get('peso_botella', instance.peso_botella)
        instance.inspeccionado = True
        # Actualizamos la instancia de nuestra Botella (estado y peso)
        botella = instance.botella
        botella.estado = data_botella['estado']
        botella.peso_actual = validated_data.get('peso_botella', None)



        #instance.botella.estado = data_botella['estado']

        # Guardamos los cambios en nuestras instancias de Botella e ItemInspeccion
        botella.save()
        instance.save()
        return instance


#------------------------------------------------------------------
class IngredienteSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Ingrediente
        fields = (
            'id',
            'codigo',
            'nombre',
            'categoria',
            'factor_peso'
        )


class ProductoIngredienteSerializer(serializers.ModelSerializer):

    ingrediente = IngredienteSerializer()

    class Meta:
        model = models.Producto
        # fields = (
        #     'id',
        #     'folio',
        #     'ingrediente',
        #     'peso_cristal',
        #     'precio_unitario',
        #     'fecha_registro'
        # )
        fields = '__all__'
        depth = 1

#------------------------------------------------------------------
class CategoriaSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Categoria
        fields = ('id', 'nombre',)

#------------------------------------------------------------------
class IngredienteCategoriaSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Ingrediente
        fields = (
            'id',
            'codigo',
            'nombre',
            #'categoria',
            #'factor_peso'
        )

class CategoriaIngredientesSerializer(serializers.ModelSerializer):

    ingredientes = IngredienteCategoriaSerializer(many=True)

    class Meta:
        model = models.Categoria
        fields = (
            'id',
            'nombre',
            'ingredientes'
        )

#------------------------------------------------------------------
class BotellaPostSerializer(serializers.ModelSerializer):

    almacen = serializers.PrimaryKeyRelatedField(read_only=False, queryset=models.Almacen.objects.all())
    sucursal = serializers.PrimaryKeyRelatedField(read_only=False, queryset=models.Sucursal.objects.all())
    usuario_alta = serializers.PrimaryKeyRelatedField(read_only=False, queryset=get_user_model().objects.all())
    producto = serializers.PrimaryKeyRelatedField(read_only=False, queryset=models.Producto.objects.all())
    proveedor = serializers.PrimaryKeyRelatedField(read_only=False, queryset=models.Proveedor.objects.all())

    class Meta:
        model = models.Botella
        fields = (
            'id',
            # Datos del marbete
            'folio',
            'tipo_marbete',
            'fecha_elaboracion_marbete',
            'lote_produccion_marbete',
            'url',
            'producto',
            # Datos del producto en el marbete
            'nombre_marca',
            'tipo_producto',
            'graduacion_alcoholica',
            'capacidad',
            'origen_del_producto',
            'fecha_importacion',
            'nombre_fabricante',
            'rfc_fabricante',
            # Datos registrados con app móvil:
            'estado',
            'fecha_registro',
            'fecha_baja',
            'usuario_alta',
            'sucursal',
            'almacen',
            'peso_cristal',
            'peso_inicial',
            'peso_actual',
            'precio_unitario',
            'proveedor',
            'ingrediente',
            'categoria'
        )


    def validate_peso(self, value):
        """ Validamos que el campo de 'peso_inicial' no esté vacío """

        if value is None:
            raise serializers.ValidationError("Para guardar la botella primero hay que pesarla.")
        
        return value 


    def create(self, validated_data):

        # Tomamos las variables del Producto que se asignarán a la Botella
        #producto_id = validated_data.get('producto')
        producto_asignado = validated_data.get('producto')
        producto_id = producto_asignado.id
        #print('::: ID PRODUCTO :::')
        #print(producto_id)
        #producto_asignado = models.Producto.objects.get(id=producto_id)
        

        peso_cristal = producto_asignado.peso_cristal
        precio_unitario = producto_asignado.precio_unitario
        capacidad = producto_asignado.capacidad
        #proveedor = producto_asignado.proveedor

        # Creamos la botella
        botella = models.Botella.objects.create(
            folio=validated_data.get('folio'),
            tipo_marbete=validated_data.get('tipo_marbete'),
            fecha_elaboracion_marbete=validated_data.get('fecha_elaboracion_marbete'),
            lote_produccion_marbete=validated_data.get('lote_produccion_marbete'),
            url=validated_data.get('url'),
            producto=producto_asignado,
            #producto=producto_asignado.id,
            #producto=validated_data.get('producto'),
            # Datos del producto en marbete
            nombre_marca=validated_data.get('nombre_marca'),
            tipo_producto=validated_data.get('tipo_producto'),
            graduacion_alcoholica=validated_data.get('graduacion_alcoholica'),
            #capacidad=validated_data.get('capacidad'),
            capacidad=capacidad, # Tomamos la capacidad directamente del Producto porque a veces la info del marbete es erronea
            origen_del_producto=validated_data.get('origen_del_producto'),
            fecha_importacion=validated_data.get('fecha_importacion'),
            nombre_fabricante=validated_data.get('nombre_fabricante'),
            rfc_fabricante=validated_data.get('rfc_fabricante'),
            # Datos registrados con app movil
            usuario_alta=validated_data.get('usuario_alta'),
            sucursal=validated_data.get('sucursal'),
            almacen=validated_data.get('almacen'),
            peso_cristal=peso_cristal,
            precio_unitario=precio_unitario,
            proveedor=validated_data.get('proveedor'),
            # Datos obtenidos de la báscula
            peso_inicial=validated_data.get('peso_inicial'),
            peso_actual=validated_data.get('peso_inicial')

        )

        return botella


#------------------------------------------------------------------
class ProductoWriteSerializer(serializers.ModelSerializer):

    ingrediente = serializers.PrimaryKeyRelatedField(read_only=False, queryset=models.Ingrediente.objects.all())

    class Meta:
        model = models.Producto
        fields = (
            'id',
            # Datos del marbete
            'folio',
            'tipo_marbete',
            'fecha_elaboracion_marbete',
            'lote_produccion_marbete',
            'url',
            # Datos del producto en el marbete
            'nombre_marca',
            'tipo_producto',
            'graduacion_alcoholica',
            'capacidad',
            'origen_del_producto',
            'fecha_importacion',
            'nombre_fabricante',
            'rfc_fabricante',
            'fecha_registro',
            # Datos obligatorios ingresados por el usuario
            'peso_cristal',
            'precio_unitario',
            'ingrediente'

        )


    def validate_peso_cristal(self, value):
        """ Validamos que el campo de 'peso_cristal' no esté vacío """

        if value is None:
            raise serializers.ValidationError("Es necesario ingresar el peso del cristal.")
        
        return value


    def validate_precio_unitario(self, value):
        """ Validamos que el campo 'precio_unitario' no esté vacío """ 
        if not value:
        #if value is None:
            raise serializers.ValidationError("Es necesario ingresar el precio unitario.")
        
        return value


#------------------------------------------------------------------
class BotellaUpdateAlmacenSucursalSerializer(serializers.ModelSerializer):

    #sucursal = serializers.PrimaryKeyRelatedField(read_only=False, queryset=models.Sucursal.objects.all())
    #almacen = serializers.PrimaryKeyRelatedField(read_only=False, queryset=models.Almacen.objects.all())

    class Meta:
        model = models.Botella
        fields = (
            'folio',
            'ingrediente',
            'categoria',
            'peso_inicial',
            'precio_unitario',
            'proveedor',
            'fecha_registro',
            'estado',
            'almacen',
            'sucursal',
        )




class TraspasoWriteSerializer(serializers.ModelSerializer):

    botella = serializers.PrimaryKeyRelatedField(read_only=False, queryset=models.Botella.objects.all())
    #botella = BotellaUpdateAlmacenSucursalSerializer()
    sucursal = serializers.PrimaryKeyRelatedField(read_only=False, queryset=models.Sucursal.objects.all())
    almacen = serializers.PrimaryKeyRelatedField(read_only=False, queryset=models.Almacen.objects.all())

    class Meta:
        model = models.Traspaso
        fields = (
            'id',
            'botella',
            'sucursal',
            'almacen',
            #'usuario',
        )

    def create(self, validated_data):

        botella = validated_data.get('botella')
        sucursal = validated_data.get('sucursal')
        almacen = validated_data.get('almacen')

        #

        traspaso = models.Traspaso.objects.create(
            botella=botella,
            sucursal=sucursal,
            almacen=almacen,
        )

        botella.almacen = almacen
        botella.sucursal = sucursal
        botella.save()

        return traspaso


#------------------------------------------------------------------
class BotellaConsultaSerializer(serializers.ModelSerializer):

    class Meta: 
        model = models.Botella
        fields = '__all__'
        depth = 1


#------------------------------------------------------------------
class IngredienteWriteSerializer(serializers.ModelSerializer):

    categoria = serializers.PrimaryKeyRelatedField(read_only=False, queryset=models.Categoria.objects.all())

    class Meta:
        model = models.Ingrediente
        fields = '__all__'
        depth = 1


#------------------------------------------------------------------
class ProveedorSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Proveedor
        fields = '__all__'
        
        


    

    



