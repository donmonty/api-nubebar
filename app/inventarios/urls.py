from django.urls import path, include
from rest_framework.routers import DefaultRouter

from inventarios import views


router = DefaultRouter()
router.register('inspecciones', views.InspeccionViewSet, 'inspecciones')
router.register('producto', views.ProductoViewSet, 'producto')
router.register('inspeccion-total', views.InspeccionTotalViewSet, 'inspeccion-total')
#router.register('detalle-inspeccion', views.DetalleInspeccionView, 'detalle-inspeccion')
#router.register(r'get-inspeccion/(?P<inspeccion_id>[0-9]+)', views.DetalleInspeccionView, 'get-inspeccion')
#router.register('get-inspeccion/', views.DetalleInspeccionView, 'get-inspeccion')
#router.register(r'get-inspeccion/inspeccion/(?P<inspeccion_id>[0-9]+)', views.DetalleInspeccionView, 'get-inspeccion')

#router.register(r'get-inspecciones/sucursal/(?P<sucursal_id>[0-9]+)/almacen/(?P<almacen_id>[0-9]+)', views.ListaInspeccionesView, 'get-inspecciones')
router.register(r'get-inspecciones/almacen/(?P<almacen_id>[0-9]+)', views.ListaInspeccionesView, 'get-inspecciones')
#router.register(r'get-botellas-no-contadas/inspeccion/(?P<inspeccion_id>[0-9]+)/ingrediente/(?P<ingrediente_id>[0-9]+)', views.ListaBotellasNoContadasView, 'get-botellas-no-contadas')
#router.register(r'get-botella-inspecciones/folio/(?P<folio_id>[a-zA-Z0-9]+)', views.InspeccionesBotellaViewSet, 'get-botella-inspecciones')

app_name = 'inventarios'

urlpatterns = [
    path('', include(router.urls)),
    path('get-inspeccion/inspeccion/<int:inspeccion_id>', views.get_inspeccion, name='get-inspeccion'),
    path('get-lista-inspecciones/almacen/<int:almacen_id>/tipo/<str:tipo_id>', views.get_lista_inspecciones, name='get-lista-inspecciones'),
    path('get-resumen-inspeccion/inspeccion/<int:inspeccion_id>', views.resumen_inspeccion, name='resumen-inspeccion'),
    path('get-resumen-inspeccion-no-contado/inspeccion/<int:inspeccion_id>', views.resumen_inspeccion_no_contado, name='resumen-inspeccion-no-contado'),
    path('get-resumen-inspeccion-contado/inspeccion/<int:inspeccion_id>', views.resumen_inspeccion_contado, name='resumen-inspeccion-contado'),
    path('get-resumen-botellas-conteo/inspeccion/<int:inspeccion_id>', views.resumen_botellas_conteo, name='resumen-botellas-conteo'),
    path('get-botellas-no-contadas/inspeccion/<int:inspeccion_id>/ingrediente/<int:ingrediente_id>', views.lista_botellas_no_contadas, name='botellas-no-contadas'),
    path('get-botellas-contadas/inspeccion/<int:inspeccion_id>/ingrediente/<int:ingrediente_id>', views.lista_botellas_contadas, name='botellas-contadas'),
    path('get-inspecciones-botella/folio/<str:folio_id>', views.lista_inspecciones_botella, name='get-inspecciones-botella'),
    path('get-detalle-botella-inspeccion/inspeccion/<int:inspeccion_id>/folio/<str:folio_id>', views.detalle_botella_inspeccion, name='get-detalle-botella-inspeccion'),
    path('get-lista-sucursales', views.lista_sucursales, name='get-lista-sucursales'),
    path('get-lista-sucursales-almacenes', views.lista_sucursales_almacenes, name='get-lista-sucursales-almacenes'),
    path('update-peso-botella/', views.update_peso_botella, name='update-peso-botella'),
    path('cerrar-inspeccion/', views.cerrar_inspeccion, name='cerrar-inspeccion'),
    path('update-botella-nueva-vacia/', views.update_botella_nueva_vacia, name='update-botella-nueva-vacia'),
    path('get-marbete-sat/folio/<str:folio_id>', views.get_marbete_sat, name='get-marbete-sat'),
    path('get-categorias', views.get_categorias, name='get-categorias'),
    path('get-ingredientes-categoria/categoria/<int:categoria_id>', views.get_ingredientes_categoria, name='get-ingredientes-categoria'),
    path('crear-botella/', views.crear_botella, name='crear-botella'),
    path('get-marbete-sat-producto/folio/<str:folio_id>', views.get_marbete_sat_producto, name='get-marbete-sat-producto'),
    path('crear-traspaso/', views.crear_traspaso, name='crear-traspaso'),
    path('consultar-botella/folio/<str:folio_id>', views.consultar_botella, name='consultar-botella'),
    path('crear-ingrediente/', views.crear_ingrediente, name='crear-ingrediente'),
    path('get-proveedores', views.get_proveedores, name='get-proveedores'),
    path('get-servicios-usuario', views.get_servicios_usuario, name='get-servicios-usuario'),
    #path('get-inspeccion/<int:inspeccion_id>', views.DetalleInspeccionView.as_view(), name='detalle-inspeccion'),
    #path('get-inspecciones/sucursal/<int:sucursal_id>/almacen/<int:almacen_id>', views.ListaInspeccionesView.as_view(), name='lista-inspecciones')
    #path('inspecciones/sucursal/<int:sucursal_id>/almacen/<int:almacen_id>', views.InspeccionDisplayViewSet, 'get-inspecciones')
    #path('nueva-inspeccion/', views.crear_inspeccion, name='crear_inspeccion')
]