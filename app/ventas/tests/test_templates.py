from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch

from core import models
from ventas import views
from ventas import parsers
from ventas import forms
from ventas.views import UploadVentas


def usuario_dummy(**params):
    """ Crea un User dummy para los tests """

    defaults = {
        'email': 'test@foodstack.mx',
        'password': 'password123'
    }

    defaults.update(params)

    return get_user_model().objects.create_user(**defaults)


def super_usuario_dummy(**params):
    """ Crea un super user para los tests """

    defaults = {
        'email': 'admin@foodstack.mx',
        'password': 'password123'
    }

    defaults.update(params)

    return get_user_model().objects.create_superuser(**defaults)


def cliente_dummy(**params):
        """ Crea un Cliente dummy para usar en los tests """

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
    """ Crea una Sucursal dummy para usar en nuestros tests """

    defaults = {
        'nombre': 'Magno Brasserie',
        'cliente': cliente_dummy(),
        'razon_social': 'Magno Brasserie SA de CV',
        'rfc': 'LPRO190101XYZ',
        'direccion': 'Efraín González Luna 666',
        'ciudad': 'Guadalajara',
        'latitud': 20.676,
        'longitud': -103.383,
        'codigo_postal': '45110'

    }

    defaults.update(params)

    return models.Sucursal.objects.create(**defaults)


"""
------------------------------------------------------------
TESTS PARA LOS TEMPLATES DE VENTAS
------------------------------------------------------------
"""

class TemplateTests(TestCase):

    def setUp(self):
        self.client = Client()

        # Creamos un super usuario dummy y lo logeamos
        usuario = super_usuario_dummy()
        self.client.force_login(user=usuario)


    def test_render_pagina_upload_ventas(self):

        url = reverse('ventas:upload')
        #url = '/ventas/upload/'
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    
    def test_render_pagina_upload_ventas_sucursal(self):

        sucursal = sucursal_dummy()
        url = reverse('ventas:upload_ventas', kwargs={'nombre_sucursal': sucursal.slug})
        #url = '/ventas/upload/TACOS-LINK/'
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)


    def test_render_pagina_upload_file(self):

        sucursal = sucursal_dummy()
        url = reverse('ventas:upload_file', kwargs={'nombre_sucursal': sucursal.slug})
        #url = '/ventas/upload-class/TACOS-LINK'
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)


    #@patch('ventas.views.parser_ventas.parser') # Mockeamos el modulo 'parser_ventas' y su método 'parser' 
    @patch('ventas.parsers.parser_magno_brasserie.parser')
    def test_post_reporte_ventas(self, mock_parser):
        """ Testear que se sube el reporte de ventas correctamente """

        # Definimos la respuesta predeterminada del mock_parser
        mock_parser.return_value = {'df_ventas': 'df_ventas', 'procesado': True}
        
        # Creamos una sucursal y el URL pra el request
        sucursal = sucursal_dummy()
        url = reverse('ventas:upload_ventas', kwargs={'nombre_sucursal': sucursal.slug})

        # Hacemos un mock del archivo de ventas a subir
        archivo_ventas = SimpleUploadedFile('ventas.csv', b'Este es un archivo CSV')

        # Metemos el archivo de ventas mockeado en un diccionario
        form_data = {'reporte_ventas': archivo_ventas}
        form_data_2 = {'ventas_csv': archivo_ventas}
        data = {}
        # Creamos un formulario y le asignamos el archivo de ventas mockeado
        formulario = forms.VentasForm(data, form_data)  # Es necesario definir el parámetro 'data' aunque esté vacío

        # Validamos el formulario
        formulario.is_valid()
        print(formulario.errors.as_data()) # Imprimimos cualquier error en la validación

        # Tomamos el archivo de ventas mockeado de el formulario validado y lo imprimimos
        archivo_subido = formulario.cleaned_data['reporte_ventas']
        print(type(archivo_subido))

        # Hacemos un POST request con los datos del formulario
        res = self.client.post(url, form_data_2, follow=True)
        # Checamos que la pagina se rendereó correctamente
        self.assertEqual(res.status_code, 200)
        # Checamos que el valor regresado de mock_parser sea el esperado
        self.assertEqual(res.context['resultado_parser'], {'df_ventas': 'df_ventas', 'procesado': True})

        #mock_parser.assert_called_with(archivo_subido, sucursal)
        






    



