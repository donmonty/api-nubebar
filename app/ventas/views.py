from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views import View

from importlib import import_module
from core.models import Sucursal
from ventas import forms
from ventas import parser_ventas
from ventas import parsers
from ventas import ventas_consumos


def upload(request):

    if request.method == 'GET':
        return render(request, 'ventas/upload.html')



"""
-----------------------------------------------------------------------------------
VIEW QUE PERMITE AL USUARIO SUBIR EL REPORTE DE VENTAS DE UNA SUCURSAL
-----------------------------------------------------------------------------------
"""
@login_required
def upload_reporte_ventas(request, nombre_sucursal):

    if request.method == 'GET':

        sucursal = get_object_or_404(Sucursal, slug=nombre_sucursal)

        return render(request, 'ventas/upload_ventas.html', {'sucursal': sucursal})


    if request.method == 'POST':

        sucursal = Sucursal.objects.get(slug=nombre_sucursal)

        # Creamos nuestra forma con los datos del POST request
        form = forms.VentasForm(request.POST, request.FILES)

        # Guardamos el reporte de ventas en una variable
        ventas_csv = request.FILES['ventas_csv']
        
        """
        ------------------------------------------------------
        PARSEAMOS EL REPORTE DE VENTAS
        ------------------------------------------------------
        """
        # Construimos el nombre del parser a importar y lo importamos dinámicamente
        nombre_parser = 'parser_' + (sucursal.slug).replace('-', '_').lower()
        parser_ventas = import_module('ventas.parsers.' + nombre_parser)

        # Alimentamos el reporte de ventas al parser y lo corremos
        #resultado_parser = parser_ventas.parser(ventas_csv, sucursal)
        resultado_parser = parser_ventas.parser(ventas_csv)

        # Si hay un error con el reporte de ventas, notificar al usuario
        if resultado_parser['procesado'] == False:
            mensaje_error = 'Hubo un error al procesar el reporte de ventas.'
            return render(request, 'ventas/upload_ventas.html', {'mensaje_error': mensaje_error})
        
        # """
        # --------------------------------------------------------------
        # REGISTRAMOS LA INFORMACIÓN DE VENTAS Y CONSUMO DE INGREDIENTES
        # EN LA BASE DE DATOS
        # --------------------------------------------------------------
        # """
        # Si el parser procesa el reporte de ventas y no hay errores, guardamos el resultado 
        # en una variable
        #df_ventas = resultado_parser['dataframe']

        # Tomamos el resultado del parser y lo procesamos para extraer la información de
        # ventas y consumo de ingredientes y luego guardarla en la base de datos
        #ventas_consumos(df_ventas, sucursal.id)

        # Mostramos la página de éxito al usuario
        return render (request, 'ventas/success.html', {'resultado_parser': resultado_parser})


"""
--------------------------------------
CLASS-BASED VIEW DE UPLOAD_VENTAS
--------------------------------------
"""

class UploadVentas(View):

    form_class = forms.VentasForm
    #initial = {'key': value}
    template_name = 'ventas/upload_ventas.html'


    def get(self, request, nombre_sucursal):
        #form = self.form_class(initial=self.initial)
        form = self.form_class()
        sucursal = get_object_or_404(Sucursal, slug=nombre_sucursal)
        return render(request, self.template_name, {'sucursal': sucursal})


    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        
        if form.is_valid():
            sucursal = models.Sucursal.objects.get(slug=nombre_sucursal)
            ventas_csv = request.FILES['ventas_csv']

            # Alimentamos el reporte de ventas al parser y lo corremos
            resultado_parser = parser_ventas(ventas_csv, sucursal.id)

            # Si hay un error con el reporte de ventas, notificar al usuario
            if resultado_parser['procesado'] == False:
                mensaje_error = 'Hubo un error al procesar el reporte de ventas.'
                return render(request, self.template_name, {'mensaje_error': mensaje_error})

            return HttpResponseRedirect(reverse('upload'))

            




            



