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

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_super_user(self, email, password):
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
