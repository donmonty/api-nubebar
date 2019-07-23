from django.urls import path, include
from rest_framework.routers import DefaultRouter

from analytics import views


app_name = 'analytics'

urlpatterns = [
    path('crear-reporte-mermas/', views.crear_reporte_mermas, name='crear-reporte-mermas'),
    path('get-reporte-mermas/reporte/<int:reporte_id>/', views.get_reporte_mermas, name='get-reporte-mermas'),
    path('get-detalle-ventas-merma/merma/<int:merma_id>/', views.get_detalle_ventas_merma, name='get-detalle-ventas-merma'),
    path('get-lista-reportes-mermas/almacen/<int:almacen_id>', views.get_lista_reportes_mermas, name='get-lista-reportes-mermas'),
    path('get-reporte-costo-stock/almacen/<int:almacen_id>', views.get_reporte_costo_stock, name='get-reporte-costo-stock')
]