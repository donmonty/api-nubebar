from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models


def cliente_dummy(**params):
        """ Crea un cliente dummy para usar en los tests """

        defaults = {
            'nombre': 'Tacos Link',
            'razon_social': 'Tacos Link SA de CV',
            'rfc': 'LINK190101XYZ',
            'direccion': 'Kokoro Village 666',
            'ciudad': 'Hyrule'
        }

        defaults.update(params)

        return models.Cliente.objects.create(**defaults)

    
def sucursal_dummy(**params):
    """ Crea una sucursal dummy para usar en nuestros tests """

    defaults = {
        'nombre': 'Tacos Link Providencia',
        'cliente': cliente_dummy(),
        'razon_social': 'TACOS LINK PROVIDENCIA SA DE CV',
        'rfc': 'LPRO190101XYZ',
        'direccion': 'Terranova 666',
        'ciudad': 'Guadalajara',
        'latitud': 20.676,
        'longitud': -103.383,
        'codigo_postal': '45110'

    }

    defaults.update(params)

    return models.Sucursal.objects.create(**defaults)


"""
---------------------------------------------------------
TESTS PARA LOS MODELOS DE LA BASE DE DATOS
---------------------------------------------------------
"""
class ModelTests(TestCase):

    def test_crear_cliente(self):
        """Testear que se crea un Cliente con éxito"""

        nombre = 'Cliente Test'
        razon_social = 'CLiente Test SA de CV'
        rfc = 'CTES190101XYZ'
        direccion = 'Calle 666'
        ciudad = 'Ciudad de la Furia'

        cliente = models.Cliente.objects.create(
            nombre=nombre,
            razon_social=razon_social,
            rfc=rfc,
            direccion=direccion,
            ciudad=ciudad
        )

        self.assertEqual(cliente.nombre, nombre)
        self.assertEqual(cliente.rfc, rfc)


    def test_crear_sucursal(self):
        """ Testear que se crea una Sucursal con éxito """

        nombre = 'TACOS LINK PROVIDENCIA'
        cliente = cliente_dummy()
        razon_social = 'TACOS LINK PROVIDENCIA SA DE CV'
        rfc = 'LPRO190101XYZ'
        direccion = 'Terranova 666'
        ciudad = 'Guadalajara'
        latitud = 20.676
        longitud = -103.383
        codigo_postal = '45110'

        sucursal = models.Sucursal.objects.create(
            nombre=nombre,
            cliente=cliente,
            razon_social=razon_social,
            rfc=rfc,
            direccion=direccion,
            ciudad=ciudad,
            latitud=latitud,
            longitud=longitud,
            codigo_postal=codigo_postal
        )

        self.assertEqual(str(sucursal), nombre)


    def test_create_user_with_email_successful(self):
        """ Test creating a new user with an email is successful """

        email = 'test@foodstack.mx'
        password = 'password123'

        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))


    def test_asignar_sucursal_a_usuario(self):
        """ Testear que se asigne una sucursal al usuario """

        user = get_user_model().objects.create_user(
            email='test@foodstack.mx',
            password='password123'
        )

        sucursal = sucursal_dummy()
        user.sucursales.add(sucursal)
        user.save()

        sucursales_usuario = user.sucursales.all()

        self.assertEqual(sucursales_usuario.count(), 1)

