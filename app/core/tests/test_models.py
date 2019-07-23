from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
from core import models
#from datetime import date
import datetime
from freezegun import freeze_time
import json


#def usuario_dummy(email='test@foodstack.mx', password='password123'):
 #   """ Crea un usuario dummy para los tests"""
  #  return get_user_model().objects.create_user(email, password)


def usuario_dummy(**params):
    """ Crea un usuario dummy para los tests """

    defaults = {
        'email': 'test@foodstack.mx',
        'password': 'password123'
    }

    defaults.update(params)

    return get_user_model().objects.create_user(**defaults)


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


def proveedor_dummy(**params):
    """ Crea un Proveedor dummy para los tests """

    defaults = {
        'nombre': 'Vinos Hyrule',
        'razon_social': 'Vinos Hyrule SA de CV',
        'rfc': 'VHYR190101XYZ',
        'direccion': 'Lake Hylia 666',
        'ciudad': 'Hyrule'
    }

    defaults.update(params)

    return models.Proveedor.objects.create(**defaults)

    
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


def producto_dummy(**params):
    """ Crear un Producto dummy para los tests """

    defaults = {
        'folio': 'Nn0000000001',
        'ingrediente': ingrediente_dummy(),
        'url': 'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0763516458',
        'capacidad': 750
    }

    defaults.update(params)

    return models.Producto.objects.create(**defaults)


def botella_dummy(**params):
    """ Crear una Botella dummy para los tests """

    defaults = {
        'folio': 'Nn0000000002',
        'producto': producto_dummy(),
        'url': 'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0763516458',
        'capacidad': 750,
        'usuario_alta': usuario_dummy(),
        'sucursal': sucursal_dummy(),
        'almacen': almacen_dummy(),
        'proveedor': proveedor_dummy(),
        'estado': '2'
    }

    defaults.update(params)

    return models.Botella.objects.create(**defaults)


def inspeccion_dummy(**params):
    """ Crear una Inspeccion dummy para los tests """

    defaults = {
        'almacen': almacen_dummy(),
        'sucursal': sucursal_dummy(),
        'usuario_alta': usuario_dummy(),
        'usuario_cierre': usuario_dummy(email='test2@foodstack.mx', password='password123')
    }

    defaults.update(params)

    return models.Inspeccion.objects.create(**defaults)
        


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
        #print('::: STR CLIENTE :::')
        #print(cliente)

        self.assertEqual(cliente.nombre, nombre)
        self.assertEqual(cliente.rfc, rfc)


    def test_crear_proveedor(self):
        """ Testear que se crea un Proveedor con éxito """

        nombre = 'Vinos Hyrule'
        razon_social = 'Vinos Hyrule SA de CV'
        rfc = 'VHYR190101XYZ'
        direccion = 'Lake Hylia 666'
        ciudad = 'Hyrule'

        proveedor = models.Proveedor.objects.create(
            nombre=nombre,
            razon_social=razon_social,
            rfc=rfc,
            direccion=direccion,
            ciudad=ciudad
        )

        #print('::: STR PROVEEDOR :::')
        #print(proveedor)

        self.assertEqual(proveedor.nombre, nombre)


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

        #print('::: STR SUCURSAL :::')
        #print(sucursal)

        self.assertEqual(str(sucursal), nombre)
        self.assertEqual(sucursal.slug, 'TACOS-LINK-PROVIDENCIA')


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
        #print(email.lower())

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

        #print('::: STR INGREDIENTE :::')
        #print(ingrediente)

        ingredientes_categoria = categoria.ingredientes.all()

        self.assertEqual(ingrediente.codigo, codigo)
        self.assertEqual(ingredientes_categoria.count(), 1)


    def  test_crear_receta(self):
        """ Testear que se construya una Receta con éxito """

        codigo_pos = 'CPWHIS001'
        nombre = 'JACK DANIELS DERECHO'
        sucursal = sucursal_dummy()

        receta = models.Receta.objects.create(
            codigo_pos=codigo_pos,
            nombre=nombre,
            sucursal=sucursal
        )

        #print('::: STR RECETA :::')
        #print(receta)

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

        #print('::: STR INGREDIENTE-RECETA :::')
        #print(ingrediente_receta)

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

        #print('::: STR ALMACEN :::')
        #print(almacen)

        almacenes_sucursal = sucursal.almacenes.all()

        self.assertEqual(almacen.nombre, nombre)
        self.assertEqual(almacenes_sucursal.count(), 1)
        self.assertEqual(almacen.tipo, '1')

    
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

        #print('::: STR CAJA :::')
        #print(caja)

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

        #print('::: STR VENTA :::')
        #print(venta)

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

        #print('::: STR CONSUMO-RECETA-VENDIDA :::')
        #print(consumo_receta_vendida)

        consumos_ingrediente = ingrediente.consumos_ingrediente.all()
        consumos_receta = receta.consumos_receta.all()
        consumos_venta = venta.consumos_venta.all()

        self.assertEqual(consumos_ingrediente.count(), 1)
        self.assertEqual(consumos_receta.count(), 1)
        self.assertEqual(consumos_venta.count(), 1)


    def test_crear_producto(self):
        """ Testear que se crea un Producto """

        folio = 'Nn0000000001'
        ingrediente = ingrediente_dummy()
        url = 'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0763516458'
        capacidad = 750
        
        producto = models.Producto.objects.create(
            folio=folio,
            ingrediente=ingrediente,
            url=url,
            capacidad=capacidad
        )

        #print('::: STR PRODUCTO :::')
        #print(producto)

        productos_ingrediente = ingrediente.productos.all()

        self.assertEqual(producto.folio, folio)
        self.assertEqual(productos_ingrediente.count(), 1)

    
    def test_crear_botella(self):
        """ Testear que se crea una Botella """

        folio = 'Nn0000000002'
        producto = producto_dummy()
        url = 'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0763516458'
        capacidad = 750
        usuario_alta = usuario_dummy()
        sucursal = sucursal_dummy()
        almacen = almacen_dummy()
        proveedor = proveedor_dummy()
        estado = '2'

        botella = models.Botella.objects.create(
            folio=folio,
            producto=producto,
            url=url,
            capacidad=capacidad,
            usuario_alta=usuario_alta,
            sucursal=sucursal,
            almacen=almacen,
            proveedor=proveedor
        )

        #print('::: STR BOTELLA :::')
        #print(botella)

        botellas = producto.botellas.all()
        botellas_sucursal = sucursal.botellas_sucursal.all()
        botellas_almacen = almacen.botellas_almacen.all()
        botellas_proveedor = proveedor.botellas_proveedor.all()

        usuario_botella = botella.usuario_alta
        email_usuario = usuario_botella.email

        self.assertEqual(botella.folio, folio)
        self.assertEqual(botella.estado, estado)
        self.assertEqual(botellas.count(), 1)
        self.assertEqual(botellas_sucursal.count(), 1)
        self.assertEqual(botellas_almacen.count(), 1)
        self.assertEqual(botellas_proveedor.count(), 1)
        self.assertEqual(email_usuario, usuario_alta.email) 


    def test_crear_traspaso(self):
        """ Testear que se crea un Traspaso """

        botella = botella_dummy()
        sucursal = sucursal_dummy()
        almacen = almacen_dummy()
        usuario = usuario_dummy(email='test2@foodstack.mx', password='password123')

        traspaso = models.Traspaso.objects.create(
            botella=botella,
            sucursal=sucursal,
            almacen=almacen,
            usuario=usuario
        )

        #print('::: STR TRASPASO :::')
        #print(traspaso)

        traspasos_botellas = botella.traspasos_botella.all()
        traspasos_sucursal = sucursal.traspasos_sucursal.all()
        traspasos_almacen = almacen.traspasos_almacen.all()
        usuario_traspaso = traspaso.usuario
        email_usuario = usuario_traspaso.email

        self.assertEqual(traspasos_botellas.count(), 1)
        self.assertEqual(traspasos_sucursal.count(), 1)
        self.assertEqual(traspasos_almacen.count(), 1)
        self.assertEqual(email_usuario, usuario.email)


    def test_crear_inspeccion(self):
        """ Testear que se crea una Inspeccion """

        almacen = almacen_dummy()
        sucursal = sucursal_dummy()
        usuario_alta = usuario_dummy()
        usuario_cierre = usuario_alta
        
        inspeccion = models.Inspeccion.objects.create(
            almacen=almacen,
            sucursal=sucursal,
            usuario_alta=usuario_alta,
            usuario_cierre=usuario_cierre
        )
        #print('::: STR INSPECCION :::')
        #print(inspeccion)

        inspecciones_almacen = almacen.inspecciones_almacen.all()
        inspecciones_sucursal = sucursal.inspecciones_sucursal.all()
        inspecciones_usuario_alta = usuario_alta.inspecciones_usuario_alta.all()
        inspecciones_usuario_cierre = usuario_cierre.inspecciones_usuario_cierre.all()

        self.assertEqual(inspecciones_almacen.count(), 1)
        self.assertEqual(inspecciones_sucursal.count(), 1)
        self.assertEqual(inspecciones_usuario_alta.count(), 1)
        self.assertEqual(inspecciones_usuario_cierre.count(), 1)
        self.assertEqual(inspeccion.estado, '0')


    def test_crear_item_inspeccion(self):
        """ Testear que se crea un ItemInspeccion con éxito """

        inspeccion = inspeccion_dummy()
        botella = models.Botella.objects.create(
            folio = 'Nn0000000002',
            producto = producto_dummy(),
            url = 'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0763516458',
            capacidad = 750,
            usuario_alta = usuario_dummy(email='compras@foodstack.mx', password='password123'),
            sucursal = inspeccion.sucursal,
            almacen = inspeccion.almacen,
            proveedor = proveedor_dummy(),
            estado = '2'
        )
        peso_botella = 1212

        item_inspeccion = models.ItemInspeccion.objects.create(
            inspeccion=inspeccion,
            botella=botella,
            peso_botella=peso_botella
        )

        #print('::: STR ITEM-INSPECCION :::')
        #print(item_inspeccion)

        items_inspeccionados = inspeccion.items_inspeccionados.all()
        inspecciones_botella = botella.inspecciones_botella.all()

        self.assertEqual(items_inspeccionados.count(), 1)
        self.assertEqual(inspecciones_botella.count(), 1)
        self.assertEqual(item_inspeccion.peso_botella, peso_botella)

    
    
    def test_crear_producto_sin_registro(self):
        """ Testear que se crea un ProductoSinRegistro con éxito """

        #mock_date.today.return_value = datetime.date(2019, 1, 1)
        

        sucursal = 'TACOS-LINK-PROVIDENCIA'
        codigo_pos = '00050'
        caja = 1
        nombre = 'CARAJILLO'

        with freeze_time("2019-06-01"):
            producto_sin_registro = models.ProductoSinRegistro.objects.create(
                sucursal=sucursal,
                codigo_pos=codigo_pos,
                caja=caja,
                nombre=nombre
            )

        #print('::: STR PRODUCTO NO REGISTRADO :::')
        #print(producto_sin_registro)

        self.assertEqual(producto_sin_registro.sucursal, 'TACOS-LINK-PROVIDENCIA')
        self.assertEqual(producto_sin_registro.fecha, datetime.date(2019, 6, 1))

