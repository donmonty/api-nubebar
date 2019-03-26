from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

from django.conf import settings


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
	ciudad          = models.CharField(max_length=255, blank=True) 
	#estado: Quizá conviene crear una tabla para los estados
	latitud 		= models.DecimalField(max_digits=9, decimal_places=3, blank=True, null=True)
	longitud 		= models.DecimalField(max_digits=9, decimal_places=3, blank=True, null=True)
	codigo_postal 	= models.CharField(max_length=5, blank=True)

	def __str__(self):
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
		
		return '{} - {} - {}'.format(nombre_receta, nombre_ingrediente, self.voumen)


"""
--------------------------------------------------------------------------
Un Almacen es una barra o bodega donde se guardan botellas. Puede tener
una o varias cajas.
--------------------------------------------------------------------------
"""

class Almacen(models.Model):

	nombre 		= models.CharField(max_length=255, blank=True)
	numero 		= models.IntegerField(default=1)
	sucursal 	= models.ForeignKey(Sucursal, related_name='almacenes', on_delete=models.CASCADE)

	def __str__(self):
		nombre_sucursal = self.sucursal.nombre

		return '{} - {}'.format(self.nombre, nombre_sucursal)


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
		nombre_sucursal = self.almacen__sucursal.nombre

		return 'CAJA: {} - BARRA: {} - SUCURSAL: {}'.format(self.numero, nombre_almacen, nombre_sucursal)


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

		return 'RECETA: {} - SUCURSAL: {} - FECHA: {} - UNIDADES: {} - IMPORTE: {} - CAJA: {}'.format(nombre_receta, nombre_sucursal, self.fecha, self.unidades, self.importe, self.caja)


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

		return 'INGREDIENTE: {} - RECETA: {} - VENTA: {} - FECHA: {} - VOLUMEN {}'.format(nombre_ingrediente, nombre_receta, self.venta, self.fecha, self.volumen)


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

		return '{} - {} - {}'.format(nombre_ingrediente, self.folio, self.peso_cristal, self.precio_unitario)


