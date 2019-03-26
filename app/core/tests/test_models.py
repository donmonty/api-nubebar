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


def almacen_dummy(**params):
    """ Crea un almacen dummy para los tests """

    defaults = {
        'nombre': 'BARRA 1',
        'numero': 1,
        'sucursal': sucursal_dummy()
    }

    defaults.update(params)

    return models.Almacen.objects.create(**defaults)


def caja_dummy(**params):
    """ Crea una caja dummy para los tests """

    defaults = {
        'numero': 1,
        'nombre': 'BARRA 1',
        'almacen': almacen_dummy()
    }

    defaults.update(params)

    return models.Caja.objects.create(**defaults)


def venta_dummy(**params):
    """ Crea una venta para los tests """

    defaults = {
        'receta': receta_dummy(),
        'sucursal': sucursal_dummy(),
        'fecha': '2019-03-26',
        'unidades': 1,
        'importe': 200,
        'caja': caja_dummy()
    } 

    defaults.update(params)

    return models.Venta.objects.create(**defaults)


def categoria_dummy(**params):
    """ Crea una categoría dummy para los tests """

    defaults = {
        'nombre': 'WHISKY',
    }

    defaults.update(params)

    return models.Categoria.objects.create(**defaults)


def ingrediente_dummy(**params):
    """ Crea un ingrediente dummy para los tests """

    defaults = {
        'codigo': 'WHIS001',
        'nombre': 'JACK DANIELS',
        'categoria': categoria_dummy(),
        'factor_peso': 0.92
    }

    defaults.update(params)

    return models.Ingrediente.objects.create(**defaults)


def receta_dummy(**params):
    """ Crea una receta dummy para los tests """

    defaults = {
        'codigo_pos': 'CPWHIS001',
        'nombre': 'JACK DANIELS DERECHO',
        'sucursal': sucursal_dummy()
    }

    defaults.update(params)

    return models.Receta.objects.create(**defaults)


"""
---------------------------------------------------------
TESTS PARA LOS MODELOS DE LA APP
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

    
    def test_new_user_email_normalized(self):
        """ Test the email for a new user is normalized """

        email = 'test@FOODSTACK.MX'
        password = 'password123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )
        print(email.lower())

        self.assertEqual(user.email, email.lower())

    
    def test_new_user_invalid_email(self):
        """ Test creating user with no email raises error """

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'password123')

    
    def test_create_new_superuser(self):
        """ Test creating new super user """

        email = 'test@foodstack.mx'
        password = 'password123'

        user = get_user_model().objects.create_superuser(
            email=email,
            password=password
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)


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


    def test_crear_ingrediente(self):
        """ Testear que se construye un Ingrediente con éxito """

        codigo = 'WHIS001'
        nombre = 'JACK DANIELS'
        categoria = models.Categoria.objects.create(nombre='WHISKY')
        factor_peso = 0.95

        ingrediente = models.Ingrediente.objects.create(
            codigo=codigo,
            nombre=nombre,
            categoria=categoria,
            factor_peso=factor_peso
        )

        ingredientes_categoria = categoria.ingredientes.all()

        self.assertEqual(ingrediente.codigo, codigo)
        self.assertEqual(ingredientes_categoria.count(), 1)


    def  test_crear_receta(self):
        """ Testear que se construya una Receta con éxito """

        codigo_pos = 'CPWHIS001',
        nombre = 'JACK DANIELS DERECHO'
        sucursal = sucursal_dummy()

        receta = models.Receta.objects.create(
            codigo_pos=codigo_pos,
            nombre=nombre,
            sucursal=sucursal
        )

        self.assertEqual(receta.codigo_pos, codigo_pos)
        
    
    def test_crear_ingredientereceta(self):
        """ Testear que se construye un IngredienteReceta con éxito """

        receta = receta_dummy()
        ingrediente = ingrediente_dummy()
        volumen = 90

        ingrediente_receta = models.IngredienteReceta.objects.create(
            receta=receta,
            ingrediente=ingrediente,
            volumen=volumen
        )

        ingredientes = receta.ingredientes.all()

        self.assertEqual(ingredientes.count(), 1)


    def test_crear_almacen(self):
        """ Testear que se construye un Almacen """

        nombre = 'BARRA 1'
        numero = 1
        sucursal = sucursal_dummy()

        almacen = models.Almacen.objects.create(
            nombre=nombre,
            numero=numero,
            sucursal=sucursal
        )

        almacenes_sucursal = sucursal.almacenes.all()

        self.assertEqual(almacen.nombre, nombre)
        self.assertEqual(almacenes_sucursal.count(), 1)

    
    def test_crear_caja(self):
        """ Testear que se construye una Caja """

        numero = 1
        nombre = 'CAJA 1'
        almacen = almacen_dummy()

        caja = models.Caja.objects.create(
            numero=numero,
            nombre=nombre,
            almacen=almacen
        )

        cajas_almacen = almacen.cajas.all()

        self.assertEqual(caja.numero, numero)
        self.assertEqual(cajas_almacen.count(), 1)


    def test_crear_venta(self):
        """ Testear que se construye una venta """

        receta = receta_dummy()
        sucursal = sucursal_dummy()
        fecha = '2019-03-26'
        unidades = 1
        importe = 200
        caja = caja_dummy()

        venta = models.Venta.objects.create(
            receta=receta,
            sucursal=sucursal,
            fecha=fecha,
            unidades=unidades,
            importe=importe,
            caja=caja
        )

        ventas_receta = receta.ventas_receta.all()
        ventas_sucursal = sucursal.ventas_sucursal.all()
        ventas_caja = caja.ventas_caja.all()

        self.assertEqual(ventas_receta.count(), 1)
        self.assertEqual(ventas_sucursal.count(), 1)
        self.assertEqual(ventas_caja.count(), 1)

    
    def test_crear_consumorecetavendida(self):
        """ Testear que se crea un ConsumoRecetaVendida """

        ingrediente = ingrediente_dummy()
        receta = receta_dummy()
        venta = venta_dummy()
        fecha = '2019-03-26'
        volumen = 90

        consumo_receta_vendida = models.ConsumoRecetaVendida.objects.create(
            ingrediente=ingrediente,
            receta=receta,
            venta=venta,
            fecha=fecha,
            volumen=volumen
        )

        consumos_ingrediente = ingrediente.consumos_ingrediente.all()
        consumos_receta = receta.consumos_receta.all()
        consumos_venta = venta.consumos_venta.all()

        self.assertEqual(consumos_ingrediente.count(), 1)
        self.assertEqual(consumos_receta.count(), 1)
        self.assertEqual(consumos_venta.count(), 1)




    





    

