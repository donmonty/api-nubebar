from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext as _

from core import models


class UserAdmin(BaseUserAdmin):
    
    ordering = ['id']
    list_display = ['email', 'name']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Datos Personales'), {'fields': ('name',)}),
        (
            _('Permisos'),
            {'fields': ('is_active', 'is_staff', 'is_superuser')}
        ),
        (('Sucursales'), {'fields': ('sucursales',)}),
        (_('Ultimo Acceso'), {'fields': ('last_login',)})
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')
        }),
    )

# Agregamos inlines para las Recetas
class IngredienteRecetaInline(admin.TabularInline):
    model = models.IngredienteReceta
    extra = 1

class IngredienteAdmin(admin.ModelAdmin):
    inlines = (IngredienteRecetaInline,)
    search_fields = ['nombre', 'codigo']

class RecetaAdmin(admin.ModelAdmin):
    inlines = (IngredienteRecetaInline,)
    search_fields = ['nombre', 'codigo_pos']



admin.site.register(models.Cliente)
admin.site.register(models.Sucursal)
admin.site.register(models.Proveedor)
admin.site.register(models.User, UserAdmin)
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
admin.site.register(models.ProductoSinRegistro)