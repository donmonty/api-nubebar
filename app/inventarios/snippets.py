from django.db.models import F, Q, QuerySet, Avg, Count, Sum
from core import models
from django.contrib.auth import get_user_model
import datetime


# API Client
#client = APIClient()

#Fechas
hoy = datetime.date.today()
ayer = hoy - datetime.timedelta(days=1)

# Proveedores
vinos_america = models.Proveedor.objects.create(nombre='Vinos America')
super_la_playa = models.Proveedor.objects.create(nombre='Super La Playa')
la_europea = models.Proveedor.objects.create(nombre='La Europea')

# Cliente
operadora_magno = models.Cliente.objects.create(nombre='MAGNO BRASSERIE')

# Sucursales
magno_brasserie = models.Sucursal.objects.create(nombre='MAGNO-BRASSERIE', cliente=operadora_magno)
atomic_thai = models.Sucursal.objects.create(nombre='ATOMIC-THAI', cliente=operadora_magno)

# Almacenes
barra_1 = models.Almacen.objects.create(nombre='BARRA 1', numero=1, sucursal=magno_brasserie)
barra_1_atomic = models.Almacen.objects.create(nombre='BARRA 1 ATOMIC', numero=1, sucursal=atomic_thai)

# Caja
caja_1 = models.Caja.objects.create(numero=1, nombre='CAJA 1', almacen=barra_1)

# Usuarios
usuario = get_user_model().objects.create(email='test@foodstack.mx', password='password123')
usuario.sucursales.add(magno_brasserie)

usuario_2 = get_user_model().objects.create(email='barman@foodstack.mx', password='password123')
usuario_2.sucursales.add(magno_brasserie)

usuario_3 = get_user_model().objects.create(email='usuario3@foodstack.mx', password='password456')
usuario_3.sucursales.add(atomic_thai)

# Autenticación
#client.force_authenticate(usuario)

#Categorías
categoria_licor = models.Categoria.objects.create(nombre='LICOR')
categoria_tequila = models.Categoria.objects.create(nombre='TEQUILA')
categoria_whisky = models.Categoria.objects.create(nombre='WHISKY')

# Ingredientes
licor_43 = models.Ingrediente.objects.create(
    codigo='LICO001',
    nombre='LICOR 43',
    categoria=categoria_licor,
    factor_peso=1.05
)
herradura_blanco = models.Ingrediente.objects.create(
    codigo='TEQU001',
    nombre='HERRADURA BLANCO',
    categoria=categoria_tequila,
    factor_peso=0.95
)
jw_black = models.Ingrediente.objects.create(
    codigo='WHIS001',
    nombre='JOHNNIE WALKER BLACK',
    categoria=categoria_whisky,
    factor_peso=0.95
)

# Recetas
trago_licor_43 = models.Receta.objects.create(
    codigo_pos='00081',
    nombre='LICOR 43 DERECHO',
    sucursal=magno_brasserie
)
trago_herradura_blanco = models.Receta.objects.create(
    codigo_pos='00126',
    nombre='HERRADURA BLANCO DERECHO',
    sucursal=magno_brasserie
)
trago_jw_black = models.Receta.objects.create(
    codigo_pos= '00167',
    nombre='JW BLACK DERECHO',
    sucursal=magno_brasserie
)
carajillo = models.Receta.objects.create(
    codigo_pos='00050',
    nombre='CARAJILLO',
    sucursal=magno_brasserie
)

# Ingredientes-Recetas
ir_licor_43 = models.IngredienteReceta.objects.create(receta=trago_licor_43, ingrediente=licor_43, volumen=60)
ir_herradura_blanco = models.IngredienteReceta.objects.create(receta=trago_herradura_blanco, ingrediente=herradura_blanco, volumen=60)
ir_jw_black = models.IngredienteReceta.objects.create(receta=trago_jw_black, ingrediente=jw_black, volumen=60)
ir_carajillo = models.IngredienteReceta.objects.create(receta=carajillo, ingrediente=licor_43, volumen=45)


# Ventas
venta_licor43 = models.Venta.objects.create(
    receta=trago_licor_43,
    sucursal=magno_brasserie,
    fecha=ayer,
    unidades=1,
    importe=120,
    caja=caja_1
)

venta_herradura_blanco = models.Venta.objects.create(
    receta=trago_herradura_blanco,
    sucursal=magno_brasserie,
    fecha=ayer,
    unidades=1,
    importe=90,
    caja=caja_1
)

# Consumos Recetas Vendidas
cr_licor43 = models.ConsumoRecetaVendida.objects.create(
    ingrediente=licor_43,
    receta=trago_licor_43,
    venta=venta_licor43,
    fecha=ayer,
    volumen=60
) 

cr_herradura_blanco = models.ConsumoRecetaVendida.objects.create(
    ingrediente=herradura_blanco,
    receta=trago_herradura_blanco,
    venta=venta_herradura_blanco,
    fecha=ayer,
    volumen=60
)

# Productos
producto_licor43 = models.Producto.objects.create(
    folio='Ii0000000001',
    ingrediente=licor_43
)

producto_herradura_blanco = models.Producto.objects.create(
    folio='Nn0000000001',
    ingrediente=herradura_blanco
)

# Botellas
botella_licor43 = models.Botella.objects.create(
    folio='Ii0000000001',
    producto=producto_licor43,
    url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Ii0765216599',
    capacidad=750,
    usuario_alta=usuario,
    sucursal=magno_brasserie,
    almacen=barra_1,
    proveedor=vinos_america
)

botella_herradura_blanco = models.Botella.objects.create(
    folio='Nn0000000001',
    producto=producto_herradura_blanco,
    url='https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=4&D2=1&D3=Nn1727494182',
    capacidad=700,
    usuario_alta=usuario,
    sucursal=magno_brasserie,
    almacen=barra_1,
    proveedor=vinos_america
)


# Inspección 1
inspeccion_1 = models.Inspeccion.objects.create(
    almacen=barra_1,
    sucursal=magno_brasserie,
    usuario_alta=usuario,
    usuario_cierre=usuario,
    estado='1' # CERRADA
)