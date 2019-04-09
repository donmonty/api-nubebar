from django.urls import path
#from django.conf.urls import url
from ventas import views

app_name = 'ventas'


urlpatterns = [
    path('upload/', views.upload, name='upload'),
    path('upload/<slug:nombre_sucursal>/', views.upload_reporte_ventas, name='upload_ventas'),
    path('upload-class/<slug:nombre_sucursal>/', views.UploadVentas.as_view(), name='upload_file')
]