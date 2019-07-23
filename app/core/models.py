from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

from django.conf import settings

import datetime
import decimal
#from datetime import date


"""
--------------------------------------------------------------------------
Un cliente es la persona moral o física que opera el centro de consumo
--------------------------------------------------------------------------
"""

class Cliente(models.Model):

	nombre 			= models.CharField(max_length=255)
	razon_social 	= models.CharField(max_length=255, blank=True)
	rfc 			= models.CharField(max_length=13, blank=True)
	direccion 		= models.TextField(max_length=500, blank=True)
	ciudad          = models.CharField(max_length=255, blank=True) 
	#estado: Quizá conviene crear una tabla para los estados

	def __str__ (self):
		return self.nombre


"""
--------------------------------------------------------------------------
Una sucursal es un centro de consumo. Un cliente puede operar una o varias
sucursales
--------------------------------------------------------------------------
"""

class Sucursal(models.Model):

	nombre 			= models.CharField(max_length=255)
	cliente 		= models.ForeignKey(Cliente, related_name='sucursales', on_delete=models.CASCADE)
	razon_social 	= models.CharField(max_length=255, blank=True)
	rfc 			= models.CharField(max_length=13, blank=True)
	direccion 		= models.TextField(max_length=500, blank=True)
	ciudad 			= models.CharField(max_length=255, blank=True) 
	#estado: Quizá conviene crear una tabla para los estados
	latitud 		= models.DecimalField(max_digits=9, decimal_places=3, blank=True, null=True)
	longitud 		= models.DecimalField(max_digits=9, decimal_places=3, blank=True, null=True)
	codigo_postal 	= models.CharField(max_length=5, blank=True)
	slug 			= models.CharField(max_length=255, blank=True)


	def save(self, *args, **kwargs):
		nombre_sucursal = self.nombre
		nombre_split = nombre_sucursal.split(' ')
		nombre_concat = ('-').join(nombre_split).upper()
		self.slug = nombre_concat
		super(Sucursal, self).save(*args, **kwargs)

	def __str__(self):
		return self.nombre
    

"""
--------------------------------------------------------------------------
Un Proveedor vende las botellas que se ingresan al inventario
--------------------------------------------------------------------------
"""

class Proveedor(models.Model):

	nombre 			= models.CharField(max_length=255)
	razon_social 	= models.CharField(max_length=255, blank=True)
	rfc 			= models.CharField(max_length=13, blank=True)
	direccion 		= models.TextField(max_length=500, blank=True)
	ciudad          = models.CharField(max_length=255, blank=True) 
	#estado: Quizá conviene crear una tabla para los estados

	def __str__ (self):
		return self.nombre


"""
--------------------------------------------------------------------------
El UserManager nos permite crear nuestro custom User
--------------------------------------------------------------------------
"""

class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        """Creates and saves a new User"""

        if not email:
            raise ValueError('El usuario debe proporcionar un email')

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """ Creates and saves a new super user """

        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


"""
--------------------------------------------------------------------------
Una clase custom que nos permite crear usuarios utilizando email en vez
de username
--------------------------------------------------------------------------
"""

class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model that supports using email instead of username"""

    email 		= models.EmailField(max_length=255, unique=True)
    name 		= models.CharField(max_length=255)
    is_active 	= models.BooleanField(default=True)
    is_staff 	= models.BooleanField(default=False)
    sucursales  = models.ManyToManyField('Sucursal')

    objects = UserManager()

    USERNAME_FIELD = 'email'


"""
--------------------------------------------------------------------------
Categoria del ingrediente (WHISKY, TEQUILA, VODKA, etc)
--------------------------------------------------------------------------
"""

class Categoria(models.Model):

	nombre = models.CharField(max_length=255)

	def __str__(self):
		return self.nombre


"""
--------------------------------------------------------------------------
Un Ingrediente es un destilado. Un ingrediente puede estar en varias recetas
--------------------------------------------------------------------------
"""

class Ingrediente(models.Model):

	codigo 		= models.CharField(max_length=255, unique=True)
	nombre 		= models.CharField(max_length=255)
	categoria 	= models.ForeignKey(Categoria, related_name='ingredientes', on_delete=models.CASCADE)
	factor_peso = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)

	def __str__(self):
		return '{} - {}'.format(self.nombre, self.codigo)



"""
--------------------------------------------------------------------------
Una Receta es un trago, coctel o botella que está en el menú. Puede tener
uno o varios ingredientes
--------------------------------------------------------------------------
"""

class Receta(models.Model):

	codigo_pos 		= models.CharField(max_length=255)
	nombre 			= models.CharField(max_length=255)
	sucursal 		= models.ForeignKey(Sucursal, related_name='recetas', on_delete=models.CASCADE)
	ingredientes 	= models.ManyToManyField(Ingrediente, through='IngredienteReceta')


	def __str__(self):
		nombre_sucursal = self.sucursal.nombre
		
		return '{} - {} - {}'.format(self.codigo_pos, self.nombre, nombre_sucursal)


"""
--------------------------------------------------------------------------
Modelo intermedio entre Ingrediente y Receta
--------------------------------------------------------------------------
"""

class IngredienteReceta(models.Model):

	receta 		= models.ForeignKey(Receta, on_delete=models.CASCADE)
	ingrediente = models.ForeignKey(Ingrediente, on_delete=models.CASCADE)
	volumen 	= models.IntegerField()

	class Meta:
		unique_together = ['receta', 'ingrediente']

	def __str__(self):
		nombre_receta = self.receta.nombre
		nombre_ingrediente = self.ingrediente.nombre
		
		return 'RECETA: {} - INGREDIENTE: {} - VOLUMEN: {}'.format(nombre_receta, nombre_ingrediente, self.volumen)


"""
--------------------------------------------------------------------------
Un Almacen es una barra o bodega donde se guardan botellas. Puede tener
una o varias cajas.
--------------------------------------------------------------------------
"""

class Almacen(models.Model):

	# Tipos de almacenes
	BARRA = '1'
	BODEGA = '0'
	TIPOS_ALMACEN = ((BARRA, 'BARRA'), (BODEGA, 'BODEGA'))

	nombre 		= models.CharField(max_length=255, blank=True)
	numero 		= models.IntegerField(default=1)
	sucursal 	= models.ForeignKey(Sucursal, related_name='almacenes', on_delete=models.CASCADE)
	tipo 		= models.CharField(max_length=1, choices=TIPOS_ALMACEN, default=BARRA)

	def __str__(self):
		nombre_sucursal = self.sucursal.nombre

		return 'NOMBRE: {} - SUCURSAL: {} - TIPO: {}'.format(self.nombre, nombre_sucursal, self.tipo)


"""
--------------------------------------------------------------------------
Una Caja registra ventas y siempre está asociada a un Almacen
--------------------------------------------------------------------------
"""

class Caja(models.Model):

	numero 		= models.IntegerField(default=1)
	nombre 		= models.CharField(max_length=255, blank=True)
	almacen 	= models.ForeignKey(Almacen, related_name='cajas', on_delete=models.CASCADE)

	def __str__(self):
		nombre_almacen = self.almacen.nombre

		return 'CAJA: {} - BARRA: {}'.format(self.numero, nombre_almacen)


"""
--------------------------------------------------------------------------
Una Venta registra la venta de una Receta que ocurre en una Sucursal a
través de una Caja
--------------------------------------------------------------------------
"""

class Venta(models.Model):

	receta 		= models.ForeignKey(Receta, related_name='ventas_receta', on_delete=models.CASCADE)
	sucursal 	= models.ForeignKey(Sucursal, related_name='ventas_sucursal', on_delete=models.CASCADE)
	fecha 		= models.DateField()
	unidades 	= models.IntegerField()
	importe 	= models.IntegerField()
	caja     	= models.ForeignKey(Caja, related_name='ventas_caja', on_delete=models.CASCADE)

	def __str__(self):
		nombre_receta = self.receta.nombre
		nombre_sucursal = self.sucursal.nombre

		return 'RECETA: {} - SUCURSAL: {} - FECHA: {} - UNIDADES: {} - IMPORTE: {} - CAJA: {}'.format(nombre_receta, nombre_sucursal, self.fecha, self.unidades, self.importe, self.caja.nombre)


"""
--------------------------------------------------------------------------
La venta de una Receta provoca el consumo de uno o más ingredientes
--------------------------------------------------------------------------
"""

class ConsumoRecetaVendida(models.Model):

	ingrediente 	= models.ForeignKey(Ingrediente, related_name='consumos_ingrediente', on_delete=models.CASCADE)
	receta 			= models.ForeignKey(Receta, related_name='consumos_receta', on_delete=models.CASCADE)
	venta 			= models.ForeignKey(Venta, related_name='consumos_venta', on_delete=models.CASCADE)
	fecha 			= models.DateField()
	volumen 		= models.IntegerField()

	def __str__(self):
		nombre_ingrediente = self.ingrediente.nombre
		nombre_receta = self.receta.nombre

		return 'INGREDIENTE: {} - RECETA: {} - VENTA: {} - FECHA: {} - VOLUMEN {}'.format(nombre_ingrediente, nombre_receta, self.venta.id, self.fecha, self.volumen)


"""
--------------------------------------------------------------------------
Un Producto es un tipo de botella con una combinación única de ingrediente,
envase, y precio unitario (Preregistro en la app anterior)
--------------------------------------------------------------------------
"""

class Producto(models.Model):

	folio 						= models.CharField(max_length=12)
	ingrediente 				= models.ForeignKey(Ingrediente, related_name='productos', on_delete=models.CASCADE)
	
	# Datos del marbete
	tipo_marbete 				= models.CharField(max_length=255, blank=True)
	fecha_elaboracion_marbete 	= models.CharField(max_length=255, blank=True)
	lote_produccion_marbete 	= models.CharField(max_length=255, blank=True)
	url 						= models.URLField(max_length=255, blank=True)

	# Datos del producto en el marbete
	nombre_marca 				= models.CharField(max_length=255, blank=True)
	tipo_producto 				= models.CharField(max_length=255, blank=True)
	graduacion_alcoholica 		= models.CharField(max_length=255, blank=True)
	capacidad 					= models.IntegerField(blank=True, null=True)
	origen_del_producto 		= models.CharField(max_length=255, blank=True)
	fecha_importacion 			= models.CharField(max_length=255, blank=True)
	nombre_fabricante 			= models.CharField(max_length=255, blank=True)
	rfc_fabricante 				= models.CharField(max_length=255, blank=True)

	# Registro con app iOS
	fecha_registro 				= models.DateTimeField(auto_now_add=True)
	peso_cristal 				= models.IntegerField(blank=True, null=True)
	precio_unitario 			= models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)


	def __str__(self):
		nombre_ingrediente = self.ingrediente.nombre

		return 'NOMBRE: {} - FOLIO: {} - PESO CRISTAL: {} - PRECIO UNITARIO: {}'.format(nombre_ingrediente, self.folio, self.peso_cristal, self.precio_unitario)


"""
--------------------------------------------------------------------------
Botella es una botella física que se da de alta en un almacén y que
tiene un folio único
--------------------------------------------------------------------------
"""

class Botella(models.Model):
	# Estados que puede tener una botella
	NUEVA = '2'
	CON_LIQUIDO = '1'
	VACIA = '0'
	PERDIDA = '3'
	ESTADOS_BOTELLA = ((NUEVA, 'NUEVA'), (CON_LIQUIDO, 'CON LIQUIDO'), (VACIA, 'VACIA'), (PERDIDA, 'PERDIDA'))
	
	# Datos del marbete
	folio                       = models.CharField(max_length=12, unique=True)
	tipo_marbete                = models.CharField(max_length=255, blank=True)
	fecha_elaboracion_marbete   = models.CharField(max_length=255, blank=True)
	lote_produccion_marbete     = models.CharField(max_length=255, blank=True)
	url                         = models.URLField(max_length=255, blank=True)
	producto                    = models.ForeignKey(Producto, related_name='botellas', blank=True, null=True, on_delete=models.SET_NULL)
	
	# Datos del producto en el marbete
	nombre_marca 				= models.CharField(max_length=255, blank=True)
	tipo_producto 				= models.CharField(max_length=255, blank=True)
	graduacion_alcoholica 		= models.CharField(max_length=255, blank=True)
	capacidad 					= models.IntegerField(blank=True, null=True)
	origen_del_producto 		= models.CharField(max_length=255, blank=True)
	fecha_importacion 			= models.CharField(max_length=255, blank=True)
	nombre_fabricante 			= models.CharField(max_length=255, blank=True)
	rfc_fabricante 				= models.CharField(max_length=255, blank=True)
	
	# Datos de registro con scan app iOS
	estado 						= models.CharField(max_length=1, choices=ESTADOS_BOTELLA, default=NUEVA) # Revisar qué tipo de estado es
	fecha_registro 				= models.DateTimeField(auto_now_add=True)
	fecha_baja 					= models.DateTimeField(blank=True, null=True, default=None) # Revisar
	usuario_alta 				= models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL) # Revisar
	sucursal 					= models.ForeignKey(Sucursal, related_name='botellas_sucursal', null=True, blank=True, on_delete=models.SET_NULL)
	almacen 					= models.ForeignKey(Almacen, related_name='botellas_almacen', blank=True, null=True, on_delete=models.SET_NULL)
	peso_cristal 				= models.IntegerField(blank=True, null=True, default=0)
	peso_inicial 				= models.IntegerField(blank=True, null=True, default=0)
	peso_actual 				= models.IntegerField(blank=True, null=True, default=0)
	precio_unitario 			= models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	proveedor 					= models.ForeignKey(Proveedor, related_name='botellas_proveedor', blank=True, null=True, on_delete=models.SET_NULL)
	ingrediente 				= models.CharField(max_length=255, blank=True)
	categoria 					= models.CharField(max_length=255, blank=True)

	def save(self, *args, **kwargs):
		
		# Checamos si el campo 'producto' es None
		if self.producto is not None:
			# Traemos los valores de 'ingrediente' y 'categoria'
			producto = self.producto
			ingrediente = producto.ingrediente
			nombre_ingrediente = ingrediente.nombre
			self.ingrediente = nombre_ingrediente

			categoria = ingrediente.categoria
			nombre_categoria = categoria.nombre
			self.categoria = nombre_categoria
			super(Botella, self).save(*args, **kwargs)

		else:
			self.ingrediente = ''
			self.categoria = ''
			super(Botella, self).save(*args, **kwargs)


	def __str__(self):
		producto = self.producto
		ingrediente = producto.ingrediente
		nombre_ingrediente = ingrediente.nombre
		nombre_sucursal = self.sucursal.nombre
		numero_almacen = self.almacen.numero
		return 'FOLIO: {} - INGREDIENTE: {} - PESO CRISTAL: {} - PRECIO: {} - ESTADO: {} - SUCURSAL: {} - ALMACEN: {}'.format(self.folio, nombre_ingrediente, self.peso_cristal, self.precio_unitario, self.estado, nombre_sucursal, numero_almacen)

"""
--------------------------------------------------------------------------
Un Traspaso sucede cuando se cambia una botella de almacén
--------------------------------------------------------------------------
"""

class Traspaso(models.Model):

	botella 	= models.ForeignKey(Botella, related_name='traspasos_botella', on_delete=models.CASCADE)
	sucursal 	= models.ForeignKey(Sucursal, related_name='traspasos_sucursal', on_delete=models.CASCADE)
	almacen 	= models.ForeignKey(Almacen, related_name='traspasos_almacen', on_delete=models.CASCADE)
	fecha 		= models.DateTimeField(auto_now_add=True)
	usuario 	= models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL)

	def __str__(self):
		folio_botella = self.botella.folio
		nombre_sucursal = self.sucursal.nombre
		numero_almacen = self.almacen.numero

		return 'FOLIO: {} - SUCURSAL: {} - ALMACEN: {} - FECHA: {}'.format(folio_botella, nombre_sucursal, numero_almacen, self.fecha)


"""
--------------------------------------------------------------------------
Una Inspeccion es un evento en el que se inspeccionan varias botellas. Se
compone de varios ItemInspeccion.
--------------------------------------------------------------------------
"""

class Inspeccion(models.Model):

	# Tipos de Inspeccion:
	DIARIA = '0'
	TOTAL = '1'
	TIPOS_INSPECCION = ((DIARIA, 'DIARIA'), (TOTAL, 'TOTAL'))

	# Estados que puede tener una Inspeccion:
	ABIERTA = '0'
	CERRADA = '1'
	ESTADOS_INSPECCION = ((ABIERTA, 'ABIERTA'), (CERRADA, 'CERRADA'))
	tipo 				= models.CharField(max_length=1, choices=TIPOS_INSPECCION, default=DIARIA)
	almacen             = models.ForeignKey(Almacen, related_name='inspecciones_almacen', on_delete=models.CASCADE)
	sucursal            = models.ForeignKey(Sucursal, related_name='inspecciones_sucursal', on_delete=models.CASCADE)
	usuario_alta        = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='inspecciones_usuario_alta', blank=True, null=True, on_delete=models.SET_NULL)
	usuario_cierre      = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='inspecciones_usuario_cierre', blank=True, null=True, on_delete=models.SET_NULL)
	fecha_alta 			= models.DateField(auto_now_add=True)
	timestamp_alta      = models.DateTimeField(auto_now_add=True)
	fecha_update        = models.DateField(auto_now=True)
	timestamp_update    = models.DateTimeField(auto_now=True)
	estado              = models.CharField(max_length=1, choices=ESTADOS_INSPECCION, default=ABIERTA)
	
	def __str__(self):
		numero_almacen = self.almacen.numero
		nombre_sucursal = self.sucursal.nombre
		
		return 'FECHA: {} - SUCURSAL: {} - ALMACEN: {} - ESTADO: {} - TIPO: {}'.format(self.fecha_alta, nombre_sucursal, numero_almacen, self.estado, self.tipo)


"""
--------------------------------------------------------------------------
Un ItemInspeccion es la inspección de una botella física.
--------------------------------------------------------------------------
"""

class ItemInspeccion(models.Model):

	inspeccion              = models.ForeignKey(Inspeccion, related_name='items_inspeccionados', on_delete=models.CASCADE)
	botella                 = models.ForeignKey(Botella, related_name='inspecciones_botella', on_delete=models.CASCADE)
	peso_botella            = models.IntegerField(null=True, blank=True)
	timestamp_inspeccion    = models.DateTimeField(auto_now=True)
	inspeccionado 			= models.BooleanField(default=False)
	
	def __str__(self):
		fecha_inspeccion = self.inspeccion.fecha_alta
		folio_botella = self.botella.folio
		return 'FECHA: {} - FOLIO: {} - PESO: {}'.format(fecha_inspeccion, folio_botella, self.peso_botella)


"""
------------------------------------------------------------------------------
Un ProductoSinRegistro es un item del reporte de ventas que no está registrado
en la base de datos
------------------------------------------------------------------------------
"""

class ProductoSinRegistro(models.Model):

    sucursal    = models.CharField(max_length=255, blank=True)
    codigo_pos  = models.CharField(max_length=255, blank=True)
    caja        = models.IntegerField(null=True, blank=True)
    nombre      = models.CharField(max_length=255, blank=True)
    fecha       = models.DateField(blank=True, null=True, default=datetime.date.today)

    def __str__(self):
        return 'SUCURSAL: {} - CODIGO: {} - NOMBRE: {}'.format(self.sucursal, self.codigo_pos, self.nombre)


"""
--------------------------------------------------------------------------
Un ReporteMermas es el reporte de mermas de una Inspeccion
--------------------------------------------------------------------------
"""

class ReporteMermas(models.Model):

	fecha_registro 	= models.DateField(auto_now_add=True)
	fecha_inicial 	= models.DateField(blank=True, null=True, default=None)
	fecha_final 	= models.DateField(blank=True, null=True, default=None)
	inspeccion 		= models.ForeignKey(Inspeccion, related_name='reportes_mermas_inspeccion', on_delete=models.CASCADE)
	almacen 		= models.ForeignKey(Almacen, related_name='reportes_mermas_almacen', on_delete=models.CASCADE)

	class Meta:
		verbose_name_plural = 'ReportesMermas'
		get_latest_by = 'fecha_registro'

	def __str__(self):
		return 'FECHA: {} - INSPECCION: {} - ALMACEN: {} - SUCURSAL: {} - FECHA INICIAL: {} - FECHA FINAL: {}'.format(self.fecha_registro, self.inspeccion.id, self.almacen.id, self.almacen.sucursal.nombre, self.fecha_inicial, self.fecha_final)


"""
--------------------------------------------------------------------------
Una MermaIngrediente es la merma registrada para un Ingediente como resultado
de hacer una Inspeccion
--------------------------------------------------------------------------
"""

class MermaIngrediente(models.Model):

	ingrediente 	= models.ForeignKey(Ingrediente, related_name='mermas_ingrediente', on_delete=models.CASCADE)
	reporte 		= models.ForeignKey(ReporteMermas, related_name='mermas_reporte', blank=True, null=True, on_delete=models.CASCADE)
	almacen 		= models.ForeignKey(Almacen, related_name='mermas_almacen', on_delete=models.CASCADE)
	fecha_inicial 	= models.DateField(blank=True, null=True, default=None)
	fecha_final 	= models.DateField(blank=True, null=True, default=None)
	consumo_ventas 	= models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	consumo_real 	= models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	merma 			= models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
	porcentaje 		= models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

	class Meta:
		verbose_name_plural = 'MermasIngredientes'

	def save(self, *args, **kwargs):

		try:
			self.merma = self.consumo_ventas - self.consumo_real
			self.porcentaje = (self.merma / self.consumo_ventas) * 100
			super(MermaIngrediente, self).save(*args, **kwargs)

		except (TypeError, ZeroDivisionError):

			if (self.consumo_ventas is None) & (self.consumo_real is None):
				self.merma = decimal.Decimal(0)
				self.porcentaje = decimal.Decimal(0)
				super(MermaIngrediente, self).save(*args, **kwargs)

			elif self.consumo_ventas is None:
				self.merma = decimal.Decimal(0) - self.consumo_real
				self.porcentaje = decimal.Decimal(-100)
				super(MermaIngrediente, self).save(*args, **kwargs)

			elif self.consumo_real is None:
				self.merma = self.consumo_ventas
				self.porcentaje = decimal.Decimal(100)
				super(MermaIngrediente, self).save(*args, **kwargs)

			else:
				self.merma = self.consumo_ventas - self.consumo_real
				self.porcentaje = decimal.Decimal(-100)
				super(MermaIngrediente, self).save(*args, **kwargs)


	def __str__(self):
		return 'INGREDIENTE: {} - MERMA: {} ml - FECHA INICIAL: {} - FECHA FINAL: {} - REPORTE: {} - ALMACEN: {} - SUCURSAL: {}'.format(self.ingrediente.nombre, self.merma, self.fecha_inicial, self.fecha_final, self.reporte.id, self.almacen.id, self.almacen.sucursal.nombre)


		# # Calculamos la merma
		# if self.consumo_ventas == None:
		# 	self.merma = decimal.Decimal(0) - self.consumo_real
		# elif self.consumo_real == None:
		# 	self.merma = self.consumo_ventas
		# else:
		# 	self.merma = self.consumo_ventas - self.consumo_real

		# # Calculamos el porcentaje
		# try:
		# 	self.porcentaje = (self.merma / self.consumo_ventas) * 100
		# 	super(MermaIngrediente, self).save(*args, **kwargs)

		# except ZeroDivisionError, Exception:
		# 	self.porcentaje = decimal.Decimal(0)
		# 	super(MermaIngrediente, self).save(*args, **kwargs)
