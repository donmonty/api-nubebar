from django.urls import path, include
from rest_framework.routers import DefaultRouter

from analytics import views


app_name = 'analytics'

urlpatterns = [
    path('crear-reporte-mermas/', views.crear_reporte_mermas, name='crear-reporte-mermas'),
    path('get-reporte-mermas/reporte/<int:reporte_id>/', views.get_reporte_mermas, name='get-reporte-mermas'),
    path('get-detalle-ventas-merma/merma/<int:merma_id>/', views.get_detalle_ventas_merma, name='get-detalle-ventas-merma'),
    path('get-lista-reportes-mermas/almacen/<int:almacen_id>', views.get_lista_reportes_mermas, name='get-lista-reportes-mermas'),
    path('get-reporte-costo-stock/almacen/<int:almacen_id>', views.get_reporte_costo_stock, name='get-reporte-costo-stock'),
    path('get-reporte-stock/sucursal/<int:sucursal_id>', views.get_reporte_stock, name='get-reporte-stock'),
    path('get-detalle-stock/producto/<int:producto_id>/sucursal/<int:sucursal_id>', views.get_detalle_stock, name='get-detalle-stock'),
    path('get-reporte-productos-sin-registro/sucursal/<int:sucursal_id>', views.get_reporte_productos_sin_registro, name='get-reporte-productos-sin-registro'),
    path('get-detalle-sin-registro/codigo/<str:codigo_pos>/sucursal/<int:sucursal_id>', views.get_detalle_sin_registro, name='get-detalle-sin-registro'),
    path('get-reporte-restock/sucursal/<int:sucursal_id>', views.get_reporte_restock, name='get-reporte-restock'),
    path('get-detalle-botellas-merma/merma/<int:merma_id>/', views.get_botellas_merma, name='get-detalle-botellas-merma'),
    path('get-reporte-restock-02/sucursal/<int:sucursal_id>', views.get_reporte_restock_02, name='get-reporte-restock-02'),
]