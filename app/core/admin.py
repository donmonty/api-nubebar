from django.contrib import admin

from core import models


admin.site.register(models.Cliente)
admin.site.register(models.Sucursal)
admin.site.register(models.Proveedor)
admin.site.register(models.User)
admin.site.register(models.Categoria)
admin.site.register(models.Ingrediente)
admin.site.register(models.Receta)
admin.site.register(models.IngredienteReceta)
admin.site.register(models.Almacen)
admin.site.register(models.Caja)
admin.site.register(models.Venta)
admin.site.register(models.ConsumoRecetaVendida)
admin.site.register(models.Producto)
admin.site.register(models.Botella)